# Pin Laser

A small **Windows** tray app that draws a glowing laser pointer — with a fading
trail — on top of your screen, following your mouse cursor. It is purely
visual: all mouse clicks pass through to the apps underneath, so you can use
it as a highlight tool during presentations, screen shares, and demos without
interfering with anything.

<!-- ![Screenshot](docs/screenshot.png) -->

## Features

- **Glowing laser dot** that always follows the cursor
- **Fading trail** for sweep-highlighting an area (shown while you hold a
  mouse button, or always — configurable)
- **Global hotkey** — `Ctrl+Shift+L` shows/hides the laser from anywhere
- **System tray menu** — Show / Hide / Settings… / Quit (left-click the tray
  icon to toggle too)
- **Customizable** — laser color, glow size, trail length, trail behavior,
  and trigger button (left / right / either)
- **Settings are saved automatically** and restored next launch
- **Multi-monitor & high-DPI aware** — the dot tracks the cursor correctly
  on mixed-DPI setups
- **Single-instance protection** — only one copy runs

## Requirements

- **Windows 10 or 11 (64-bit)**
- No Python or other software needed to run the app

## Download & Run

1. Grab the latest release from the [Releases](../../releases) page.
2. Extract the ZIP and double-click `PinLaser.exe`.
3. Press `Ctrl+Shift+L` to show/hide the laser.

> **First run:** the app is unsigned, so Windows SmartScreen may show
> *"Windows protected your PC"* — click **More info → Run anyway**. Some
> antivirus programs may flag the file; this is a common false positive for
> PyInstaller-packaged apps — allow it if so.

## Usage

- Press `Ctrl+Shift+L` to toggle the laser pointer.
- Left-click the tray icon to toggle it.
- Right-click the tray icon for **Show Laser**, **Hide Laser**,
  **Settings…**, and **Quit**.
- In **Settings…** you can pick:
  - **Trail behavior** — *Only while clicking* (default) or *Always show
    trail*
  - **Trail trigger button** — Left / Right / Either (on-click mode)
  - **Laser color**, **glow size**, and **trail length**

## Privacy & Safety

- Purely visual — the overlay is transparent to input, so it never
  intercepts your clicks or blocks other apps.
- **No network access** — nothing is uploaded or tracked.
- **No keylogging** — the mouse buttons are checked only to decide when to
  draw the trail.

## For Developers

Built with **PySide6 (Qt6)** + Win32 `ctypes`, packaged with **PyInstaller**.

```bash
# Install
py -m pip install -e .

# Run
pinlaser            # or: py main.py

# Tests
py -m pytest

# Package into a single exe
packaging\build.bat    # -> dist\PinLaser.exe
```

### Project structure

```
├── main.py               # entry point: tray icon, hotkey, single-instance lock
├── overlay.py            # click-through overlay window (16 ms cursor loop)
├── laser.py              # glowing dot + fading trail rendering
├── hotkeys.py            # Win32 global hotkey (Ctrl+Shift+L)
├── win_utils.py          # ctypes: GetCursorPos / GetAsyncKeyState
├── settings.py           # QSettings-backed app configuration
├── settings_dialog.py    # settings UI (live apply, cancel restores)
├── assets/               # app icon (PNG)
├── packaging/            # build.bat, icon/version tooling, PyInstaller files
└── tests/                # pytest suite (laser trail + settings roundtrip)
```

## Troubleshooting

| Problem | Fix |
|---|---|
| SmartScreen warning on first run | **More info → Run anyway** (unsigned exe) |
| Antivirus flags the exe | False positive — add an exception |
| Hotkey doesn't work | Another app may be using `Ctrl+Shift+L`; use the tray menu |

## Code signing

Releases are currently **unsigned**. An application for free code signing via
[SignPath Foundation](https://about.signpath.io) is in progress; once approved,
new tagged releases are built and signed automatically by the CI pipeline
(`.github/workflows/release.yml`), so future downloads from the Releases page
will be authentic and tamper-checked.

## License

Released under the [MIT License](LICENSE).
