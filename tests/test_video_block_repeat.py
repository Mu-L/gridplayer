from pathlib import Path

import pytest
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

from gridplayer.models.video import Video
from gridplayer.params.static import VideoEndAction, VideoInitialState
from gridplayer.settings import Settings
from gridplayer.widgets.video_block import VideoBlock


@pytest.fixture(scope="module", autouse=True)
def _qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def _isolated_settings(tmp_path):
    settings = Settings()
    settings.settings = QSettings(str(tmp_path / "test.ini"), QSettings.IniFormat)


def _block(mocker, **video_kwargs):
    block = mocker.Mock()
    block.video_params = Video(uri="http://example.com/a.mp4", **video_kwargs)
    return block


def test_loop_end_stop_without_explicit_loop(mocker):
    block = _block(mocker, end_action=VideoEndAction.STOP, loop_end=None)

    VideoBlock.loop_end_action(block)

    block.stop_playback.assert_called_once()
    block._loop_to_start.assert_not_called()
    block.next_video.assert_not_called()


def test_loop_end_close_schedules_close(mocker):
    block = _block(mocker, end_action=VideoEndAction.CLOSE, loop_end=None)
    single_shot = mocker.patch("gridplayer.widgets.video_block.QTimer.singleShot")

    VideoBlock.loop_end_action(block)

    single_shot.assert_called_once_with(0, block.close)
    block.stop_playback.assert_not_called()
    block._loop_to_start.assert_not_called()


def test_loop_end_loop_file_still_loops(mocker):
    block = _block(mocker, end_action=VideoEndAction.LOOP_FILE, loop_end=None)

    VideoBlock.loop_end_action(block)

    block._loop_to_start.assert_called_once()
    block.stop_playback.assert_not_called()


def test_loop_end_next_file(mocker):
    block = _block(mocker, end_action=VideoEndAction.NEXT_FILE, loop_end=None)

    VideoBlock.loop_end_action(block)

    block.next_video.assert_called_once()
    block._loop_to_start.assert_not_called()


def test_loop_end_previous_file(mocker):
    block = _block(mocker, end_action=VideoEndAction.PREVIOUS_FILE, loop_end=None)

    VideoBlock.loop_end_action(block)

    block.previous_video.assert_called_once()
    block.next_video.assert_not_called()


def test_loop_end_shuffle_file(mocker):
    block = _block(mocker, end_action=VideoEndAction.SHUFFLE_FILE, loop_end=None)

    VideoBlock.loop_end_action(block)

    block.shuffle_video.assert_called_once()


def test_loop_end_pause_at_start(mocker):
    block = _block(mocker, end_action=VideoEndAction.PAUSE, loop_end=None)

    VideoBlock.loop_end_action(block)

    block._pause_at_start.assert_called_once()
    block.stop_playback.assert_not_called()
    block._destroy_video_driver.assert_not_called()


def test_pause_at_start_seeks_and_pauses(mocker):
    block = mocker.Mock()
    block.loop_start = 0

    VideoBlock._pause_at_start(block)

    block.seek.assert_called_once_with(0)
    block.set_pause.assert_called_once_with(True)
    block.stop_playback.assert_not_called()
    block._destroy_video_driver.assert_not_called()


def test_loop_end_stop_with_segment_still_loops(mocker):
    block = _block(mocker, end_action=VideoEndAction.STOP, loop_end=5000)

    VideoBlock.loop_end_action(block)

    block._loop_to_start.assert_called_once()
    block.stop_playback.assert_not_called()
    block.close.assert_not_called()


def test_loop_start_without_end_loops_when_stop(mocker):
    block = _block(
        mocker, end_action=VideoEndAction.STOP, loop_start=1500, loop_end=None
    )

    VideoBlock.loop_end_action(block)

    block._loop_to_start.assert_called_once()
    block.stop_playback.assert_not_called()
    block.close.assert_not_called()


def test_loop_start_without_end_loops_when_close(mocker):
    block = _block(
        mocker, end_action=VideoEndAction.CLOSE, loop_start=1500, loop_end=None
    )
    single_shot = mocker.patch("gridplayer.widgets.video_block.QTimer.singleShot")

    VideoBlock.loop_end_action(block)

    block._loop_to_start.assert_called_once()
    single_shot.assert_not_called()
    block.stop_playback.assert_not_called()


def test_stopped_overlay_uses_hide_timer(mocker):
    block = mocker.Mock()
    block._ctx.is_drag_ui = False
    block._ctx.is_disable_overlay = False
    block._ctx.is_overlay_hide_on_timeout = True
    block._ctx.overlay_timeout = 3
    block.is_stopped = True
    block.is_loading = False
    block._is_error = False
    block.isVisible.return_value = True

    VideoBlock.show_overlay(block)

    block.overlay.show.assert_called_once()
    block.overlay_hide_timer.start.assert_called_once_with(3000)

    VideoBlock.hide_overlay(block)

    block.overlay.hide.assert_called_once()


def test_stop_playback_destroys_driver(mocker):
    block = mocker.Mock()
    block.video_params = Video(uri="http://example.com/a.mp4")

    VideoBlock.stop_playback(block)

    block._set_playback_state.assert_called_once_with(VideoInitialState.STOPPED)
    block._destroy_video_driver.assert_called_once()
    block.video_status.hide.assert_called_once()
    block.show_overlay.assert_called()


