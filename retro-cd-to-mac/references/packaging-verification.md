# Packaging, verification and recovery

Use this reference before promoting any candidate to the user's final deliverable or sharing the workflow. Keep the original installation and the most recent verified configuration until the replacement is accepted.

## Define the deliverable honestly

These are separate properties:

- **Installed:** the original installation and required registration steps completed.
- **Launches:** the intended application reaches visible, responsive UI.
- **Usable:** a representative document, task, mission or map works, including relevant controls.
- **Physical-disc-free:** it works with the original CD/DVD removed. A bundled local image can still be required.
- **Self-contained:** the application runtime and required initial assets are bundled, apart from documented system prerequisites. Required external runtime/assets mean it is not self-contained, even when those dependencies are documented.
- **Relocatable:** moving the bundle does not break paths or silently lose existing state.
- **Portable:** another compatible Mac can initialize and run it with all prerequisites documented. A clean-account test on the same Mac is useful intermediate evidence, not a substitute for a second-Mac test.

One property does not imply the next. A running Wine process, updater success, headless decoder test or screenshot of a menu is not an end-to-end acceptance result. Mark untested features as untested.

## Deliverable layout and writable state

For app bundles, resolve paths from the actual bundle, with correct quoting for spaces and non-ASCII filenames. For other deliverables, resolve paths from their supported installation/configuration location. Never hard-code a creator’s username, Desktop, temporary mount, workspace or device number. Check runtime and host architecture requirements, including any translation prerequisite.

Choose and document a state model suited to the deliverable. The following are Wine app-bundle options, not requirements for VM, emulator, native or data-only workflows:

- A writable bundled prefix can work locally but may fail in read-only locations, protected folders or shared accounts. Mutating a signed bundle also complicates distribution.
- An immutable bundled seed plus a per-user writable runtime is often easier to maintain. Use a stable application identity and a suitable per-user application-support location. This is external user data, not a reason to claim the entire running installation is inside the app.

Initialize a writable runtime only if absent. Do not overwrite it from the seed on each launch. A fresh seed contains no later user files or settings. Before changing runtime location or version, identify existing documents/saves/settings/registration, copy them safely, verify the new state, and retain a rollback path. Never automatically discard a prefix after a failed launch.

A distributable automation package should contain instructions, scripts, manifests and redistributable templates, not a registered prefix or disc image. Runtime binary redistribution needs its required notices and source/provenance information. Do not transplant a locally available proprietary font into a public package merely because it solved a rendering issue.

## Dependency audit

Inspect the final launcher's complete flow and helper scripts, not only the first executable. Check:

- Paths in scripts, configuration, registry values and app metadata, using targeted reads that avoid secret-bearing values.
- Symlinks and their resolved destinations, including Windows drive mappings and user-folder links.
- Runtime frameworks, dynamic library paths, renderer plugins and architecture-specific components.
- Local images, mount points, external writable prefixes and any helper process that initializes them.
- Working-directory assumptions and paths left over from temporary installer/test launchers.

A path scan is a finding aid, not proof of independence. Follow a suspect dependency to its caller and exercise the final artifact. Do not delete a working directory just because its name contains `work` or `test`.

A launcher may initialize a separate writable runtime or continue using a development environment. Removing that directory can delete current documents, saves, registration or settings even if an initial seed can be recreated. Trace live state before cleanup. Locally usable software is not proven portable by copying its icon alone.

## Local virtual-disc lifecycle

If a local disc image is required, resolve it from the installed bundle or declared persistent data location. Mount it read-only; discover the returned device and mount path rather than assuming a disk number. Map the required drive/label and verify it through the compatibility runtime.

Track ownership of each mount. On normal exit and failed launch, detach only mounts created for this invocation when no active consumer still needs them. Never eject unrelated media. Guard concurrent launches so one instance cannot detach a disc another is using. Keep a useful recovery path if the app is forcibly terminated before cleanup.

When disc-free operation is required, test startup with the physical disc removed. If claiming independence from all virtual source media, detach installer images too. A runtime that hangs while probing an empty optical reader is a different issue from missing application assets; inspect drive mappings and relevant startup diagnostics before asking for repeated disc swaps. A successful test after unplugging a reader does not establish that connected-reader startup is fixed.

## Crash and cinematic investigation

Reproduce the user's exact transition: startup, menu to document/map, embedded video to interactive content, several minutes of use, save/load or exit. Record visible result, exit status, runtime version and narrow diagnostics. Preserve a baseline and change one relevant variable per candidate.

Use task-specific logging, preferably with a unique run filename so a restart cannot overwrite the fault. Avoid raw registry dumps, environment dumps and user documents. A crash report's displayed offset may belong to its crash reporter rather than the original failing application instruction. Do not assign a cause without supporting evidence.

If startup works but embedded video or subsequent content crashes, inspect earlier component-disable overrides alongside codecs and renderers. For a DirectShow application under Wine, a `quartz=` disable entry is one relevant setting to investigate, not a universal toggle. Alter only the component implicated by reproduction, in isolation. Verify visible playback, skipping and transition into real work separately; recovering a transition does not prove video presentation works.

A decoder producing frames off-screen does not prove the application's actual playback window, sound, subtitles or transition works. Test those separately. If skipping a problematic intro is an accepted workaround, preserve its source and state the limitation. Do not silently disable all audio or movies to obtain a successful menu.

## Acceptance matrix

