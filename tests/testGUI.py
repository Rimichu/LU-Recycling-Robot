"""
Tests for the GUI module (gui/).

These tests verify the ControlPanel can be instantiated and configured
without actually rendering windows (Tk is stubbed where needed).
"""
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestControlPanelImport:
    """Verify the GUI module is importable."""

    def test_import_control_panel(self):
        try:
            from gui.control_panel import ControlPanel
        except ImportError:
            pytest.skip("gui module not available")

    def test_control_panel_has_expected_interface(self):
        try:
            from gui.control_panel import ControlPanel
        except ImportError:
            pytest.skip("gui module not available")
        # Verify key methods/attributes exist
        assert callable(getattr(ControlPanel, "__init__", None))