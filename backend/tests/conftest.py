"""
Pytest configuration and shared fixtures for Bhumi Vikas Sahayak backend tests.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure root is on path
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def client():
    """Test client with the full FastAPI app."""
    from backend.app.main import app
    return TestClient(app)


@pytest.fixture(scope="session")
def corpus():
    """Loaded corpus for unit tests."""
    from backend.app.config import load_settings
    from backend.app.corpus import load_corpus
    settings = load_settings()
    return load_corpus(settings)


@pytest.fixture(scope="session")
def settings():
    """Loaded settings."""
    from backend.app.config import load_settings
    return load_settings()