def test_stop_playback_resets_position_and_segment_loop(mocker):
    block = mocker.Mock()
    block.video_params = Video(
        uri="http://example.com/a.mp4",
        current_position=12345,
        loop_start=1000,
        loop_end=5000,
        is_paused=False,
    )

    VideoBlock.stop_playback(block)

    assert block.video_params.current_position == 0
    assert block.video_params.loop_start is None
    assert block.video_params.loop_end is None
    block.loop_start_change.emit.assert_called_with(0)
    block.loop_end_change.emit.assert_called_with(100.0)


def test_set_playback_state_syncs_overlay_when_already_playing(mocker):
    block = _block(mocker, playback_state=VideoInitialState.PLAYING)

    VideoBlock._set_playback_state(block, VideoInitialState.PLAYING)

    block.is_paused_change.emit.assert_called_once_with(False)
    block.is_stopped_change.emit.assert_not_called()
    block.show_overlay.assert_not_called()


def test_set_playback_state_syncs_overlay_when_already_stopped(mocker):
    block = _block(mocker, playback_state=VideoInitialState.STOPPED)

    VideoBlock._set_playback_state(block, VideoInitialState.STOPPED)

    block.is_paused_change.emit.assert_called_once_with(True)
    block.is_stopped_change.emit.assert_called_once_with(True)
    block.show_overlay.assert_called_once()


def test_set_video_stopped_defers_load(mocker):
    block = mocker.Mock()
    block.video_params = None
    block.is_video_initialized = False
    video = Video(uri="http://example.com/a.mp4", is_paused=True, is_stopped=True)

    VideoBlock.set_video(block, video)

    assert block.video_params is video
    block._present_stopped.assert_called_once()
    block._start_load.assert_not_called()
    block.reset.assert_not_called()


def test_apply_snapshot_stopped_destroys_driver(mocker):
    block = mocker.Mock()
    snapshot = Video(uri="http://example.com/a.mp4", is_paused=True, is_stopped=True)
    block.video_params = Video(uri=snapshot.uri, is_paused=False, is_stopped=False)
    block._default_title = "a.mp4"

    VideoBlock.apply_snapshot(block, snapshot)

    assert block.video_params.is_stopped is True
    block._destroy_video_driver.assert_called_once()
    block._present_stopped.assert_called_once()
    block._start_load.assert_not_called()


def test_apply_snapshot_playing_on_stopped_starts_load(mocker):
    block = mocker.Mock()
    snapshot = Video(uri="http://example.com/a.mp4", is_paused=False, is_stopped=False)
    block.video_params = Video(uri=snapshot.uri, is_paused=True, is_stopped=True)
    block.is_video_initialized = False
    block._default_title = "a.mp4"

    VideoBlock.apply_snapshot(block, snapshot)

    assert block.video_params.is_stopped is False
    block._start_load.assert_called_once()
    block._present_stopped.assert_not_called()
    block._destroy_video_driver.assert_not_called()


def test_set_video_playing_starts_load(mocker):
    block = mocker.Mock()
    block.video_params = None
    block.is_video_initialized = False
    video = Video(uri="http://example.com/a.mp4", is_paused=False, is_stopped=False)

    VideoBlock.set_video(block, video)

    block._present_stopped.assert_not_called()
    block._start_load.assert_called_once()


def test_set_pause_uninitialized_stopped_loads(mocker):
    block = mocker.Mock()
    block._is_state_change_in_progress = False
    block.is_video_initialized = False
    block.video_params = mocker.Mock()

    VideoBlock.set_pause(block, False)

    block._load_and_play.assert_called_once()
    block.video_driver.play.assert_not_called()
    block.video_driver.set_pause.assert_not_called()


def test_set_pause_uninitialized_pause_is_noop(mocker):
    block = mocker.Mock()
    block._is_state_change_in_progress = False
    block.is_video_initialized = False
    block.video_params = mocker.Mock()

    VideoBlock.set_pause(block, True)

    block._load_and_play.assert_not_called()
    block.video_driver.set_pause.assert_not_called()


def test_switch_video_stopped_same_file_loads(mocker):
    uri = Path("/tmp/a.mp4")
    block = mocker.Mock()
    block.is_local_file = True
    block.video_params = mocker.Mock(uri=uri)
    block.is_video_initialized = False

    VideoBlock.switch_video(block, uri)

    block._load_and_play.assert_called_once()
    block.seek.assert_not_called()
    block.set_video.assert_not_called()


def test_switch_video_initialized_same_file_seeks(mocker):
    uri = Path("/tmp/a.mp4")
    block = mocker.Mock()
    block.is_local_file = True
    block.video_params = mocker.Mock(uri=uri)
    block.is_video_initialized = True
    block.loop_start = 0

    VideoBlock.switch_video(block, uri)

    block.seek.assert_called_once_with(0)
    block._load_and_play.assert_not_called()


def test_switch_video_stopped_other_file_starts_playback(mocker):
    block = mocker.Mock()
    block.is_local_file = True
    block.video_params = mocker.Mock(uri=Path("/tmp/a.mp4"))
    block.is_video_initialized = False

    VideoBlock.switch_video(block, Path("/tmp/b.mp4"))

    assert block.video_params.uri == Path("/tmp/b.mp4")
    assert block.video_params.playback_state is VideoInitialState.PLAYING
    block.set_video.assert_called_once_with(block.video_params)
