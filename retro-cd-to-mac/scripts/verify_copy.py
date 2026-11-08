#!/usr/bin/env python3
"""Compare two file trees without following symlinks or changing either tree."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys


def inventory(root):
    entries, errors = {}, []

    def walk_error(exc):
        errors.append({"error": str(exc)})

    for directory, dirs, files, dir_fd in os.fwalk(root, follow_symlinks=False, onerror=walk_error):
        for leaf in dirs + files:
            name = (Path(directory) / leaf).relative_to(root).as_posix()
            try:
                info = os.stat(leaf, dir_fd=dir_fd, follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    entries[name] = ["link", os.readlink(leaf, dir_fd=dir_fd)]
                elif stat.S_ISDIR(info.st_mode):
                    entries[name] = ["directory"]
                elif stat.S_ISREG(info.st_mode):
                    entries[name] = ["file", info.st_size]
                else:
                    errors.append({"path": name, "error": "unsupported file type"})
            except OSError as exc:
                errors.append({"path": name, "error": str(exc)})
    return entries, errors


def digest(root, name):
    # Pin each parent directory so a replaced link cannot redirect a later open.
    parts = Path(name).parts
    dir_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory = os.open(root, dir_flags)
    try:
        for part in parts[:-1]:
            child = os.open(part, dir_flags, dir_fd=directory)
            os.close(directory)
            directory = child
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode):
                raise OSError("file type changed during verification")
            value = hashlib.sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                value.update(block)
            after = os.stat(parts[-1], dir_fd=directory, follow_symlinks=False)
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
                    after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
                raise OSError("file changed during verification")
            return value.digest()
    finally:
        os.close(directory)


def compare(source, destination, content=False):
    left, errors_left = inventory(source)
    right, errors_right = inventory(destination)
    report = {"mode": "content" if content else "metadata", "files_checked": 0,
              "missing": sorted(left.keys() - right.keys()),
              "extra": sorted(right.keys() - left.keys()), "different": [],
              "errors": errors_left + errors_right}
    for name in sorted(left.keys() & right.keys()):
        if left[name] != right[name]:
            report["different"].append(name)
        elif left[name][0] == "file":
            report["files_checked"] += 1
            if content:
                try:
                    if digest(source, name) != digest(destination, name):
                        report["different"].append(name)
                except OSError as exc:
                    report["errors"].append({"path": name, "error": str(exc)})
    report["status"] = "different_or_incomplete" if any(
        report[key] for key in ("missing", "extra", "different", "errors")) else (
        "content_match" if content else "metadata_match_only")
    report["limitations"] = "File-tree comparison only; no disc layout, audio tracks, protection or application completeness verification."
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--content", action="store_true", help="read and SHA-256 compare all regular files")
    parser.add_argument("--timeout", type=float, default=300, help="maximum total scan seconds; no automatic retries")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    if not args.worker:
        command = [sys.executable, str(Path(__file__).resolve()), str(args.source), str(args.destination), "--worker"]
        if args.content:
            command.append("--content")
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout)
            print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, end="", file=sys.stderr)
            return result.returncode
        except subprocess.TimeoutExpired:
            print(json.dumps({"status": "timeout", "verified": False,
                              "note": "Verification stopped. Inspect the drive; do not automatically repeat the scan."}))
            return 2
    try:
        source, destination = args.source.resolve(strict=True), args.destination.resolve(strict=True)
        if not source.is_dir() or not destination.is_dir():
            parser.error("source and destination must be directories")
        if source == destination or source in destination.parents or destination in source.parents:
            parser.error("use distinct, non-nested source and destination directories")
        report = compare(source, destination, args.content)
    except OSError as exc:
        print(json.dumps({"status": "error", "verified": False, "error": str(exc)}))
        return 2
    print(json.dumps(report, indent=2))
    return 1 if report["status"] == "different_or_incomplete" else 0


if __name__ == "__main__":
    sys.exit(main())
