import ctypes
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter

from win_utils import MSG

WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000

_user32 = ctypes.windll.user32
_user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_uint, ctypes.c_uint]
_user32.RegisterHotKey.restype = wintypes.BOOL
_user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
_user32.UnregisterHotKey.restype = wintypes.BOOL


class HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, hotkey_id, callback):
        super().__init__()
        self._id = hotkey_id
        self._callback = callback

    def nativeEventFilter(self, event_type, message):
        if event_type == b"windows_generic_MSG":
            try:
                ptr = int(message)
            except (TypeError, ValueError):
                return False
            if ptr:
                msg = MSG.from_address(ptr)
                if msg.message == WM_HOTKEY and msg.wParam == self._id:
                    self._callback()
                    return True
        return False


class HotkeyManager:
    DEFAULT_MODS = MOD_CONTROL | MOD_SHIFT
    DEFAULT_VK = ord("L")

    def __init__(self, app, mods=DEFAULT_MODS, vk=DEFAULT_VK):
        self._app = app
        self._id = 0x4C4C
        self._mods = mods
        self._vk = vk
        self._filter = None
        self._registered = False

    @property
    def registered(self):
        return self._registered

    def register(self, callback):
        if not _user32.RegisterHotKey(None, self._id, self._mods | MOD_NOREPEAT, self._vk):
            return False
        self._filter = HotkeyFilter(self._id, callback)
        self._app.installNativeEventFilter(self._filter)
        self._registered = True
        return True

    def unregister(self):
        if not self._registered:
            return
        _user32.UnregisterHotKey(None, self._id)
        if self._filter is not None:
            self._app.removeNativeEventFilter(self._filter)
            self._filter = None
        self._registered = False
