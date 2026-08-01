# Pin Laser App -- Technical Reference

Supporting reference for [SKILL.md](SKILL.md). Contains exact Win32
signatures, window flags, DPI math, and packaging commands used by the
Pin Laser app. Not loaded automatically -- read it when you need details.

---

## Win32 ctypes (win_utils.py)

```python
import ctypes
from ctypes import wintypes

VK_LBUTTON = 0x01
VK_RBUTTON = 0x02

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", ctypes.c_uint),
        ("wParam", ctypes.c_size_t),
        ("lParam", ctypes.c_ssize_t),
        ("time", ctypes.c_ulong),
        ("pt", POINT),
        ("lPrivate", ctypes.c_ulong),
    ]

_user32 = ctypes.windll.user32
_user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
_user32.GetCursorPos.restype = wintypes.BOOL
_user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
_user32.GetAsyncKeyState.restype = ctypes.c_short

def get_cursor_pos():
    pt = POINT()
    if _user32.GetCursorPos(ctypes.byref(pt)):
        return pt.x, pt.y
    return 0, 0

def is_button_down(vk):
    return bool(_user32.GetAsyncKeyState(vk) & 0x8000)
```

## Global hotkey (hotkeys.py)

```python
WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000

# RegisterHotKey(None, hotkey_id, mods, vk)
if not _user32.RegisterHotKey(None, hotkey_id,
                              MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT, ord("L")):
    return False  # already in use

class HotkeyFilter(QAbstractNativeEventFilter):
    def nativeEventFilter(self, event_type, message):
        if event_type == b"windows_generic_MSG":
            ptr = int(message)
            if ptr:
                msg = MSG.from_address(ptr)
                if msg.message == WM_HOTKEY and msg.wParam == self._id:
                    self._callback()
                    return True
        return False
```

- `MOD_NOREPEAT` suppresses auto-repeat spam.
- Unregister on quit (`app.aboutToQuit`) via `UnregisterHotKey(None, id)` and
  `removeNativeEventFilter`.

## Overlay window flags (overlay.py)

```python
self.setWindowFlags(
    Qt.WindowType.FramelessWindowHint
    | Qt.WindowType.WindowStaysOnTopHint
    | Qt.WindowType.WindowTransparentForInput
    | Qt.WindowType.Tool
    | Qt.WindowType.WindowDoesNotAcceptFocus
)
self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
```

- Geometry = union of all screens: `geo = geo.united(screen.geometry())`.
- Listen to `app.screenAdded` / `app.screenRemoved` -> recompute.
- Recompute in `show_laser()` and each `_tick()`; only call `setGeometry`
  when the union actually changed.

## DPI-safe cursor mapping

`GetCursorPos` returns **physical** pixels; widget coordinates are logical.

```python
def _to_local(self, px, py):
    screen = self._app.primaryScreen()
    for s in self._app.screens():
        dpr = s.devicePixelRatio()
        g = s.geometry()
        x0, y0 = g.x() * dpr, g.y() * dpr
        x1, y1 = x0 + g.width() * dpr, y0 + g.height() * dpr
        if x0 <= px < x1 and y0 <= py < y1:
            screen = s
            break
    dpr = screen.devicePixelRatio()
    return px / dpr - self._origin.x(), py / dpr - self._origin.y()
```

## Laser trail (laser.py)

```python
FRAME_TIME = 0.016
# update_pos(x, y, trail_active):
#   append (x, y, now) only when trail_active
#   drop while now - trail[0].t > max_trail * FRAME_TIME
#   drop while len > max_trail
# paint:
#   trail: per segment age = (now - t2) / (max_trail * FRAME_TIME)
#          skip if age >= 1.0; alpha = int(220 * (1-age))
#          width = 1.0 + trail_width * (1-age); round cap/join
#   dot: QRadialGradient radius = glow_radius * (1 + 0.05*sin(now*7))
#        stops: white -> base.lighter(150) -> base@190 -> base@0
#        then small solid white center ellipse
```

## Resource path (frozen vs source)

