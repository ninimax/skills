import os
from pathlib import Path
import tempfile
from unittest import TestCase
from unittest.mock import patch

from test_diagnostics import copy


class CopyBoundaryTests(TestCase):
    def test_replaced_parent_does_not_redirect_content_scan(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, dest, outside = (root / n for n in ("disc", "copy", "outside"))
            for directory in (source / "assets", dest / "assets", outside):
                directory.mkdir(parents=True)
                (directory / "track").write_bytes(b"same")
            original = copy.inventory
            def swap_after_inventory(tree):
                result = original(tree)
                if tree == dest:
                    (source / "assets").rename(source / "moved")
                    (source / "assets").symlink_to(outside, target_is_directory=True)
                return result
            with patch.object(copy, "inventory", side_effect=swap_after_inventory):
                report = copy.compare(source, dest, content=True)
            self.assertEqual(report["status"], "different_or_incomplete")
            self.assertEqual(report["errors"][0]["path"], "assets/track")

    def test_replaced_file_refuses_links_and_fifo(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "file").write_bytes(b"data")
            (root / "link").symlink_to("file")
            os.mkfifo(root / "pipe")
            for name in ("link", "pipe"):
                with self.subTest(name=name), self.assertRaises(OSError):
                    copy.digest(root, name)
