"""E2E test fixtures — starts a real dev server for Playwright tests."""
import socket
import subprocess
import sys
import time

import pytest

E2E_PORT = 5099
E2E_BASE_URL = f"http://localhost:{E2E_PORT}"


def _port_is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


@pytest.fixture(scope="session")
def base_url():
    """Start the dev server and return the base URL."""
    if _port_is_open(E2E_PORT):
        # Server already running (manual dev mode) — reuse it
        yield E2E_BASE_URL
        return

    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app",
         "--host", "127.0.0.1", "--port", str(E2E_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    # Wait for server to be ready (up to 10 seconds)
    for _ in range(100):
        if _port_is_open(E2E_PORT):
            break
        time.sleep(0.1)
    else:
        proc.kill()
        raise RuntimeError(f"Dev server failed to start on port {E2E_PORT}")

    yield E2E_BASE_URL

    proc.terminate()
    proc.wait(timeout=5)
