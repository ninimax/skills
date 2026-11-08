#!/usr/bin/env python3
"""Static dependency triage, not proof of portability. Does not execute the app."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import re
import stat
import subprocess
import sys

MACHO = {b"\xfe\xed\xfa\xce", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe",
         b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca", b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca"}
SYSTEM_OTOOL = "/usr/bin/otool"
MAX_PLIST_BYTES = 4 * 1024 * 1024


def read_bundle_info(app, plist):
    try:
        resolved = plist.resolve(strict=True)
        if app not in resolved.parents:
            raise ValueError("Info.plist resolves outside the bundle")
        info = resolved.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_PLIST_BYTES:
            raise ValueError("Info.plist is not a regular file within the size limit")
        fd = os.open(resolved, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or not os.path.samestat(info, opened):
                raise ValueError("Info.plist changed before it could be read")
            data = stream.read(MAX_PLIST_BYTES + 1)
        if len(data) > MAX_PLIST_BYTES:
            raise ValueError("Info.plist exceeds the size limit")
    except (OSError, RuntimeError) as exc:
        raise ValueError("Info.plist is inaccessible or its link cannot be resolved") from exc
    try:
        values = plistlib.loads(data)
    except Exception as exc:
        # plistlib exposes format-specific parser exceptions; omit any input text.
        raise ValueError("Info.plist could not be parsed") from exc
    if not isinstance(values, dict):
        raise ValueError("Info.plist must have a dictionary root")
    return values


def audit(app, max_files=100000, macho=False):
    app = app.resolve(strict=True)
    issues, scanned = [], 0
    def flag(path, kind, detail):
        issues.append({"path": str(path.relative_to(app)), "kind": kind, "detail": detail})
    plist = app / "Contents/Info.plist"
    try:
        info = read_bundle_info(app, plist)
        name = info.get("CFBundleExecutable")
        if (not isinstance(name, str) or not name or name == ".." or "\x00" in name
                or Path(name).name != name):
            flag(plist, "invalid_executable", "Missing or invalid CFBundleExecutable")
        else:
            executable = app / "Contents/MacOS" / name
            target = executable.resolve(strict=False)
            if app not in target.parents or not target.is_file() or not os.access(target, os.X_OK):
                flag(executable, "missing_executable", "Launcher missing or not executable")
    except (OSError, ValueError, RuntimeError) as exc:
        flag(plist, "invalid_plist", str(exc))
    def walk_error(exc):
        issues.append({"kind": "scan_error", "detail": str(exc)})
    for directory, dirs, files in os.walk(app, followlinks=False, onerror=walk_error):
        for name in dirs + files:
            path = Path(directory) / name
            scanned += 1
            if scanned > max_files:
                issues.append({"kind": "scan_limit", "detail": "Audit incomplete; increase --max-files after reviewing size."})
                return {"status": "incomplete", "entries_scanned": scanned - 1, "findings": issues}
            if path.is_symlink():
                try:
                    target = path.resolve(strict=True)
                    if target != app and app not in target.parents:
                        flag(path, "external_link", os.readlink(path))
                    elif os.path.isabs(os.readlink(path)):
                        flag(path, "absolute_internal_link", "Resolves inside this bundle now but breaks when moved")
                except (OSError, RuntimeError) as exc:
                    flag(path, "broken_or_cyclic_link", str(exc))
                continue
            if not path.is_file():
                continue
            try:
                # Only launcher text is inspected. Never read registry files, save files or key data.
                relative = path.relative_to(app)
                if relative.parts[:2] == ("Contents", "MacOS") and path.stat().st_size < 262144:
                    raw = path.read_bytes()
                    if raw.startswith(b"#!"):
                        source = raw.decode("utf-8", errors="replace")
                        for pattern, kind in ((r"/(Users|home|Volumes|private/tmp|tmp)/", "machine_path"),
                                              (r"\$(?:\{)?HOME\b|~\/|expanduser|Path\.home", "user_external_state"),
                                              (r"/opt/homebrew/|/usr/local/", "external_tool_dependency")):
                            if re.search(pattern, source):
                                flag(path, kind, "Review this launcher's external references; source omitted for privacy")
                if macho:
                    with path.open("rb") as stream:
                        magic = stream.read(4)
                    if magic in MACHO:
                        if not os.access(SYSTEM_OTOOL, os.X_OK):
                            flag(path, "macho_unchecked", "otool unavailable")
                            continue
                        result = subprocess.run([SYSTEM_OTOOL, "-L", str(path)], capture_output=True,
                                                text=True, errors="replace", timeout=10)
                        if result.returncode:
                            flag(path, "macho_unchecked", "otool failed")
                        for line in result.stdout.splitlines()[1:]:
                            dep = line.strip().split(" (", 1)[0]
                            if dep.startswith("/") and not dep.startswith(("/System/Library/", "/usr/lib/")):
                                flag(path, "absolute_library", dep)
            except (OSError, subprocess.TimeoutExpired) as exc:
                flag(path, "scan_error", str(exc))
    incomplete = any(issue["kind"] in ("invalid_plist", "scan_error", "macho_unchecked") for issue in issues)
    return {"status": "incomplete" if incomplete else ("review_findings" if issues else "no_static_findings"),
            "entries_scanned": scanned, "findings": issues,
            "limitations": ["Not a portability verdict; test relocation and another Mac/account.",
                            "Does not analyze registry, dynamic code, relative rpaths, plugins, signing or embedded secrets.",
                            "External Wine device/user links may be intentional; classify rather than delete blindly.",
                            "Nested helper scripts outside Contents/MacOS need manual review.",
                            "--macho adds library inspection but can be slow on large runtimes."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", type=Path)
    parser.add_argument("--max-files", type=int, default=100000)
    parser.add_argument("--macho", action="store_true", help="also inspect Mach-O absolute library references with otool")
    args = parser.parse_args()
    if args.max_files < 1:
        parser.error("--max-files must be positive")
    if not args.app.is_dir() or args.app.suffix.lower() != ".app":
        parser.error("supply an existing .app directory")
    try:
        report = audit(args.app, args.max_files, args.macho)
    except OSError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}))
        return 2
    print(json.dumps(report, indent=2))
    return 2 if report["status"] == "incomplete" else 0


if __name__ == "__main__":
    sys.exit(main())
