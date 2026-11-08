import importlib.util
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


copy = load("verify_copy")
bundle = load("audit_bundle")
host = load("inspect_host")


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def trees(self):
        source, dest = self.root / "disc", self.root / "copy"
        source.mkdir()
        dest.mkdir()
        return source, dest

    def test_same_size_corruption_requires_hashes(self):
        source, dest = self.trees()
        (source / "data.cab").write_bytes(b"GOOD")
        (dest / "data.cab").write_bytes(b"FAIL")
        self.assertEqual(copy.compare(source, dest)["status"], "metadata_match_only")
        report = copy.compare(source, dest, True)
        self.assertEqual(report["different"], ["data.cab"])

    def test_missing_extra_and_link_not_followed(self):
        source, dest = self.trees()
        (source / "empty").mkdir()
        (dest / "extra").write_text("extra")
        for tree in (source, dest):
            (tree / "loop").symlink_to("loop")
        report = copy.compare(source, dest, True)
        self.assertEqual(report["missing"], ["empty"])
        self.assertEqual(report["extra"], ["extra"])
        self.assertEqual(report["errors"], [])

    def test_unicode_content_match(self):
        source, dest = self.trees()
        for tree in (source, dest):
            (tree / "中文 data.bin").write_bytes(b"\x00\x01test")
        result = subprocess.run([sys.executable, str(ROOT / "scripts/verify_copy.py"),
                                 str(source), str(dest), "--content"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "content_match")

    def test_nested_copy_rejected(self):
        source, dest = self.trees()
        nested = source / "nested"
        nested.mkdir()
        result = subprocess.run([sys.executable, str(ROOT / "scripts/verify_copy.py"),
                                 str(source), str(nested)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)

    def app(self):
        app = self.root / "Example.app"
        macos = app / "Contents/MacOS"
        macos.mkdir(parents=True)
        (app / "Contents/Info.plist").write_bytes(plistlib.dumps({"CFBundleExecutable": "launch"}))
        launcher = macos / "launch"
        launcher.write_text('#!/bin/sh\nexec "$(dirname "$0")/../Resources/runtime"\n')
        launcher.chmod(0o755)
        return app

    def test_bundle_reports_live_dependencies_without_source(self):
        app = self.app()
        launcher = app / "Contents/MacOS/launch"
        launcher.write_text('#!/bin/sh\nexport PREFIX="$HOME/Documents/work/runtime-final"\n# private-token\n')
        (app / "outside").symlink_to(self.root)
        (app / "broken").symlink_to("missing")
        report = bundle.audit(app)
        kinds = {issue["kind"] for issue in report["findings"]}
        self.assertTrue({"user_external_state", "external_link", "broken_or_cyclic_link"} <= kinds)
        self.assertNotIn("private-token", json.dumps(report))
        self.assertTrue(launcher.exists())

    def test_absolute_internal_link_and_scan_limit(self):
        app = self.app()
        (app / "absolute").symlink_to(app / "Contents")
        kinds = {issue["kind"] for issue in bundle.audit(app)["findings"]}
        self.assertIn("absolute_internal_link", kinds)
        self.assertEqual(bundle.audit(app, max_files=1)["status"], "incomplete")

    def test_clean_bundle_not_certified_portable(self):
        report = bundle.audit(self.app())
        self.assertEqual(report["status"], "no_static_findings")
        self.assertIn("Not a portability verdict", report["limitations"][0])

    def test_malformed_plist_root_reported(self):
        app = self.app()
        (app / "Contents/Info.plist").write_bytes(plistlib.dumps(["not", "a", "dictionary"]))
        report = bundle.audit(app)
        self.assertIn("invalid_plist", {issue["kind"] for issue in report["findings"]})

    def test_external_plist_or_contents_link_is_not_parsed(self):
        app = self.app()
        plist = app / "Contents/Info.plist"
        outside = self.root / "outside.plist"
        plist.rename(outside)
        plist.symlink_to(outside)
        with mock.patch.object(bundle.plistlib, "loads") as parse:
            self.assertEqual(bundle.audit(app)["status"], "incomplete")
            plist.unlink()
            outside.rename(plist)
            contents = app / "Contents"
            contents.rename(self.root / "outside")
            contents.symlink_to(self.root / "outside", target_is_directory=True)
            self.assertEqual(bundle.audit(app)["status"], "incomplete")
            parse.assert_not_called()

    def test_internal_relative_plist_link(self):
        app = self.app()
        plist = app / "Contents/Info.plist"
        plist.rename(plist.with_name("Metadata.plist"))
        plist.symlink_to("Metadata.plist")
        self.assertEqual(bundle.audit(app)["status"], "no_static_findings")

    def test_unsafe_plists_exit_incomplete_without_hanging(self):
        app = self.app()
        plist = app / "Contents/Info.plist"
        for kind in ("oversize", "fifo", "malformed"):
            with self.subTest(kind=kind):
                plist.unlink()
                if kind == "oversize":
                    with plist.open("wb") as stream:
                        stream.truncate(bundle.MAX_PLIST_BYTES + 1)
                elif kind == "fifo":
                    os.mkfifo(plist)
                else:
                    plist.write_bytes(b'<?xml version="1.0"?><plist><date>bad private date</date>')
                result = subprocess.run([sys.executable, str(ROOT / "scripts/audit_bundle.py"), str(app)],
                                        capture_output=True, text=True, timeout=5)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(json.loads(result.stdout)["status"], "incomplete")
                self.assertNotIn("bad private date", result.stdout + result.stderr)

    def test_macho_inspector_cannot_be_selected_by_path(self):
        app = self.app()
        (app / "payload").write_bytes(b"\xfe\xed\xfa\xce")
        fake_tool = self.root / "otool"
        fake_tool.write_text("#!/bin/sh\nexit 1\n")
        fake_tool.chmod(0o755)
        with mock.patch.dict(os.environ, {"PATH": str(self.root)}), \
             mock.patch.object(bundle.os, "access", return_value=True), \
             mock.patch.object(bundle.subprocess, "run", return_value=subprocess.CompletedProcess(
                 [], 0, stdout="", stderr="")) as invoked:
            bundle.audit(app, macho=True)
            self.assertEqual(invoked.call_args.args[0][0], "/usr/bin/otool")

    def test_unreadable_tree_is_incomplete(self):
        app = self.app()
        def failed_walk(root, followlinks, onerror):
            onerror(PermissionError("Synthetic unreadable resource directory"))
            return iter([])
        with mock.patch.object(bundle.os, "walk", side_effect=failed_walk):
            report = bundle.audit(app)
        self.assertEqual(report["status"], "incomplete")

    def test_copy_timeout_never_reports_match(self):
        source, dest = self.trees()
        result = subprocess.run([sys.executable, str(ROOT / "scripts/verify_copy.py"),
                                 str(source), str(dest), "--timeout", "0.000001"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["verified"], False)

    def test_host_probe_timeout(self):
        report = host.probe([sys.executable, "-c", "import time; time.sleep(10)"], 0.01)
        self.assertEqual(report["status"], "timeout")


if __name__ == "__main__":
    unittest.main()
