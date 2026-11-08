# Disc intake and installation

Use this reference for unknown Windows CDs/DVDs. These are diagnostic branches, not mandatory settings for every application.

## Establish the source and scope

Record the product, edition, language, disc labels, installation/play-disc roles, number of discs, relevant executable architecture, and host/runtime architecture. Inspect read-only before launching an executable. A disc can contain both Windows and classic Mac content; an unreadable classic Mac partition does not prove the Windows data track is unreadable.

Identify the mounted volume and its current device before copying, remapping or ejecting. Device numbers can change after any swap or image mount. Never reuse a remembered raw device identifier. Do not format, repair-write or initialize the original media. Present a request to insert a particular disc only when that physical intervention is necessary.

Distinguish these situations:

- No device detected: inspect connection, power and available drive information.
- Device detected but no mounted volume: inspect filesystem and track layout before declaring the medium damaged.
- Files visible but reads stall: preserve completed work, note the exact file or sector, and investigate media/drive reliability.
- Installer starts but fails: treat this as an installation/runtime issue until a read failure is evidenced.

A compatibility runtime translates supported Windows behavior; it is not a guarantee for every Windows program. Kernel drivers, hardware dongles, obsolete online activation, unsupported 16-bit installers and certain disc checks can require another supported environment. Document the blocker and supported alternatives instead of repeatedly changing graphics settings.

## Copy without destroying evidence

Prefer an immutable local copy for installation. Record each file's relative path, size, successful read and digest, plus disc identity and acquisition method. Verify copied data against the source where reads are reliable. A hash of the destination alone proves only that a later copy can be compared with that destination, not that the original disc was read correctly.

For raw or mixed-mode media, preserve the track/layout information the software needs. A directory copy or newly built ISO may omit audio tracks and other disc metadata. Do not label it a faithful full-disc image without checking that distinction.

Use bounded retries. On a stalled read, stop the specific copy process, retain partial data and an explicit incomplete status, and ask for one physical inspection/clean/reinsert or an alternate reader when appropriate. Do not restart an endless full-disc copy loop. Resume only after verifying the reinserted medium and the existing prefix of copied data. A partial image ending at a sector boundary is still incomplete. Never install from a known incomplete image without explicitly scoping the attempt and its limits.

Keep verified source copies separate from modified installer media. If adding a compatibility wrapper to a derived installer image, record the modification and preserve the original copy.

For a compilation, compare each installer’s file list and referenced media with the actual payload. A file with a movie or audio extension may contain only a short placeholder or a list of filenames. Inspect its format before promising playback. Matching disc hashes or archive checksums can confirm that the supplied bytes survived copying or extraction even when the edition omits content. Record such omissions separately from any crash whose cause is still unknown.

## Isolate installation

Create an isolated environment appropriate to the application and selected route. For Wine, use a dedicated prefix and inspect user-folder links. For VMs/emulators, inspect shared folders, disk images and configuration. For native installers or data extraction, stage output where practical. A cloned environment can still share real documents or saves. Record intentional shared locations.

Do not reuse an unrelated application’s registered environment as a generic template. Its keys, registration, overrides, fonts and patches can contaminate the result. A runtime may be reusable; a registered installation generally is not.

Determine installer and program requirements separately. Scope Windows-version emulation and DLL overrides to the executable that needs them; installer requirements can differ from those of the application. One runtime may help installation while another runs the application better. Preserve the completed installation and test independently. Do not select a Windows version solely from the disc’s age.

If no window is visible, check whether the intended executable started, whether its process exited, and whether a dialog is behind another window or on a virtual desktop. A locked Mac or inaccessible UI needs a user handoff. A running process does not prove the installer is usable. Prefer the original installer; alternate launcher executables require evidence of their role.

## Multi-disc installers

Capture all installation discs separately, preserving exact labels and contents. Do not merge discs and assume the installer will accept the combined folder. Common checks include volume label, drive type, source drive, source path, a particular file and the original launch location.

At a disc prompt:

1. Read the exact requested disc, including whether setup asks to return to disc 1 after disc 2.
2. Keep the current installer and entered registration state alive.
3. Inspect the source drive that this installer actually uses.
4. Map the requested verified local disc to that same drive when required. Check label and CD-ROM type through the runtime, not only the Mac's Finder name.
5. Retry the existing prompt once and observe whether progress resumes.
6. If it loops, trace narrowly scoped volume/path queries before another full restart.

