#!/usr/bin/env python3
"""Bounded read-only host inventory. No environment, key or registry dumps."""
import argparse
import json
import platform
import shutil
import subprocess


def probe(argv, timeout):
    try:
        run = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return {"status": "ok" if run.returncode == 0 else "error",
                "exit_code": run.returncode, "output": run.stdout[:24000],
                "error": run.stderr[:2000]}
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "note": "Do not infer absent hardware; inspect a stalled drive."}
    except OSError as exc:
        return {"status": "unavailable", "error": str(exc)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=15, help="seconds per system probe")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    report = {"system": platform.system(), "architecture": platform.machine(),
              "tools_on_path": {name: shutil.which(name) for name in
                                ("wine", "wineserver", "file", "otool", "codesign", "hdiutil")}}
    if platform.system() == "Darwin":
        report["probes"] = {name: probe(argv, args.timeout) for name, argv in (
            ("macos", ["/usr/bin/sw_vers"]),
            ("translation", ["/usr/sbin/sysctl", "-n", "sysctl.proc_translated"]),
            ("disks", ["/usr/sbin/diskutil", "list"]),
            ("free_space", ["/bin/df", "-h", "."]))}
    else:
        report["note"] = "macOS probes skipped; this host cannot establish Mac compatibility."
    report["limitations"] = ["Does not establish Rosetta availability from a native process.",
                              "Does not list GUI-only runtimes, GPU/display modes or disc contents.",
                              "Disk output may contain private volume names; review before sharing."]
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
