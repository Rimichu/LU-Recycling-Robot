"""
Tests targeting the main application (main.py) and its helpers.

Hardware connections are mocked so tests can run offline.
"""
import sys
import socket
import threading
import time
import logging
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ── load_camera_calibration ──────────────────────────────────────────────

class TestLoadCameraCalibration:
    """Test calibration loader from main.py."""

    def test_loads_valid_npz(self, calibration_data):
        from main import load_camera_calibration
        path, expected_mtx, expected_dist = calibration_data
        mtx, dist = load_camera_calibration(path)
        np.testing.assert_array_almost_equal(mtx, expected_mtx)
        np.testing.assert_array_almost_equal(dist, expected_dist)

    def test_returns_none_when_file_missing(self, tmp_path):
        from main import load_camera_calibration
        mtx, dist = load_camera_calibration(tmp_path / "nonexistent.npz")
        assert mtx is None
        assert dist is None

    def test_returns_none_on_corrupt_file(self, tmp_path):
        from main import load_camera_calibration
        bad = tmp_path / "bad.npz"
        bad.write_bytes(b"not a real npz file")
        mtx, dist = load_camera_calibration(bad)
        assert mtx is None
        assert dist is None

    def test_returns_none_when_keys_missing(self, tmp_path):
        from main import load_camera_calibration
        path = tmp_path / "incomplete.npz"
        np.savez(path, foo=np.array([1, 2, 3]))
        mtx, dist = load_camera_calibration(path)
        assert mtx is None
        assert dist is None


# ── connect_to_pi / disconnect_from_pi ───────────────────────────────────

class TestPiConnection:
    """Test TCP connect/disconnect helpers."""

    def test_connect_to_pi_succeeds(self, tcp_echo_server):
        from main import connect_to_pi
        host, port = tcp_echo_server
        sock = connect_to_pi(pi_server_address=host, pi_server_port=port)
        assert sock is not None
        assert isinstance(sock, socket.socket)
        sock.close()

    def test_connect_to_pi_timeout_on_bad_host(self):
        from main import connect_to_pi
        with pytest.raises((socket.timeout, ConnectionRefusedError, OSError)):
            connect_to_pi(pi_server_address="192.0.2.1", pi_server_port=1)

    def test_disconnect_from_pi(self, tcp_echo_server):
        from main import connect_to_pi, disconnect_from_pi
        host, port = tcp_echo_server
        sock = connect_to_pi(pi_server_address=host, pi_server_port=port)
        disconnect_from_pi(sock)
        # Socket should be closed — sending should fail
        with pytest.raises(OSError):
            sock.sendall(b"test")


# ── connect_to_robot / disconnect_from_robot ─────────────────────────────

class TestRobotConnection:
    """Test Kuka robot connect/disconnect (mocked)."""

    @patch("main.KukaRobot")
    def test_connect_to_robot(self, MockKuka):
        from main import connect_to_robot
        instance = MockKuka.return_value
        robot = connect_to_robot(ip_address="192.168.1.195", speed=1)
        MockKuka.assert_called_once_with("192.168.1.195")
        instance.connect.assert_called_once()
        instance.set_speed.assert_called_once_with(1)
        assert robot is instance

    @patch("main.KukaRobot")
    def test_disconnect_from_robot(self, MockKuka):
        from main import connect_to_robot, disconnect_from_robot
        robot = connect_to_robot()
        disconnect_from_robot(robot)
        robot.disconnect.assert_called_once()

    @patch("main.KukaRobot")
    def test_connect_custom_speed(self, MockKuka):
        from main import connect_to_robot
        instance = MockKuka.return_value
        connect_to_robot(speed=5)
        instance.set_speed.assert_called_once_with(5)