For each test, record date, artifact/configuration fingerprint, host and runtime versions, action, observed result, who observed it, and remaining limits. Prefer direct app interaction; ask the user only for physical interventions, inaccessible UI or a subjective quality judgment that materially affects the result. Do not repeatedly ask them to run the same failed test without a new diagnostic purpose.

Minimum relevant checks:

| Area | Evidence to collect |
| --- | --- |
| Installation | Correct product/edition/language, completed installer, required files and matching update status |
| Startup | Cold launch of the actual exported app from its intended destination |
| Representative use | Exercise a meaningful operation; if completion was the failure, verify the finish and return to a usable screen, or complete the export and reopen the result |
| Display/input | Correct aspect ratio, no clipping, pointer/click alignment at center and edges, focus switch and return |
| Performance | Repeat the same workload before/after; separate first-load delay from recurring stutter |
| Text/audio/video | Readable labels and content without overflow; relevant sound and cinematic transitions |
| Persistence | Save and reload test data without overwriting the user's existing data |
| Exit | Normal quit closes the window/process and owned mounts; a second launch succeeds |
| Media | Physical disc absent, and installer image absent when the claimed mode permits it |
| Location | Launch after moving the artifact; inspect the state location and dependencies again |
| Portability | Clean account or another supported Mac, or explicitly mark this untested |

Select checks for the user's actual work: import/export, printing, device interaction, playable levels or other core tasks. Mark irrelevant checks not applicable with a reason. Media independence, relocation and portability checks depend on the requested deliverable. Do not imply that hardware integrations work merely because a document window opens.

Keep test duration proportional to the task. A short representative test is useful, but do not call it exhaustive coverage. State known omissions such as network play, expansion campaigns, video, CD audio, hardware support or another Mac.

## Promote without regressing

Keep experiments in isolated environments or copies, such as dedicated prefixes when using Wine. APFS cloning can reduce copying cost, but inspect links and shared external data before calling a clone isolated. Identify the most recent user-confirmed version, not merely the latest file timestamp.

Promote only the smallest tested change. Preserve current documents, saves, settings and registration; do not overwrite a live environment with an older test clone. Compare launcher/configuration and relevant artifact hashes after copying. Launch and test the actual final destination, because exporting or relocating can introduce new permissions, paths and runtime initialization behavior.

Once acceptance passes, stop speculative tuning. For a later performance request, start a new candidate from the working baseline. Do not let a faster renderer silently replace a version whose cursor and exit behavior were verified. If the new candidate fails a previously passing check, retain the working version and report the tradeoff.

## Process cleanup and space recovery

Cleanup is part of every test lifecycle, not only a final tidy-up. Prefer a unique task-owned temporary directory and register artifacts as they are created: extracted installers, cloned or copied environments, downloaded packages, mounted images, logs, screenshots, crash reports and redirected diagnostic output. Scripts should use temporary-directory context managers or explicit cleanup handlers where practical. Do not wait until the end to discover which directories a test created.

After each rejected candidate, and after the accepted replacement passes final-location acceptance, classify the artifacts:

- Keep the final deliverable, current documents/saves/settings, requested or evidential source copies, and the last working rollback until the replacement is accepted.
- Keep a small, sanitized diagnostic record for unresolved problems. Remove bulky raw traces and screenshots once the needed facts are preserved, unless the user asked to retain them or they are still needed for diagnosis.
- Remove obsolete test copies, extracted installers, superseded downloads, temporary virtual-disc images and generated reports that are no longer needed. Do not treat a file called `final`, `backup`, `test` or `work` as disposable from its name alone.

Before removal, trace references from the final deliverable and other live environments. Delete only exact task-owned paths inside the intended workspace or temporary root, with no broad name-based globs. Prefer a recoverable, clearly named Trash location for user-visible artifacts. Permanent deletion is appropriate only for known task-owned temporary content within the authorized scope. Never empty the user's whole Trash as part of routine cleanup.

Stop only this application's owned processes and environment. When using Wine, do not use global kills that can terminate unrelated applications. Supply the correct prefix and runtime environment for a targeted wineserver operation; verify termination, waiting for that prefix's server when needed, before moving or changing its state.

Before cleanup, inventory final deliverables, active runtimes, user data, registered environments, source discs and rollback assets. Scan dependencies and check for running test instances. Detach only mounts owned by the finished test after confirming that no active consumer still needs them. Remove only authorized obsolete artifacts. Prefer a clearly named recoverable Trash folder with an original-location manifest when practical. Do not delete every directory matching `test` without dependency inspection.

After cleanup, launch the final deliverable again and perform the smallest relevant interaction to expose a hidden dependency on deleted staging files. Record what was removed, what remains and why. List large retained artifacts with logical sizes. Where useful, compare `du` logical usage and `df` free space before and after; neither is a guaranteed measurement of recoverable physical space.

Moving files to Trash does not immediately recover their storage. Emptying Trash is permanent and may include unrelated items, so inspect its contents before advising that it is safe. Report logical size separately from physical space reclaimed: APFS clones share blocks, and snapshots or other references may retain storage. Never claim the sum of duplicate app sizes is guaranteed recoverable space.

## Handoff report

Give the final deliverable location, how to launch and quit, where current documents/saves/settings live, required runtime/host prerequisites, disc-free status, known workarounds, and exactly what was tested. Include a concise restore route to the prior verified configuration. Share sanitized symptom-based methods and reproduction steps, not private diagnostics or licensed application data.
