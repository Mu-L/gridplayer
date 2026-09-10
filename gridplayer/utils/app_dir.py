import os
import sys
from pathlib import Path

from PyQt5.QtCore import QStandardPaths

from gridplayer.params import env

PORTABLE_APP_DIR = "portable_data"

ENV_USER_DATA_DIR = "GP_USER_DATA_DIR"


def is_portable() -> bool:
    if not (env.IS_WINDOWS and env.IS_PYINSTALLER):
        return False

    portable_data_dir = Path(sys.executable).parent / PORTABLE_APP_DIR

    return portable_data_dir.is_dir()


def get_user_data_dir_override() -> Path | None:
    value = os.environ.get(ENV_USER_DATA_DIR, "").strip()

    if not value:
        return None

    app_dir = Path(value).expanduser()

    if not app_dir.is_absolute():
        app_dir = Path.cwd() / app_dir

    return app_dir


def get_app_data_dir() -> Path:
    user_data_dir = get_user_data_dir_override()

    if user_data_dir is not None:
        user_data_dir.mkdir(parents=True, exist_ok=True)

        return user_data_dir

    if is_portable():
        return Path(sys.executable).parent / PORTABLE_APP_DIR

    app_dir = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))

    if not app_dir.is_dir():
        app_dir.mkdir(parents=True)

    return app_dir