```python
def resource_path(name):
    if getattr(sys, "frozen", False):
        return os.path.join(getattr(sys, "_MEIPASS", "."), name)
    base = os.path.dirname(os.path.abspath(__file__))
    for rel in (os.path.join("assets", name), name):
        candidate = os.path.join(base, rel)
        if os.path.exists(candidate):
            return candidate
    return os.path.join(base, name)
```

## Single-instance lock (main.py)

```python
directory = QStandardPaths.writableLocation(
    QStandardPaths.StandardLocation.AppLocalDataLocation
)
os.makedirs(directory, exist_ok=True)
lock = QLockFile(os.path.join(directory, "pinlaser.lock"))
lock.setStaleLockTime(0)
if not lock.tryLock(100):
    QMessageBox.information(None, "Pin Laser", "Pin Laser is already running.")
    sys.exit(0)
```

Keep `lock` referenced for the app lifetime; it releases on destruction.

## Settings

```python
DEFAULTS = {
    "trail_on_click": True,
    "trail_button": "left",
    "color": "#ff2a1a",
    "glow_radius": 28.0,
    "trail_length": 40,
}

class AppSettings:
    def __init__(self, store=None):
        self._store = store if store is not None else QSettings("PinLaser", "PinLaser")
        self.trail_on_click = bool(self._store.value("trail_on_click",
                                     DEFAULTS["trail_on_click"], type=bool))
        # ... same pattern for the rest ...
    def save(self):
        self._store.setValue("trail_on_click", self.trail_on_click)
        # ...
        self._store.sync()  # flush buffered writes
```

The `store=None` param makes settings testable with a temp
`QSettings(path, QSettings.Format.IniFormat)`.

## Multi-size ICO writer (make_icon.py)

Load the PNG with `QImage`, scale to sizes `[16,24,32,48,64,128,256]`, encode
each as PNG bytes, then pack the ICO format manually:

```python
header  = struct.pack("<HHH", 0, 1, count)          # reserved, type=1, count
entry   = struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(data), offset)
# dim = size if size < 256 else 0  (0 means 256)
```

Each directory entry embeds a PNG (supported since Windows Vista); offsets
start at `6 + 16 * count`.

## PyInstaller version file (version_info.txt)

```python
VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1, 0, 0, 0), prodvers=(1, 0, 0, 0),
        mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1,
        subtype=0x0, date=(0, 0),
    ),
    kids=[
        StringFileInfo([StringTable(u"040904B0", [
            StringStruct(u"CompanyName", u"kremsotech"),
            StringStruct(u"FileDescription", u"Pin Laser"),
            StringStruct(u"FileVersion", u"1.0.0"),
            StringStruct(u"ProductName", u"Pin Laser"),
            StringStruct(u"ProductVersion", u"1.0.0"),
            StringStruct(u"OriginalFilename", u"PinLaser.exe"),
        ])]),
        VarFileInfo([VarStruct(u"Translation", [1033, 1200])]),
    ],
)
```

`CompanyName` is what Windows shows as **Publisher**.

## PyInstaller build command

```bat
py -m PyInstaller --noconfirm --clean --windowed --onefile --name PinLaser ^
    --icon "%CD%\packaging\pinlaser.ico" ^
    --version-file "%CD%\packaging\version_info.txt" ^
    --add-data "%CD%\assets\app_icon_pin-laser.png;." ^
    --specpath packaging --workpath build --distpath dist ^
    main.py
```

- **Always use absolute `%CD%` paths** -- PyInstaller resolves relative
  `--add-data` paths against the spec directory, not the CWD.
- `--add-data "src;."` puts the file at the `_MEIPASS` root, matching
  `resource_path()` in frozen mode.
- `--windowed` hides the console; `--onefile` produces a single portable exe.

## Smoke test

```bat
set PINLASER_SMOKE=1
py main.py            :: source
dist\PinLaser.exe     :: frozen (auto-quits after ~2 s)
```

Check version metadata:

```powershell
(Get-Item 'dist\PinLaser.exe').VersionInfo
```
