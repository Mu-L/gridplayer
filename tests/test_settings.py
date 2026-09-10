from PyQt5.QtCore import QSettings

from gridplayer.params.static import (
    UnsavedChangesMode,
    VideoEndAction,
    VideoInitialState,
)
from gridplayer.settings import _Settings


def _make_settings(tmp_path, values):
    ini_path = tmp_path / "settings.ini"

    writer = QSettings(str(ini_path), QSettings.IniFormat)
    for key, value in values.items():
        writer.setValue(key, value)
    writer.sync()

    settings = _Settings.__new__(_Settings)
    settings.settings = QSettings(str(ini_path), QSettings.IniFormat)
    return settings


def test_migrate_track_changes_true_to_ask(tmp_path):
    settings = _make_settings(tmp_path, {"playlist/track_changes": True})

    settings._migrate_track_changes_flag()

    assert not settings.settings.contains("playlist/track_changes")
    assert settings.settings.value("playlist/unsaved_changes") == "ask"


def test_migrate_track_changes_false_to_discard(tmp_path):
    settings = _make_settings(tmp_path, {"playlist/track_changes": False})

    settings._migrate_track_changes_flag()

    assert not settings.settings.contains("playlist/track_changes")
    assert settings.settings.value("playlist/unsaved_changes") == "discard"


def test_migrate_track_changes_keeps_existing_mode(tmp_path):
    settings = _make_settings(
        tmp_path,
        {
            "playlist/track_changes": True,
            "playlist/unsaved_changes": UnsavedChangesMode.DISCARD.value,
        },
    )

    settings._migrate_track_changes_flag()

    assert not settings.settings.contains("playlist/track_changes")
    assert settings.settings.value("playlist/unsaved_changes") == "discard"


def test_migrate_track_changes_noop_without_legacy_key(tmp_path):
    settings = _make_settings(tmp_path, {"player/language": "en_US"})

    settings._migrate_track_changes_flag()

    assert not settings.settings.contains("playlist/unsaved_changes")
    assert settings.settings.value("player/language") == "en_US"


def test_migrate_paused_true_to_paused_state(tmp_path):
    settings = _make_settings(tmp_path, {"video_defaults/paused": True})

    settings._migrate_paused_to_initial_state()

    assert not settings.settings.contains("video_defaults/paused")
    assert settings.settings.value("video_defaults/initial_state") == "paused"


def test_migrate_paused_false_to_playing_state(tmp_path):
    settings = _make_settings(tmp_path, {"video_defaults/paused": False})

    settings._migrate_paused_to_initial_state()

    assert not settings.settings.contains("video_defaults/paused")
    assert settings.settings.value("video_defaults/initial_state") == "playing"


def test_migrate_paused_keeps_existing_initial_state(tmp_path):
    settings = _make_settings(
        tmp_path,
        {
            "video_defaults/paused": True,
            "video_defaults/initial_state": VideoInitialState.STOPPED.value,
        },
    )

    settings._migrate_paused_to_initial_state()

    assert not settings.settings.contains("video_defaults/paused")
    assert settings.settings.value("video_defaults/initial_state") == "stopped"


def test_migrate_repeat_key_and_value(tmp_path):
    settings = _make_settings(tmp_path, {"video_defaults/repeat": "none"})

    settings._migrate_repeat_to_end_action()

    assert not settings.settings.contains("video_defaults/repeat")
    assert settings.settings.value("video_defaults/end_action") == "stop"


def test_migrate_repeat_single_file_to_loop_file(tmp_path):
    settings = _make_settings(tmp_path, {"video_defaults/repeat": "single_file"})

    settings._migrate_repeat_to_end_action()

    assert settings.settings.value("video_defaults/end_action") == "loop_file"


def test_migrate_repeat_keeps_existing_end_action(tmp_path):
    settings = _make_settings(
        tmp_path,
        {
            "video_defaults/repeat": "none",
            "video_defaults/end_action": VideoEndAction.PAUSE.value,
        },
    )

    settings._migrate_repeat_to_end_action()

    assert not settings.settings.contains("video_defaults/repeat")
    assert settings.settings.value("video_defaults/end_action") == "pause"


def test_migrate_repeat_remaps_legacy_value_on_new_key(tmp_path):
    settings = _make_settings(tmp_path, {"video_defaults/end_action": "dir"})

    settings._migrate_repeat_to_end_action()

    assert settings.settings.value("video_defaults/end_action") == "next_file"


def test_migrate_paused_noop_without_legacy_key(tmp_path):
    settings = _make_settings(tmp_path, {"player/language": "en_US"})

    settings._migrate_paused_to_initial_state()

    assert not settings.settings.contains("video_defaults/initial_state")
    assert settings.settings.value("player/language") == "en_US"
