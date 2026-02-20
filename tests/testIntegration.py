"""
Integration-level tests.

These combine multiple modules to verify end-to-end-like behaviour
without the actual hardware.
"""
import sys
import socket
import threading
import time
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestPiRoundTrip:
    """Connect to a mock Pi server, send a command, verify response."""

    @pytest.fixture
    def ping_server(self):
        """TCP server that responds to 'ping' with 'pong'."""
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        host, port = srv.getsockname()
        stop = threading.Event()

        def _run():
            srv.settimeout(1)
            while not stop.is_set():
                try:
                    conn, _ = srv.accept()
                    data = conn.recv(1024)
                    if data == b"ping":
                        conn.sendall(b"pong")
                    conn.close()
                except socket.timeout:
                    continue

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        yield host, port
        stop.set()
        srv.close()
        t.join(timeout=3)

    def test_ping_pong(self, ping_server):
        from main import connect_to_pi
        host, port = ping_server
        sock = connect_to_pi(pi_server_address=host, pi_server_port=port)
        sock.sendall(b"ping")
        resp = sock.recv(1024)
        assert resp == b"pong"
        sock.close()


class TestCalibrationIntegration:
    """Load calibration → build maps → undistort a frame."""

    def test_full_pipeline(self, calibration_data, dummy_frame):
        import cv2
        from main import load_camera_calibration

        path, expected_mtx, expected_dist = calibration_data
        mtx, dist = load_camera_calibration(path)
        assert mtx is not None

        map1, map2 = cv2.initUndistortRectifyMap(
            mtx, dist, None, mtx,
            (dummy_frame.shape[1], dummy_frame.shape[0]),
            cv2.CV_16SC2,
        )
        result = cv2.remap(dummy_frame, map1, map2, interpolation=cv2.INTER_LINEAR)
        assert result.shape == dummy_frame.shape
        assert result.dtype == dummy_frame.dtype