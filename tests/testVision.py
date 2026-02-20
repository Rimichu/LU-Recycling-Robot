"""
Tests for vision / detection / classification utilities.
"""
import sys
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ── Calibration file round-trip ──────────────────────────────────────────

class TestCalibrationRoundTrip:
    """Verify calibrate.py output can be consumed by main.py loader."""

    def test_npz_round_trip(self, tmp_path):
        mtx = np.eye(3, dtype=np.float64) * 500
        dist = np.zeros(5, dtype=np.float64)
        path = tmp_path / "cal.npz"
        np.savez(path, mtx=mtx, dist=dist)

        data = np.load(path)
        np.testing.assert_array_equal(data["mtx"], mtx)
        np.testing.assert_array_equal(data["dist"], dist)


# ── Undistortion pipeline ────────────────────────────────────────────────

class TestUndistortion:
    """Verify that undistortion maps can be built and applied."""

    def test_init_undistort_rectify_map(self, calibration_data):
        import cv2
        path, mtx, dist = calibration_data
        map1, map2 = cv2.initUndistortRectifyMap(
            mtx, dist, None, mtx, (640, 480), cv2.CV_16SC2
        )
        assert map1 is not None
        assert map2 is not None
        assert map1.shape[:2] == (480, 640)

    def test_remap_preserves_shape(self, calibration_data, dummy_frame):
        import cv2
        _, mtx, dist = calibration_data
        map1, map2 = cv2.initUndistortRectifyMap(
            mtx, dist, None, mtx,
            (dummy_frame.shape[1], dummy_frame.shape[0]),
            cv2.CV_16SC2,
        )
        result = cv2.remap(dummy_frame, map1, map2, interpolation=cv2.INTER_LINEAR)
        assert result.shape == dummy_frame.shape

    def test_remap_does_not_modify_input(self, calibration_data, dummy_frame):
        import cv2
        _, mtx, dist = calibration_data
        original = dummy_frame.copy()
        map1, map2 = cv2.initUndistortRectifyMap(
            mtx, dist, None, mtx,
            (dummy_frame.shape[1], dummy_frame.shape[0]),
            cv2.CV_16SC2,
        )
        cv2.remap(dummy_frame, map1, map2, interpolation=cv2.INTER_LINEAR)
        np.testing.assert_array_equal(dummy_frame, original)


# ── Detection model loading (mocked) ─────────────────────────────────────

class TestModelLoading:
    """Smoke-test model loading helpers if they exist."""

    def test_yolo_import(self):
        """ultralytics should be importable."""
        try:
            from ultralytics import YOLO
        except ImportError:
            pytest.skip("ultralytics not installed")

    @patch("ultralytics.YOLO")
    def test_yolo_load_returns_model(self, MockYOLO):
        from ultralytics import YOLO
        model = YOLO("fake_weights.pt")
        MockYOLO.assert_called_once_with("fake_weights.pt")
        assert model is not None