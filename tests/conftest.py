"""Shared fixtures for the test suite."""
import sys
import types
import pytest
import socket
import threading
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Stub out hardware-only modules so imports don't fail on dev machines
# ---------------------------------------------------------------------------
_HARDWARE_MODULES = ["lgpio", "picamera2", "picamera2.encoders", "picamera2.outputs"]

for mod_name in _HARDWARE_MODULES:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def dummy_frame():
    """Return a small BGR test frame."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def calibration_data(tmp_path):
    """Create a temporary calibration .npz file and return its path."""
    mtx = np.array([[800, 0, 320],
                     [0, 800, 240],
                     [0,   0,   1]], dtype=np.float64)
    dist = np.array([0.1, -0.25, 0.0, 0.0, 0.0], dtype=np.float64)
    path = tmp_path / "calibration_data.npz"
    np.savez(path, mtx=mtx, dist=dist)
    return path, mtx, dist


@pytest.fixture
def tcp_echo_server():
    """Spin up a tiny TCP echo server; yields (host, port). Shuts down after test."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    host, port = server.getsockname()
    stop = threading.Event()

    def _serve():
        server.settimeout(1)
        while not stop.is_set():
            try:
                conn, _ = server.accept()
                data = conn.recv(1024)
                if data:
                    conn.sendall(data)
                conn.close()
            except socket.timeout:
                continue

    t = threading.Thread(target=_serve, daemon=True)
    t.start()
    yield host, port
    stop.set()
    server.close()
    t.join(timeout=3)