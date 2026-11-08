# Display, input, font and performance troubleshooting

Use this guide when an application opens but presentation, interaction, text or motion is wrong. These are evidence-driven diagnostic branches, not universal presets. Match the actual rendering/input path and runtime before selecting a change.

## Establish the working baseline

Record the application version, runtime build, wrapper version and checksum, launch arguments, rendering API, display size, backing-pixel scale, logical render resolution, window mode and relevant configuration. Retain a recoverable copy of the accepted configuration and user data. Make one diagnostic change at a time in an isolated candidate. Where a wrapper requires coupled settings, record that set as one experiment.

Run the exact delivered launcher, not an unrelated test launcher. A copied app can pick up another runtime environment, renderer or stale process. Stop only that candidate's processes before changing runtime or synchronization settings. When using Wine, do not kill all Wine processes. Verify that no process from the previous trial remains before comparison.

## Identify the rendering and input paths

Inspect supported settings, diagnostic output and imports before choosing a wrapper:

- GDI raster applications need GDI/window/modeset investigation. A DirectDraw DLL will not intercept a GDI-only path.
- DirectDraw applications may benefit from a DirectDraw wrapper. Determine whether it presents through OpenGL, GDI or another Direct3D translation layer.
- Direct3D 8/9 and OpenGL applications need API-appropriate candidates. A wrapper that helps a 2D workload may break a 3D workload.
- Mouse input may use Win32 client messages, screen-coordinate cursor APIs, absolute input or buffered relative DirectInput. Fixing one path does not automatically fix the others.
- Video playback can use a separate window, renderer and decoder. Menu success does not establish embedded-media or content-transition success.

Do not infer the active renderer solely from a configured DLL override or a crash reporter's module list. Confirm the actual loaded modules and successful renderer initialization when necessary.

If a wrapper ignores a windowed-mode request, check the setting against the configuration template for the **installed version**, including its section and whether the application can override it. Inspect the effective window or swapchain mode after the application changes resolution. A loaded wrapper can still present in exclusive fullscreen.

## Scaling and placement

| Symptom | Useful next check | Avoid |
|---|---|---|
| Fullscreen black surface with a small picture in one corner | Compare logical content size, render target, client rectangle and viewport; check whether fullscreen merely enlarged the container | Repeatedly toggling fullscreen without measuring the content |
| Picture shifted or an edge control unreachable | After the mode switch, measure the client origin in screen coordinates and add the client width and height. Compare all four edges with the actual virtual desktop bounds in the same units. A full-height client starting below the desktop top can put its last buttons outside the display. | Adjusting mouse sensitivity or hardcoding the observed offset |
| Picture fills one dimension with black bars | Compare content and monitor aspect ratios; full-height centered 4:3 can be correct | Calling pillarboxing a failure or stretching without user preference |
| Cropped UI after restart or mode change | Check persisted application resolution against wrapper and virtual-desktop size | Applying multiple independent scaling layers |
| Small but accurate playable window | Preserve it as baseline; test aspect-preserving presentation separately | Replacing the only playable version before the larger candidate passes |

Preserve the intended proportions of fixed-resolution content by default. For resizable desktop applications, prefer supported window resizing and layout reflow. “Fullscreen” means the application occupies the display; it does not require distorting 4:3 artwork to fill an ultrawide monitor. Offer stretch only if requested, explain its visual effect, and recheck input mapping.

Distinguish render resolution from presentation size. A larger backbuffer can increase GPU work; enlarging an unchanged low-resolution image is a different operation. Integer scaling can preserve pixel edges but leave more unused space. Nearest-neighbor and filtered presentation should be compared visually, especially for small text.

Wine Retina/modeset/display-capture behavior is runtime-specific. Record which driver owns a setting. Do not globally apply `RetinaMode`, `EmulateModeset` or `CaptureDisplaysForFullscreen`: choices can conflict across renderers, input APIs, versions and displays. Prefer supported application/runtime controls over custom hooks.

## Cursor geometry and visibility are separate problems

A second pointer with accurate clicks is a visibility defect. A single visible pointer can still have incorrect coordinates. Hiding the macOS pointer must never be used to conceal misalignment.

For an aspect-preserving viewport, let logical content coordinates be `Wg × Hg`, client dimensions in one consistent coordinate system be `Wc × Hc`, and `s = min(Wc/Wg, Hc/Hg)`. The centered viewport offset is `ox=(Wc-s*Wg)/2`, `oy=(Hc-s*Hg)/2`. Map a client pointer to content coordinates with `(x-ox)/s, (y-oy)/s`, applying the same transform for rendering and input. Account for the window's screen-to-client origin first. Convert backing pixels and logical points explicitly and exactly once. Define how out-of-viewport clicks are handled rather than silently clicking an edge control.

This formula is a diagnostic model, not permission to inject a generic hook. A wrapper may already perform the inverse transform; applying it twice causes another offset. Relative input has its own units and acceleration and cannot simply be treated as an absolute pointer position.

| Symptom | Investigation |
|---|---|
| Click lands consistently below pointer | Check window/client origin and title-bar offset before DPI or sensitivity |
| Error increases toward an edge | Compare input scale with render scale and viewport letterboxing |
| Pointer correct centrally, doubled or offset at screen edges | Test fullscreen capture/confinement, native edge UI, focus and client boundary handling |
| Pointer stuck while system pointer moves | Check input acquisition/cooperative mode and whether the application consumes relative DirectInput rather than transformed Win32 APIs |
| Two aligned pointers | Address visibility only; retain the accepted mapping and buttons |
| Works after switching away and back | Record a focus-acquisition workaround, then verify repeated launches and focus changes; do not claim a permanent repair |
| Renderer faster but mouse broken | Treat performance and input as separate acceptance gates; keep the prior working version |

