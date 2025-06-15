import importlib
import sys
import ctypes
import pytest

import aw_watcher_virtualdesktop.platform as platform_mod


def reload_for_platform(monkeypatch, plat, mods=None):
    monkeypatch.setattr(sys, 'platform', plat, raising=False)
    if mods:
        for name, mod in mods.items():
            monkeypatch.setitem(sys.modules, name, mod)
    importlib.reload(platform_mod)


@pytest.mark.skipif(getattr(ctypes, 'WINFUNCTYPE', None) is None, reason='non-windows')
def test_get_virtual_desktop_windows(monkeypatch):
    class FakeGUID:
        def __init__(self, *args, **kwargs):
            self.value = ''

    class FakeMgr:
        def GetWindowDesktopId(self, hwnd, guid_ptr):
            guid_ptr.value = 'abc'
            return 0

    fake_mod = importlib.import_module('types')
    fake_mod.GUID = FakeGUID
    fake_mod.CoInitialize = lambda: None
    fake_mod.CoCreateInstance = lambda clsid, interface=None: FakeMgr()
    fake_mod.IUnknown = object
    reload_for_platform(monkeypatch, 'win32', {'comtypes': fake_mod})
    class Dummy:
        def GetWindowDesktopId(self, hwnd, guid_ptr):
            guid_ptr.value = 'abc'
            return 0
    monkeypatch.setattr(platform_mod, 'IVirtualDesktopManager', Dummy, raising=False)
    monkeypatch.setattr(platform_mod, 'CLSID_VirtualDesktopManager', FakeGUID, raising=False)
    monkeypatch.setitem(sys.modules, 'aw_watcher_virtualdesktop.windows', type('M', (), {'get_active_window_handle': lambda: 1}))
    assert platform_mod.get_virtual_desktop() == 'abc'


def test_get_virtual_desktop_x11(monkeypatch):
    reload_for_platform(monkeypatch, 'linux')
    monkeypatch.setenv('XDG_SESSION_TYPE', 'x11')
    monkeypatch.setattr(platform_mod, '_get_current_desktop_x11', lambda: 1, raising=False)
    assert platform_mod.get_virtual_desktop() == 1


def test_get_virtual_desktop_gnome(monkeypatch):
    reload_for_platform(monkeypatch, 'linux')
    monkeypatch.setenv('XDG_SESSION_TYPE', 'wayland')
    monkeypatch.setenv('XDG_CURRENT_DESKTOP', 'GNOME')
    monkeypatch.setattr(platform_mod, '_get_current_desktop_gnome', lambda: 3, raising=False)
    assert platform_mod.get_virtual_desktop() == 3
