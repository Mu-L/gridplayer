import importlib.resources
import os
import platform
import sys
from pathlib import Path

IS_LINUX = platform.system() == "Linux"
IS_MACOS = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"


def _is_kde() -> bool:
    if not IS_LINUX:
        return False

    blob = ":".join(
        (
            os.environ.get("XDG_CURRENT_DESKTOP", ""),
            os.environ.get("DESKTOP_SESSION", ""),
            os.environ.get("XDG_SESSION_DESKTOP", ""),
        )
    ).lower()
    return "kde" in blob or "plasma" in blob


IS_PYINSTALLER = getattr(sys, "frozen", False)
IS_SNAP = IS_LINUX and "SNAP" in os.environ
IS_APPIMAGE = IS_LINUX and "APPIMAGE" in os.environ
IS_FLATPAK = IS_LINUX and "FLATPAK_ID" in os.environ
IS_KDE = _is_kde()

PYINSTALLER_LIB_ROOT = Path(sys._MEIPASS) if IS_PYINSTALLER else Path.cwd()


def _resolve_resources_dir() -> Path:
    # When frozen, resources are collected as data files under sys._MEIPASS;
    # importlib.resources is unreliable there because the package lives in the
    # PYZ archive.
    if IS_PYINSTALLER:
        return PYINSTALLER_LIB_ROOT / "gridplayer" / "resources"
    return Path(str(importlib.resources.files("gridplayer") / "resources"))


RESOURCES_DIR = _resolve_resources_dir()


VLC_VERSION = None
VLC_PYTHON_VERSION = None

if IS_FLATPAK:
    FLATPAK_RUNTIME_DIR = (
        Path(os.environ["XDG_RUNTIME_DIR"])
        / "app"
        / os.environ["FLATPAK_ID"]
        / "gridplayer"
    )
    FLATPAK_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
else:
    FLATPAK_RUNTIME_DIR = None
