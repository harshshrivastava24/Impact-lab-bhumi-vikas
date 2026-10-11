"""
Pydantic models for Bhumi Vikas Sahayak API contract.
Implements the shared context data model exactly.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Params and Topics
# ---------------------------------------------------------------------------

UseType = Literal["residential", "commercial", "public", "industrial", "agricultural"]
DevelopmentType = Literal["detached", "semi_detached", "row"]
Topic = Literal[
    "front_setback", "rear_setback", "side_setback",
    "height_limit", "far", "ground_coverage",
    "application_fee", "permission_fee",
    "permission_validity", "documents_required", "plan_check",
]


class Params(BaseModel):
    plot_area: Optional[float] = None
    road_width: Optional[float] = None
    use_type: Optional[UseType] = None
    built_up_area: Optional[float] = None
    height: Optional[float] = None
    development_type: Optional[DevelopmentType] = None
    frontage: Optional[float] = None
    depth: Optional[float] = None
    floor_to_floor: Optional[float] = None
    existing_developed_area: Optional[bool] = None
    streets_abutting: Optional[int] = None


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------

class Figure(BaseModel):
    topic: Topic
    label: str
    value: Optional[float] = None
    unit: str
    derived: bool = False
    conditional: bool = False
    trace: str
    rule: str
    page: int
    cases: Optional[List["Figure"]] = None
    warning: Optional[str] = None


Figure.model_rebuild()


# ---------------------------------------------------------------------------
# Citation
# ---------------------------------------------------------------------------

class Citation(BaseModel):
    rule: str
    sub_rule: Optional[str] = None
    title: str
    part: str
    page_start: int
    page_end: int
    text_en: str
    pdf_en_url: str
    pdf_hi_url: str
    footnotes: List[str] = Field(default_factory=list)
    candidate: bool = False
    excerpt: Optional[str] = None


# ---------------------------------------------------------------------------
# Amendment flag
# ---------------------------------------------------------------------------

class AmendmentFlag(BaseModel):
    date: str
    rule: str
    concerns: str
    source_url: str
    source_kind: Literal["primary", "secondary"]
    applied: bool = False
    note: str


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

class Version(BaseModel):
    consolidated_to: str
    label: str


# ---------------------------------------------------------------------------
# Lookup request / response
# ---------------------------------------------------------------------------

class LookupRequest(BaseModel):
    params: Params = Field(default_factory=Params)
    topics: List[Topic] = Field(default_factory=list)
    language: Literal["en", "hi"] = "en"
    query: Optional[str] = None
    raw_query: Optional[str] = None


class LookupResponse(BaseModel):
    status: Literal["answered", "not_found", "refused", "blocked"]
    message: Optional[str] = None
    figures: List[Figure] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    version: Version
    amendment_flags: List[AmendmentFlag] = Field(default_factory=list)
    disclaimer: str
    language: Literal["en", "hi"]
    used_inference: bool = False


# ---------------------------------------------------------------------------
# Parse request / response
# ---------------------------------------------------------------------------

class ParseRequest(BaseModel):
    text: str


class ParseResponse(BaseModel):
    language: Literal["en", "hi"]
    params: Params
    topics: List[Topic] = Field(default_factory=list)
    used_inference: bool = False


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    ok: bool
    rules_loaded: int
    version: str
    inference_configured: bool
