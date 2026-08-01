---
name: pin-laser-app
description: Use when someone asks to build the Pin Laser app, create a Windows click-through laser pointer overlay, scaffold a PySide6 tray overlay app, or package it into a shareable exe.
disable-model-invocation: true
argument-hint: [output-dir]
---

# What This Skill Does

Builds the **Pin Laser** app from an empty folder to a shareable Windows exe:
a system-tray app that draws a glowing laser pointer (with a fading trail)
on top of the screen, following the mouse cursor. Purely visual -- all
clicks pass through to the apps underneath.

This skill captures BOTH the technology (PySide6 + Win32 ctypes + PyInstaller)
and the process (scaffold, overlay, laser, hotkey, settings, tests, packaging,
sharing). For exact Win32 signatures, window flags, and packaging commands, see
[reference.md](reference.md).

# Technology Stack

| Concern | Technology |
|---|---|
| GUI / tray / overlay | PySide6 (Qt6): `QSystemTrayIcon`, `QWidget`, `QPainter` |
| Cursor + mouse buttons | `ctypes.windll.user32` `GetCursorPos` / `GetAsyncKeyState` |
| Global hotkey | `RegisterHotKey` / `UnregisterHotKey` + `QAbstractNativeEventFilter` (WM_HOTKEY) |
| Persistence | `QSettings` (HKCU registry) |
| Single instance | `QLockFile` in `QStandardPaths.AppLocalDataLocation` |
| Rendering | `QRadialGradient` dot + deque of line segments for the trail |
| Tests | pytest |
| Packaging | PyInstaller `--onefile --windowed` |
| Metadata / icon | `version_info.txt` (VSVersionInfo) + multi-size ICO from PNG |

# Process

Run all commands from the target directory. If `$0` is provided, use it as the
project/output directory (create it and work inside it). If `$0` is empty,
use the current directory.

## 1. Scaffold

1. Create `requirements.txt` with exactly: `PySide6>=6.6`.
2. Create `main.py` as the entry point:
   - `QApplication(sys.argv)`, `setApplicationName("Pin Laser")`,
     `setQuitOnLastWindowClosed(False)`.
   - Acquire a single-instance lock BEFORE creating the tray/overlay
     (see reference.md). On failure, show a message box and `sys.exit(0)`.
   - Build the tray icon + menu: Show Laser, Hide Laser, Settings..., Quit.
     Tray left-click toggles the laser.
   - Register the hotkey; on failure notify via tray message but keep running.
   - `app.aboutToQuit.connect(hotkeys.unregister)`.
   - `resource_path(name)`: frozen -> `sys._MEIPASS`, source -> `assets/`
     first, then the script's directory (see reference.md).
   - `load_icon()`: load `app_icon_pin-laser.png` scaled to 64x64; fall back
     to a programmatically drawn radial-gradient dot if missing.
   - Honor `PINLASER_SMOKE=1` env: `QTimer.singleShot(2000, app.quit)`.

## 2. win_utils.py

- Define `POINT` (x, y `c_long`) and `MSG` ctypes structs (see reference.md).
- `get_cursor_pos()` -> `GetCursorPos` returns `(x, y)` or `(0, 0)`.
- `is_button_down(vk)` -> `GetAsyncKeyState(vk) & 0x8000`.
- Constants `VK_LBUTTON = 0x01`, `VK_RBUTTON = 0x02`.

## 3. hotkeys.py

- `RegisterHotKey(None, id, mods, vk)` with `MOD_CONTROL|MOD_SHIFT|MOD_NOREPEAT`
  for `ord("L")`. Keep the id (e.g. `0x4C4C`).
- `QAbstractNativeEventFilter` subclass: on `windows_generic_MSG`, cast the
  pointer to `MSG`; if `message == WM_HOTKEY (0x0312)` and
  `wParam == id`, invoke the callback.
- `installNativeEventFilter` on the app; `unregister()` removes it.

## 4. overlay.py (OverlayWindow)

- Flags: `FramelessWindowHint | WindowStaysOnTopHint |
  WindowTransparentForInput | Tool | WindowDoesNotAcceptFocus`.
- Attributes: `WA_TranslucentBackground`, `WA_ShowWithoutActivating`,
  `WA_TransparentForMouseEvents` (must stay click-through -- never remove).
- Geometry: union of ALL `app.screens()` geometries; track `_origin` top-left.
  Recompute on `screenAdded`/`screenRemoved` signals, in `show_laser()`, and
  via change-detection in `_tick()` (compare before calling `setGeometry`).
- `_tick()` (16 ms timer, only while visible): poll cursor, map to local
  coords (DPI-aware via `devicePixelRatio`, see reference.md), update the
  laser, call `self.update()`.
- Trail active if `trail_on_click` is off, or the configured mouse button
  is held (`VK_LBUTTON`/`VK_RBUTTON`/either).
