"""Shared setup for the Playwright end-to-end tests.

These tests drive a real browser against a running copy of the app (started
with `python run.py` or the Docker container), so they talk to it over HTTP
instead of using Flask's test_client().

Set E2E_BASE_URL to point the tests somewhere other than http://127.0.0.1:5000.
"""

import os
import urllib.error
import urllib.request

import pytest

DEFAULT_BASE_URL = "http://127.0.0.1:5000"


@pytest.fixture(scope="session")
def base_url():
    """Overrides pytest-base-url so page.goto("/ui/...") resolves against the app."""
    return os.environ.get("E2E_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


@pytest.fixture(scope="session", autouse=True)
def require_running_app(base_url):
    """Skip (rather than fail) the E2E suite when no app is listening.

    This keeps a plain `pytest` run, such as the GitHub Actions unit-test job,
    working when nobody has started the server.
    """
    try:
        urllib.request.urlopen(base_url + "/", timeout=3)
    except (urllib.error.URLError, OSError):
        pytest.skip(f"E2E tests need the app running at {base_url}")