A label marker file may not be honored by the runtime. A read-only labeled image can help, but its actual reported label must be verified. A runtime can also replace a drive mapping with the newly mounted physical volume; inspect again after swaps.

If correct labels on additional drive letters do not resolve the prompt, determine whether setup queries its original launch/source drive. When required and supported, swap verified media behind that same runtime drive, including returning to an earlier disc if requested. Do not prescribe a universal drive letter or assume the sequence always moves forward.

Do not repeatedly restart setup and ask for the key again. First preserve the active installer and diagnose its current failure. Do not invent registration entries merely because the files appear installed.

## Keys, licenses, text and installation completion

Request a key only when the actual installer requires it. Prefer direct user entry into the installer; installation-time key entry does not imply reentry on every launch. Do not publish keys, entered names, raw registry dumps or registration-bearing archives. If the user supplied a key, avoid repeating it in logs, command arguments, reports or the shared package. Follow the current tool's confirmation requirements for license acceptance; past acceptance of another product does not determine this product's terms.

Owning physical media does not remove a separate key, activation or license requirement. If asked to skip or bypass a required check, do not do so. Do not use fabricated or third-party keys, invented registration entries, key generators, cracks or unauthorized modified executables. Offer legitimate options such as locating the original key, publisher recovery or support, or an official digital edition. Read-only copying and diagnosis may continue without crossing the check.

Fix unreadable installer text before the user must review a license or input a key. Distinguish incorrect code page/encoding from missing font glyphs and scaling blur. Use an appropriately licensed font already available or an explicitly sourced redistributable font. A font available on one Mac is not automatically available or redistributable on every Mac. Scope substitutions to the affected environment and visually verify full labels and text fit. See [display-input-performance.md](display-input-performance.md) for rendering issues.

Successful archive extraction is not a complete installation. The original installer may generate key-derived assets, install locale-specific files, register components, write program paths or configure other data after extraction. Validate its final completion state and required program files. Preserve the installed environment before applying updates.

If a patch or startup reports missing files after extraction, check whether the genuine installer generates registered assets, installs optional components or creates locale-specific data. Complete supported installation rather than fabricating missing payloads. A successful patch does not establish that all required files are present or that real work can proceed.

## Diagnose misleading errors narrowly

If the program says its files are corrupt after extraction, identify the path it tried to open. Compare the launch working directory, source drive and installed paths with what the original installer sets. For a Windows registry path, check the key, value type and 32- or 64-bit view actually read by the process. Restore only entries supported by installer records or a verified install, then retry the failing action. A generic warning alone is not a reason to reread the disc or reinstall.

A Windows installer saying administrator privileges are required is not proof that macOS permissions must be widened. Inspect the exact failing Windows operation and error code. Do not respond with global permissions changes, disabling platform security or running the entire workflow as root.

A generic administrator error can mask a runtime registry-semantics failure such as ERROR_CHILD_MUST_BE_VOLATILE (1021). Confirm the failing API and affected key before considering a narrowly scoped remedy. Preserve the environment first. Do not change unrelated permissions or keys, fake successful API results or skip installer completion work just to suppress a message.

## Updates and provenance

Match patches to product, edition, language and installed version. Inspect updater logs for actual failure, missing files and prerequisites. Keep the registered install backup. Prefer vendor-distributed updates and document the source, exact version, digest and verification performed.

A matching hash from an archive is not publisher authentication. An unsigned archive-hosted updater, a valid publisher signature, a weak archive signature and a failed timestamp-chain verification are different evidence states. Report precisely which checks passed. Pin downloaded runtime/tool versions and digests; do not silently fetch a moving latest build for a previously verified configuration. Follow current execution permissions for nonstandard sources.

Preserve publisher files and application data. Use official updates or a supported replacement engine when appropriate. A replacement engine must be compatible with this edition and tested with its installed assets; verify the features and formats the user needs, including media or extensions where relevant. Do not bundle proprietary disc contents or user registration into the public skill.

## Transition to packaging

Record the verified installed location and restore the launcher from installation mode to program mode. Remove temporary diagnostic hooks from the deliverable. Then follow [packaging-verification.md](packaging-verification.md); installation complete, interface visible, usable, physical-disc-free and portable are separate claims.