- `paintEvent`: antialiased `QPainter`, delegate to `LaserEffect.paint`.

## 5. laser.py (LaserEffect)

- `deque` of `(x, y, t_monotonic)` points; `FRAME_TIME = 0.016`.
- `update_pos(x, y, trail_active)`: always store pos; append only when active;
  drop points older than `max_trail * FRAME_TIME` or beyond `max_trail`.
- `paint()`: draw the trail first, then the dot.
- Trail: for each consecutive pair, `age = (now - t2) / duration`;
  skip if `age >= 1.0`; alpha `int(220 * (1-age))`, width
  `1.0 + trail_width * (1-age)`, round caps/joins.
- Dot: pulsing `QRadialGradient` (white core -> `base.lighter(150)` ->
  base@190 alpha -> transparent), then a small white center dot.

## 6. settings.py + settings_dialog.py

- `DEFAULTS` dict: `trail_on_click=True`, `trail_button="left"`,
  `color="#ff2a1a"`, `glow_radius=28.0`, `trail_length=40`.
- `AppSettings(store=None)`: store defaults to `QSettings("PinLaser","PinLaser")`
  (injectable for tests); load each key with `type=` matching the default.
  `save()` writes all keys then `store.sync()` (durable).
- Dialog: combo (Only while clicking / Always), button combo (left/right/either),
  color picker, glow slider (10-60), length slider (8-80). Mutate `settings`
  live; `reject()` restores the values captured at open; `accept()` calls
  `settings.save()`.

## 7. Tests

- `tests/test_laser.py`: trail append/skip when inactive, max-length trim,
  expiry after duration (inject a fake `_clock`), `clear()`, pos update.
- `tests/test_settings.py`: defaults and save/load roundtrip using a temp
  `QSettings(path, IniFormat)` injected via `AppSettings(store=...)`.
- Run with `py -m pytest`.

## 8. Packaging

- `make_icon.py`: load `assets/app_icon_pin-laser.png` with `QImage`, scale
  to sizes 16..256, pack a multi-size ICO (PNG-compressed entries, see
  reference.md). Output `pinlaser.ico`.
- `version_info.txt`: `VSVersionInfo` with `CompanyName`, `FileDescription`,
  `ProductName`, `FileVersion`/`ProductVersion` (see reference.md).
- `build.bat`: `cd /d "%~dp0.."`; run `make_icon.py`; then PyInstaller with
  **absolute** `%CD%` paths (relative paths resolve against the spec dir):
  `--onefile --windowed --name PinLaser --icon ... --version-file ...`
  `--add-data "<abs>/assets/app_icon_pin-laser.png;."`
  `--specpath packaging --workpath build --distpath dist main.py`.

## 9. Share

- Zip `dist/PinLaser.exe` + a `HOW_TO_RUN.txt` (requirements, usage, and a
  note that the unsigned exe triggers SmartScreen -> "More info -> Run anyway").

## 10. Verify

1. `py -m pytest -q` -> all pass.
2. `PINLASER_SMOKE=1 py main.py` -> starts and exits cleanly.
3. Run `build.bat`; then `PINLASER_SMOKE=1 dist/PinLaser.exe` -> exit 0.
4. Check metadata: PowerShell `(Get-Item 'dist\PinLaser.exe').VersionInfo`
   shows the expected CompanyName/FileDescription.
5. Confirm `resource_path` resolves `assets/app_icon_pin-laser.png`.

# Output Format

```
[output-dir]/
├── main.py, overlay.py, laser.py, hotkeys.py, win_utils.py,
├── settings.py, settings_dialog.py, __main__.py
├── assets/app_icon_pin-laser.png
├── packaging/            # build.bat, make_icon.py, version_info.txt, pinlaser.ico
├── tests/                # test_laser.py, test_settings.py
├── dist/PinLaser.exe     # build output (share this, zipped)
├── pyproject.toml        # deps + console script; py-modules list (flat layout)
├── requirements.txt
├── .gitignore
└── README.md
```

# Notes

- **Windows-only.** `ctypes.windll` fails on macOS/Linux -- state this to the
  user and do not attempt cross-platform adaptations.
- **Never** make the overlay capture input. The whole app is click-through by
  design; removing `WindowTransparentForInput`/`WA_TransparentForMouseEvents`
  is out of scope.
- **Never** use `GetAsyncKeyState` for keyboard keys -- only `VK_LBUTTON` /
  `VK_RBUTTON`. No keylogging, ever.
- Keep per-frame work minimal (16 ms budget): the geometry change-check must
  early-return when nothing changed.
- PyInstaller onefile exes are often flagged by antivirus as false positives;
  the unsigned exe shows a SmartScreen warning. Document both for recipients.
- Keep file versions pinned in `requirements.txt` (`PySide6>=6.6`) to avoid
  surprise breakage.
- Preserve existing behavior when modifying; always re-run tests + smoke test.
