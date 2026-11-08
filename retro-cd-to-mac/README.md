# Retro CD to Mac

A Codex skill for installing, diagnosing and packaging legacy Windows software from the user’s own CDs, DVDs or disc images on macOS. It includes reusable diagnostic scripts and symptom-based troubleshooting guidance, with no product-specific presets, application assets or bundled runtime.

## Install

Copy the `retro-cd-to-mac` folder into `$CODEX_HOME/skills/` (normally `~/.codex/skills/`). Start a new Codex session if the skill does not appear. Python 3.9+ is required for the optional scripts. Native UI verification requires computer-use capability in the host agent; the skill does not supply that capability.

Example request:

> Use $retro-cd-to-mac for the Windows disc I inserted. Make a Mac app if compatible, preserve my files, and verify the display, mouse and normal use. Tell me whether it can run without the disc and on another Mac.

The agent discovers your setup before choosing a runtime or workflow. Compatibility differs by application, media condition, Mac architecture and macOS version. Some programs need a different environment. Disc-free operation and portability are separately tested properties.

Disc-free means legitimate physical-media independence through full installation, official updates or supported local media mapping. The skill does not bypass CD keys, activation, license checks or disc protection. If a required key or authorization is unavailable, it recommends legitimate recovery or publisher-supported alternatives rather than skipping the check.

## Contents and testing

- `SKILL.md`: the reusable workflow and reference routing.
- `references/`: generic installation, display, input, performance and packaging guidance.
- `scripts/`: read-only host inspection, disc-copy comparison and app dependency triage.
- `tests/`: synthetic regression tests for the diagnostic scripts.

Run `python3 -m unittest discover -s tests -v` from this folder. Tests validate diagnostic behavior, not arbitrary application compatibility. No second-Mac verification is implied. The skill adapts testing to the software: document editing/export for productivity tools, meaningful calculation for utilities, or map interaction for games.

The workflow includes cleanup of task-owned temporary tests and diagnostic artifacts after the needed evidence is captured. It preserves final deliverables, user data, required source copies, working rollback versions and evidence for unresolved issues; it does not automatically delete user files or empty Trash.

Share a clean export of the tracked skill files, not a working directory, its Git history or an installed game. The diagnostic scripts do not upload anything, but their local reports can identify volumes, filenames, user directories and installed tools. Keep reports, disc images, installers, CD keys and registered environments out of public archives and issues. Runtime/engine downloads and redistribution notices must be handled independently.

## Contributing a reusable improvement

This toolkit's original scripts and documentation are MIT-licensed; see `LICENSE`. Applications, fonts, runtimes and engines retain their own separate licenses and are not included.

Contribute a reproducible symptom, evidence that distinguishes causes, a scoped diagnostic method, rollback guidance, verification and limitations. Organize shared guidance by failure mode or technical subsystem, never by product title or someone’s collection. Keep product names, edition-specific settings and machine details in private local case notes. Remove credentials, personal paths and proprietary data from shared examples. A configuration that worked once must not become a universal default.
