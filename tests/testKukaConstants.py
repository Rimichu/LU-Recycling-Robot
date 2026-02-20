"""
Tests for kuka/constants.py — verify all expected constants are present
and have sane values.
"""
import sys
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestKukaConstants:
    def test_imports(self):
        from kuka.constants import CAM_FRAME_WIDTH, CAM_FRAME_HEIGHT
        assert isinstance(CAM_FRAME_WIDTH, int)
        assert isinstance(CAM_FRAME_HEIGHT, int)

    def test_frame_dimensions_positive(self):
        from kuka.constants import CAM_FRAME_WIDTH, CAM_FRAME_HEIGHT
        assert CAM_FRAME_WIDTH > 0
        assert CAM_FRAME_HEIGHT > 0

    def test_frame_dimensions_reasonable(self):
        from kuka.constants import CAM_FRAME_WIDTH, CAM_FRAME_HEIGHT
        # At least VGA, at most 4K
        assert 320 <= CAM_FRAME_WIDTH <= 3840
        assert 240 <= CAM_FRAME_HEIGHT <= 2160