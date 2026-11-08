# Diagnostic tools

Run from the skill folder, or use absolute paths to its scripts. Python 3.9+ is required. JSON goes to standard output; save reports in the user's private task folder, not in the shareable skill. Paths and volume names can be personal information. These tools are read-only and never launch an application, install software, swap a volume or delete files.

## Inspect a Mac

```sh
python3 scripts/inspect_host.py --timeout 15
```

Reports macOS, process architecture, disk listing, current-volume free space and relevant commands on PATH. Each probe has a timeout. GUI-only runtimes, actual display modes and contents of the disc require separate inspection. `sysctl.proc_translated` is not an installation check for Rosetta. A timeout or permission error is not a negative hardware result.

## Compare a disc copy

```sh
python3 scripts/verify_copy.py "/Volumes/DISC" "/path/to/local/disc-copy"
python3 scripts/verify_copy.py "/Volumes/DISC" "/path/to/local/disc-copy" --content --timeout 600
```

First invocation compares names, file sizes, directories and literal symlink destinations. `metadata_match_only` does not establish intact file content. The second reads regular files and compares SHA-256. It reports missing, extra, differing and unreadable entries and does not follow symlinks. Do not compare changing trees or install into the source copy while verifying. Metadata and permissions are not preserved or compared by this script; use an appropriate separate copying method.

The timeout covers the whole scan in a child process, not a promise that an unresponsive physical drive will immediately recover after cancellation. The script does not retry reads. If verification times out, inspect media/drive state first. Hashing a whole optical disc may take substantially longer than an SSD copy; choose a justified limit rather than looping failed scans.

Exit 0 means the selected comparison finished with no reported difference. Exit 1 means a difference or read failure. Exit 2 means timeout or invalid invocation. Neither a content match nor an ISO file-tree match verifies audio tracks, sector layout, media checks or installer completeness. A symlink match confirms the stored target text only, not the external target's content.

## Audit a Mac bundle

```sh
python3 scripts/audit_bundle.py "/path/to/Example.app"
python3 scripts/audit_bundle.py "/path/to/Example.app" --macho --max-files 150000
```

Checks the bundle entrypoint, symlinks, shell launchers directly under `Contents/MacOS`, and optionally absolute Mach-O library references with `otool`. It flags `$HOME`-based state as needing review, even when intentionally designed. Wine `z:` and user-directory links can be intentional: do not erase links automatically. A relative internal link is portable only if its destination remains bundled.

Reports `no_static_findings`, `review_findings`, or `incomplete`. Exit 0 means the scan completed, not that findings passed or portability was verified. Exit 2 means incomplete scan or invalid invocation. Read the JSON status and findings. Nested helpers, compiled launcher logic, registry references, shell expansions, runtime plugins, architecture compatibility, relative library search paths and code signatures still require review. No registry or credential inspection is performed, and launcher source is not printed.

The auditor reads bundle metadata only from a regular file inside the bundle, up to 4 MiB. Unreadable, malformed or skipped metadata makes the scan incomplete. Optional native library inspection uses the system tool at `/usr/bin/otool`.

Run from a trusted, quiescent copy. These tools are not sandboxes for hostile files or forensic validators. Keep raw reports private. For public troubleshooting, share only the relevant status or a redacted finding; paths, filenames, symlink destinations and disk listings can identify your account and media.
