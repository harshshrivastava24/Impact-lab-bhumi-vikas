"""Shared data access for the plan check (Phase 3).

Reads the same files as the Phase 2 lookup: config/settings.json, config/range_tables.json and the
corpus loaded by backend.app.corpus. Adds only the plan-check files: exceptions and interface strings.
"""
import json
import os
from functools import lru_cache
from pathlib import Path

from .config import ROOT, load_settings
from .corpus import load_corpus

CONFIG = ROOT / "config"


def _load(name: str):
    with open(CONFIG / name, encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def raw_settings() -> dict:
    return _load("settings.json")


@lru_cache
def app_settings():
    return load_settings()


@lru_cache
def corpus():
    return load_corpus(app_settings())


@lru_cache
def tables() -> dict:
    return {t["id"]: t for t in _load("range_tables.json")}


@lru_cache
def exceptions() -> list:
    return _load("exceptions.json")


@lru_cache
def strings(language: str) -> dict:
    base = _load("strings.en.json")
    if language == "hi":
        base = {**base, **_load("strings.hi.json")}
    return base


def version() -> dict:
    s = app_settings()
    return {"consolidated_to": s.consolidated_to, "label": s.version_label}


def log_path() -> Path:
    override = os.environ.get("BVS_LOG_PATH")
    return Path(override) if override else app_settings().log_path
