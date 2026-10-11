"""
Configuration loader for Bhumi Vikas Sahayak backend.
All file paths and thresholds come from config/settings.json.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class Settings:
    consolidated_to: str
    version_label: str
    corpus_path: Path
    fulltext_path: Path
    pdf_en_path: Path
    pdf_hi_path: Path
    log_path: Path
    relevance_threshold: float
    inference_timeout_s: int
    devanagari_ratio_threshold: float
    high_rise_height_threshold_m: float
    expected_record_count: int
    disclaimer: str
    range_tables_path: Path = field(default_factory=lambda: ROOT / "config" / "range_tables.json")
    topic_map_path: Path = field(default_factory=lambda: ROOT / "config" / "topic_map.json")
    amendments_path: Path = field(default_factory=lambda: ROOT / "config" / "amendments.json")

    # Inference (optional, from env)
    inference_url: Optional[str] = None
    inference_key: Optional[str] = None
    inference_model: Optional[str] = None

    @property
    def inference_configured(self) -> bool:
        return bool(self.inference_url)


def load_settings(settings_path: Optional[Path] = None) -> Settings:
    """Load settings from config/settings.json; fail fast if missing."""
    if settings_path is None:
        settings_path = ROOT / "config" / "settings.json"

    if not settings_path.exists():
        raise FileNotFoundError(f"settings.json not found at {settings_path}")

    raw = json.loads(settings_path.read_text(encoding="utf-8"))

    import os
    return Settings(
        consolidated_to=raw["consolidated_to"],
        version_label=raw["version_label"],
        corpus_path=ROOT / raw["corpus_path"],
        fulltext_path=ROOT / raw["fulltext_path"],
        pdf_en_path=ROOT / raw["pdf_en_path"],
        pdf_hi_path=ROOT / raw["pdf_hi_path"],
        log_path=ROOT / raw["log_path"],
        relevance_threshold=raw["relevance_threshold"],
        inference_timeout_s=raw["inference_timeout_s"],
        devanagari_ratio_threshold=raw["devanagari_ratio_threshold"],
        high_rise_height_threshold_m=raw["high_rise_height_threshold_m"],
        expected_record_count=raw["expected_record_count"],
        disclaimer=raw["disclaimer"],
        inference_url=os.environ.get("BVS_INFERENCE_URL"),
        inference_key=os.environ.get("BVS_INFERENCE_KEY"),
        inference_model=os.environ.get("BVS_INFERENCE_MODEL"),
    )