Capture/confinement and cursor hiding must release on focus loss, normal quit and process failure. Do not install a global pointer-hiding helper or continuously force focus. If a per-application shim is necessary, constrain it to the exact process/build and actual client viewport, guard supported binaries, retain original files, and test dialogs and video transitions. Custom shims from one application build are not general-purpose fixes.

## Missing display modes and transitions

An application can request different display modes during startup, media playback and interactive content. Check the failing mode itself rather than assuming the configured main resolution applies throughout. A fixed Wine virtual desktop can be a diagnostic or acceptable windowed fallback, but enlarging it can reintroduce cursor and presentation bugs. Test transitions into and out of the affected content, not just the initial menu.

An application “Change Graphics Mode” error does not prove broken disc data. Conversely, a running process with a valid swapchain does not prove a visible usable application. Inspect the actual window and interaction.

## Text, encoding and legacy fonts

First distinguish missing glyphs/encoding from unreadable rasterization:

1. Confirm the intended language and codepage in the isolated runtime; do not impose a fixed locale on every application. Do not change global macOS language or fonts.
2. Determine the font actually selected by the application, not merely the requested face name.
3. Identify bitmap-font assets versus GDI font rasterization. An application using precomputed glyph assets will not necessarily respond to system-font substitutions.
4. For GDI, inspect nominal height, internal leading, glyph advance and rendering format. Positive font height can leave a much smaller usable glyph cell than expected.
5. Try a properly licensed font with suitable small-size metrics in the isolated environment only. Prefer the application's own selector if available. Preserve the original substitutions.
6. Check the exact document, dialog or briefing that failed, including dense characters, line wrapping, buttons and panel fit.

Small monochrome GDI glyphs can merge complex strokes when a fallback font leaves too little usable character height. Inspect glyph format and metrics before trying ClearType or image filtering; presentation filters cannot reconstruct strokes lost during rasterization. Evaluate a suitably licensed font in the isolated environment and verify the affected panel. A font present on one Mac is not necessarily available or redistributable elsewhere; no single face is a default for every user.

Offscreen glyph probes are diagnostic evidence. They do not establish actual text readability, layout fit or input correctness. Keep graphics and cursor settings unchanged during font-only experiments.

## Performance and frame pacing

Separate low frame rate, uneven frame pacing, input latency, loading time and slow processing or simulation. Record the same scene, settings and short interaction for each comparison. Collect frame times/FPS where available, CPU/GPU indicators and bounded logs; supplement with user-visible observation. Label subjective smoothness reports as such.

- Lower resolution helps only if the relevant work is resolution-dependent. If performance is unchanged, do not keep reducing image quality without another reason.
- An extra translation layer, software copies or GPU readbacks can cost time. Compare a suitable simpler renderer in isolation, then retest input and quitting.
- Use one pacing mechanism initially. Multiple limiters and vsync layers can interact. A cap can improve consistency but cannot raise a low frame rate.
- A configured frame cap is not proof of the observed frame rate or reduced CPU use. A static menu can still busy-poll between presented frames.
- For Wine, synchronization-mode changes require a fully stopped task-specific Wine server and consistent settings across its processes. They are not safe universal speed switches.
- Disable verbose diagnostic logging before delivery, but do not blame a small startup-only log for sustained lag without evidence.
- Keep loading-time comparisons separate from sustained responsiveness and rendering. Repeated starts may be faster because of caches; report cold and warm behavior where relevant.
- Stop when the accepted version meets the requested quality. Do not destabilize a working app for speculative gains.

## Crash, video and shutdown checks

Capture the exact trigger: startup, video, document or level loading, sustained use, saving or quit. Preserve a crash report and bounded runtime logs, with keys and private paths redacted before sharing. A report may fault inside its own reporting code and contain no original stack; do not attribute causation to that address.

If the frame freezes and the process is still alive, collect evidence **before** restarting it. Identify the affected process by executable and test environment; when available, take two short thread-stack samples a few seconds apart and compare them with CPU activity and the last log events. Look for repeated work, a blocked read or wait, or a window that no longer repaints. These are leads, not proof. If the process exited instead, inspect its exit status and crash report. Retest the specific transition in a normal launch: verbose tracing can change the timing.

Do not disable a runtime component globally to hide one startup problem. A component skipped at boot may be needed when opening a document, playing embedded video or loading a level. Audit earlier overrides at the failing transition. Restoring a component may recover interaction without fixing video presentation, so test and record those outcomes separately.

A shutdown hang is a failed acceptance check. Compare runtime, resource and localization differences separately when evidence points there. If only an alternative language build exits correctly, present that as a tradeoff requiring the user’s choice, not a reason to silently change language. Provide an application-scoped escape hatch if necessary; never force-quit unrelated applications.

## Required interaction evidence before promoting a display/input change

- Complete picture with expected aspect ratio and no cropped controls.
- Pointer and button activation at center, all four edges and corners; both click and drag where used.
- Left/right buttons, wheel, keyboard, camera/relative controls as relevant.
- Actual document, task or level opened beyond the menu; render-mode transition exercised.
- Focus away/back, window move/resize or fullscreen transition if supported.
- Readable text and complete dialogs; video failure distinguished from failure of the main task.
- Save/load and normal exit where relevant, then a fresh launch of the delivered app.

If native UI automation cannot exercise the application's input path, do not count a synthetic click or screenshot as success. Ask the user one targeted real-input check, record that evidence explicitly, and keep unverified claims bounded.
