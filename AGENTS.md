# AGENTS.md

Project-wide instructions for this repository.

## Skills

- **`/pin-laser-app`** — Builds the Pin Laser app (Windows click-through
  laser-pointer overlay) from an empty folder to a shareable exe:
  PySide6 + Win32 ctypes overlay, global hotkey, settings, tests, and
  PyInstaller packaging with publisher metadata and icon.
  - Trigger phrases: "build the pin laser app", "scaffold the laser
    pointer overlay", "create a Windows click-through overlay app".
  - Invocation: slash-command only (the model will not auto-run it).
  - Argument: optional `[output-dir]`.
  - Output: working app + `dist/PinLaser.exe` + share zip in the
    target directory.

## Conventions

- Windows-only app (uses `ctypes.windll`); do not port to macOS/Linux.
- The overlay must remain click-through (`WindowTransparentForInput`,
  `WA_TransparentForMouseEvents`) — never capture input.
- `GetAsyncKeyState` is used only for mouse buttons, never keyboard keys.
- Keep per-frame work under the 16 ms tick budget.
- Run `py -m pytest` and the `PINLASER_SMOKE=1` smoke test after changes.
