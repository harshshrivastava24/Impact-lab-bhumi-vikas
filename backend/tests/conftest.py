import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@pytest.fixture(autouse=True)
def log_to_tmp(tmp_path, monkeypatch):
    log = tmp_path / "queries.jsonl"
    monkeypatch.setenv("BVS_LOG_PATH", str(log))
    return log
