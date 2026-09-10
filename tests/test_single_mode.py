from types import SimpleNamespace

import pytest
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

from gridplayer.player.managers.single_mode import SingleModeManager
from gridplayer.settings import Settings


@pytest.fixture(scope="module", autouse=True)
def _qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def _isolated_settings(tmp_path):
    settings = Settings()
    settings.settings = QSettings(str(tmp_path / "test.ini"), QSettings.IniFormat)


def _block(mocker, *, block_id, is_paused, is_stopped=False):
    vb = mocker.Mock()
    vb.id = block_id
    vb.video_params.is_paused = is_paused
    vb.is_stopped = is_stopped
    return vb


def _manager(mocker, blocks, active, pause_background=True):
    ctx = SimpleNamespace(
        is_single_mode=False,
        is_pause_background_videos=pause_background,
        active_block=active,
        video_blocks=blocks,
        commands=SimpleNamespace(grid_cell_count=lambda: len(blocks)),
    )
    manager = SingleModeManager(context=ctx)
    manager._ctx.is_pause_background_videos = pause_background
    return manager


def test_single_mode_pauses_only_playing_background(mocker):
    active = _block(mocker, block_id="a", is_paused=False)
    playing = _block(mocker, block_id="b", is_paused=False)
    paused = _block(mocker, block_id="c", is_paused=True)
    stopped = _block(mocker, block_id="d", is_paused=True, is_stopped=True)
    manager = _manager(mocker, [active, playing, paused, stopped], active)

    manager.single_mode_on()

    playing.set_pause.assert_called_once_with(True)
    paused.set_pause.assert_not_called()
    stopped.set_pause.assert_not_called()
    stopped.stop_playback.assert_not_called()
    playing.hide.assert_called_once()
    paused.hide.assert_called_once()
    stopped.hide.assert_called_once()


def test_single_mode_off_resumes_only_paused_playing(mocker):
    active = _block(mocker, block_id="a", is_paused=False)
    playing = _block(mocker, block_id="b", is_paused=False)
    stopped = _block(mocker, block_id="d", is_paused=True, is_stopped=True)
    manager = _manager(mocker, [active, playing, stopped], active)
    manager.single_mode_on()
    playing.set_pause.reset_mock()

    manager.single_mode_off()

    playing.set_pause.assert_called_once_with(False)
    stopped.set_pause.assert_not_called()
    stopped.stop_playback.assert_not_called()


def test_single_mode_does_not_pause_when_setting_off(mocker):
    active = _block(mocker, block_id="a", is_paused=False)
    playing = _block(mocker, block_id="b", is_paused=False)
    manager = _manager(mocker, [active, playing], active, pause_background=False)

    manager.single_mode_on()

    playing.set_pause.assert_not_called()
    playing.hide.assert_called_once()
