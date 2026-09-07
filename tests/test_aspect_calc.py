import pytest

from gridplayer.params.static import VideoAspect, VideoCrop
from gridplayer.utils.aspect_calc import (
    calc_crop_region,
    calc_resize_scale,
    calc_view_geometry,
)

VIDEO = (1920, 1080)
PANE = (1600, 900)


class TestLegacyGeometry:
    """Without a pixel crop the ratio-form geometry is unchanged."""

    @pytest.mark.parametrize(
        ("aspect", "expected"),
        [
            (VideoAspect.FIT, ("1920:1080", "1600:900")),
            (VideoAspect.STRETCH, ("1600:900", "1600:900")),
            (VideoAspect.NONE, ("1920:1080", "1920:1080")),
        ],
    )
    def test_no_crop(self, aspect, expected):
        assert (
            calc_view_geometry(VIDEO, PANE, aspect, VideoCrop(0, 0, 0, 0)) == expected
        )


class TestViewGeometryWithCrop:
    def test_none_letterboxes_user_region(self):
        crop = VideoCrop(100, 50, 40, 30)

        assert calc_view_geometry(VIDEO, PANE, VideoAspect.NONE, crop) == (
            "1920:1080",
            "+100+50+40+30",
        )

    def test_fit_extends_borders_when_region_taller_than_pane(self):
        # Region 960x1080 (8:9) in a 16:9 pane -> crop 270 top/bottom.
        crop = VideoCrop(480, 0, 480, 0)

        assert calc_view_geometry(VIDEO, PANE, VideoAspect.FIT, crop) == (
            "1920:1080",
            "+480+270+480+270",
        )

    def test_fit_extends_borders_when_region_wider_than_pane(self):
        # Region 1920x540 (32:9) in a 16:9 pane -> crop 480 left/right.
        crop = VideoCrop(0, 270, 0, 270)

        assert calc_view_geometry(VIDEO, PANE, VideoAspect.FIT, crop) == (
            "1920:1080",
            "+480+270+480+270",
        )

    def test_fit_borders_round_to_nearest_pixel(self):
        # Region 959x1080 -> target height 539.4375 -> extra rounds to 270.
        crop = VideoCrop(481, 0, 480, 0)

        assert calc_view_geometry(VIDEO, PANE, VideoAspect.FIT, crop) == (
            "1920:1080",
            "+481+270+480+270",
        )

    def test_fit_leaves_matching_region_unchanged(self):
        # Region 1600x900 already matches the 16:9 pane; no extra borders.
        crop = VideoCrop(160, 90, 160, 90)

        assert calc_view_geometry(VIDEO, PANE, VideoAspect.FIT, crop) == (
            "1920:1080",
            "+160+90+160+90",
        )

    def test_fit_does_not_zero_out_tiny_region(self):
        # 4x1 region in a 1x10000 pane: unclamped extra would wipe the region.
        crop = VideoCrop(958, 1079, 958, 0)

        assert calc_view_geometry(VIDEO, (1, 10000), VideoAspect.FIT, crop) == (
            "1920:1080",
            "+959+1079+959+0",
        )

    def test_stretch_compensates_override_for_cropped_region(self):
        # Region 960x1080 must display as 16:9; VLC derives the SAR from the
        # pre-crop dims, so the override is compensated to 32:9.
        crop = VideoCrop(480, 0, 480, 0)

        assert calc_view_geometry(VIDEO, PANE, VideoAspect.STRETCH, crop) == (
            "32:9",
            "+480+0+480+0",
        )

    def test_stretch_without_crop_reduces_to_pane_ratio(self):
        crop = VideoCrop(0, 0, 0, 0)

        assert calc_view_geometry(VIDEO, PANE, VideoAspect.STRETCH, crop) == (
            "1600:900",
            "1600:900",
        )

    def test_stretch_compensates_vertical_crop(self):
        # Region 1920x540 must display as 16:9 -> override 8:9.
        crop = VideoCrop(0, 270, 0, 270)

        assert calc_view_geometry(VIDEO, PANE, VideoAspect.STRETCH, crop) == (
            "8:9",
            "+0+270+0+270",
        )

    def test_stretch_tiny_override_stays_in_vlc_sar_range(self):
        # Inverse of the degenerate huge-ratio case: 1x1 region in a 1px-wide
        # huge pane. The reduced fraction must still fit VLC's uint32 SAR math.
        crop = VideoCrop(1919, 1079, 0, 0)

        override, geo = calc_view_geometry(
            VIDEO, (1, 600000), VideoAspect.STRETCH, crop
        )
        num, den = (int(part) for part in override.split(":"))

        assert geo == "+1919+1079+0+0"
        assert 0 < num <= (1 << 19) - 1
        assert 0 < den <= (1 << 19) - 1

    def test_stretch_degenerate_override_falls_back_to_native(self):
        # 1x1 region in a 1px-tall huge pane -> absurd ratio -> "0:0" resets
        # the override in VLC (letterbox) instead of overflowing its SAR math.
        crop = VideoCrop(1919, 1079, 0, 0)

        assert calc_view_geometry(VIDEO, (600000, 1), VideoAspect.STRETCH, crop) == (
            "0:0",
            "+1919+1079+0+0",
        )

    def test_zero_pane_size_falls_back_to_letterbox(self):
        crop = VideoCrop(10, 10, 10, 10)

        assert calc_view_geometry(VIDEO, (0, 900), VideoAspect.FIT, crop) == (
            "1920:1080",
            "+10+10+10+10",
        )

    def test_zero_video_size_falls_back_to_letterbox(self):
        crop = VideoCrop(10, 10, 10, 10)

        assert calc_view_geometry((0, 0), PANE, VideoAspect.FIT, crop) == (
            "0:0",
            "+10+10+10+10",
        )


