"""Loads data files from config/. No table value lives in Python source."""
import json
import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(os.environ.get("BVS_ROOT", Path(__file__).resolve().parents[2]))
CONFIG = ROOT / "config"


def _load(name: str):
    with open(CONFIG / name, encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def settings() -> dict:
    return _load("settings.json")


@lru_cache
def tables() -> dict:
    return _load("range_tables.json")["tables"]


@lru_cache
def exceptions() -> list:
    return _load("exceptions.json")


@lru_cache
def amendments() -> list:
    return _load("amendments.json")


@lru_cache
def strings(language: str) -> dict:
    base = _load("strings.en.json")
    if language == "hi":
        base = {**base, **_load("strings.hi.json")}
    return base


def path(key: str) -> Path:
    return ROOT / settings()["paths"][key]


def log_path() -> Path:
    override = os.environ.get("BVS_LOG_PATH")
    return Path(override) if override else path("log")
