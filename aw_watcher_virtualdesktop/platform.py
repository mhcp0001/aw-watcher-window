import os
import sys
import subprocess
from typing import Optional


if sys.platform.startswith("win"):
    import ctypes
    try:
        import comtypes
        from ctypes import wintypes
        from comtypes import GUID, COMMETHOD, HRESULT

        try:
            class IVirtualDesktopManager(comtypes.IUnknown):
                _iid_ = GUID("{A5CD92FF-29BE-454C-8D04-D82879FB3F1B}")
                _methods_ = [
                    COMMETHOD([], HRESULT, "IsWindowOnCurrentVirtualDesktop",
                              (["in"], wintypes.HWND, "hwnd"),
                              (["out"], ctypes.POINTER(ctypes.c_bool), "onCurrentDesktop")),
                    COMMETHOD([], HRESULT, "GetWindowDesktopId",
                              (["in"], wintypes.HWND, "hwnd"),
                              (["out"], ctypes.POINTER(GUID), "desktopId")),
                    COMMETHOD([], HRESULT, "MoveWindowToDesktop",
                              (["in"], wintypes.HWND, "hwnd"),
                              (["in"], ctypes.POINTER(GUID), "desktopId")),
                ]

            CLSID_VirtualDesktopManager = GUID("{AA509086-5CA9-4C25-8F95-589D3C07B48A}")
        except Exception:
            # comtypes might be a stub without ctypes integration (as in tests)
            class IVirtualDesktopManager:  # type: ignore
                pass

            CLSID_VirtualDesktopManager = GUID("{AA509086-5CA9-4C25-8F95-589D3C07B48A}")
    except Exception:  # pragma: no cover - used on non-windows platforms
        comtypes = None  # type: ignore
        IVirtualDesktopManager = object  # type: ignore
        CLSID_VirtualDesktopManager = None


    def get_virtual_desktop() -> Optional[str]:
        from .windows import get_active_window_handle
        if comtypes is None:
            return None

        comtypes.CoInitialize()
        manager = comtypes.CoCreateInstance(
            CLSID_VirtualDesktopManager, interface=IVirtualDesktopManager
        )
        desktop_id = comtypes.GUID()
        hwnd = get_active_window_handle()
        res = manager.GetWindowDesktopId(hwnd, ctypes.byref(desktop_id))
        if res != 0:
            return None
        return str(desktop_id)

elif sys.platform == "darwin":
    import ctypes

    CGSGetActiveSpace = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics").CGSGetActiveSpace
    CGSGetActiveSpace.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint64)]

    def get_virtual_desktop() -> Optional[int]:
        space = ctypes.c_uint64()
        # 0 for default connection
        CGSGetActiveSpace(0, ctypes.byref(space))
        return int(space.value)

else:
    def _get_current_desktop_x11() -> Optional[int]:
        try:
            from Xlib import X, display as xdisplay
        except Exception:
            return None
        disp = xdisplay.Display()
        root = disp.screen().root
        NET_CURRENT_DESKTOP = disp.intern_atom("_NET_CURRENT_DESKTOP")
        prop = root.get_full_property(NET_CURRENT_DESKTOP, X.AnyPropertyType)
        if prop:
            return int(prop.value[0])
        return None

    def _get_current_desktop_gnome() -> Optional[int]:
        try:
            out = subprocess.check_output([
                "gdbus",
                "call",
                "--session",
                "--dest",
                "org.gnome.Shell",
                "--object-path",
                "/org/gnome/Shell",
                "--method",
                "org.gnome.Shell.Eval",
                "global.workspace_manager.get_active_workspace_index()",
            ], text=True)
            val = out.split()[0].strip("(),")
            return int(val)
        except Exception:
            return None

    def _get_current_desktop_kde() -> Optional[int]:
        try:
            out = subprocess.check_output([
                "qdbus",
                "org.kde.KWin",
                "/KWin",
                "currentDesktop",
            ], text=True)
            return int(out.strip())
        except Exception:
            return None

    def get_virtual_desktop() -> Optional[int]:
        if os.environ.get("XDG_SESSION_TYPE") == "x11":
            return _get_current_desktop_x11()
        session = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if session.startswith("gnome"):
            return _get_current_desktop_gnome()
        if session.startswith("kde"):
            return _get_current_desktop_kde()
        # fallback to x11 property
        return _get_current_desktop_x11()

__all__ = ["get_virtual_desktop"]