class TestCropRegion:
    @pytest.mark.parametrize(
        ("crop", "expected"),
        [
            (VideoCrop(480, 0, 480, 0), (480, 0, 960, 1080)),
            (VideoCrop(2000, 0, 0, 0), (1919, 0, 1, 1080)),
            (VideoCrop(0, 0, 3000, 3000), (0, 0, 1, 1)),
            (VideoCrop(2000, 2000, 2000, 2000), (1919, 1079, 1, 1)),
        ],
    )
    def test_clamped_to_video_bounds(self, crop, expected):
        assert calc_crop_region(VIDEO, crop) == expected


class TestResizeScale:
    @pytest.mark.parametrize("aspect", list(VideoAspect))
    def test_no_zoom(self, aspect):
        assert calc_resize_scale(VIDEO, PANE, aspect, 1.0, VideoCrop(0, 0, 0, 0)) == 0

    def test_fit_zoom_is_fill_ratio(self):
        scale = calc_resize_scale(VIDEO, (1600, 1080), VideoAspect.FIT, 2.0)

        assert scale == pytest.approx(max(1600 / 1920, 1080 / 1080) * 2)

    def test_none_zoom_is_fit_ratio(self):
        scale = calc_resize_scale(VIDEO, (1600, 1080), VideoAspect.NONE, 2.0)

        assert scale == pytest.approx(min(1600 / 1920, 1080 / 1080) * 2)

    def test_fit_with_crop_uses_extended_region(self):
        # Final region 960x540 == pane ratio -> fill ratio == 5/3.
        scale = calc_resize_scale(
            VIDEO, PANE, VideoAspect.FIT, 2.0, VideoCrop(480, 0, 480, 0)
        )

        assert scale == pytest.approx(10 / 3)

    def test_none_with_crop_uses_user_region(self):
        scale = calc_resize_scale(
            VIDEO, PANE, VideoAspect.NONE, 2.0, VideoCrop(480, 0, 480, 0)
        )

        assert scale == pytest.approx(5 / 3)

    def test_degenerate_crop_region_clamps(self):
        scale = calc_resize_scale(
            VIDEO, PANE, VideoAspect.NONE, 2.0, VideoCrop(1919, 1079, 0, 0)
        )

        assert scale == pytest.approx(min(1600 / 1, 900 / 1) * 2)

    def test_zero_pane_size(self):
        assert (
            calc_resize_scale(
                VIDEO, (0, 0), VideoAspect.FIT, 2.0, VideoCrop(0, 0, 0, 0)
            )
            == 0
        )
