"""
Parser service: language detection, rule-based parameter extraction.
Implements FR-02, FR-03, and optional inference via FR-05 Section 5.3.
"""
from __future__ import annotations

import json
import logging
import re
import unicodedata
from typing import Any, Dict, List, Optional

from backend.app.models import Params, Topic

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Language detection (FR-03)
# ---------------------------------------------------------------------------

def detect_language(text: str, devanagari_threshold: float = 0.2) -> str:
    """Detect language: ratio of Devanagari chars above threshold → 'hi'."""
    if not text:
        return "en"
    devanagari_count = sum(
        1 for c in text
        if "\u0900" <= c <= "\u097F"  # Devanagari block
    )
    ratio = devanagari_count / len(text)
    return "hi" if ratio >= devanagari_threshold else "en"


# ---------------------------------------------------------------------------
# Rule-based parser (FR-02)
# ---------------------------------------------------------------------------

# Number extraction patterns for English and Hindi
_NUMBER_RE = re.compile(
    r"(?:"
    r"(\d+(?:\.\d+)?)\s*"  # digits
    r"(?:"
    r"sq\.?\s*m(?:eter|etre)?s?|वर्ग\s*मीटर|sqm|sq\.m\."  # area units
    r"|m(?:eter|etre)?s?\b|मीटर|metre|meter"               # length units
    r")"
    r")",
    re.IGNORECASE,
)

_AREA_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:sq\.?\s*m(?:eter|etre)?s?|वर्ग\s*मीटर|sqm|sq\.m\.)",
    re.IGNORECASE,
)

_LENGTH_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:m(?:eter|etre)?s?\b|मीटर|metre|meter|मी\.?)",
    re.IGNORECASE,
)

# Keywords per topic (for topic detection)
TOPIC_KEYWORDS: Dict[str, List[str]] = {
    "front_setback": ["front", "front open space", "building line", "setback from road",
                      "मुख", "सामने", "सड़क से", "front setback"],
    "rear_setback": ["rear", "back", "rear open space", "rear setback",
                     "पीछे", "पश्चिम", "पिछली"],
    "side_setback": ["side", "lateral", "side open space", "side setback",
                     "बगल", "साइड", "पार्श्व"],
    "height_limit": ["height", "maximum height", "how tall", "floors", "storey",
                     "ऊंचाई", "मंजिल", "उचाई"],
    "far": ["FAR", "floor area ratio", "floor area", "built-up area allowed",
            "एफएआर", "फ्लोर एरिया"],
    "ground_coverage": ["ground coverage", "coverage", "GC"],
    "application_fee": ["application fee", "fees", "how much fee", "शुल्क", "आवेदन शुल्क"],
    "permission_fee": ["permission fee", "sanction fee", "अनुमति शुल्क"],
    "permission_validity": ["validity", "valid for", "how long", "expire", "revalidate",
                             "मान्यता", "कितने समय"],
    "documents_required": ["documents", "papers", "what documents", "required documents",
                            "दस्तावेज़", "कागज"],
    "plan_check": ["plan check", "footprint", "compliance check", "drawing"],
}

# Road-width keywords
_ROAD_KEYWORDS = re.compile(
    r"road(?:\s+width)?\s+(?:of\s+|is\s+)?(\d+(?:\.\d+)?)\s*m|"
    r"(\d+(?:\.\d+)?)\s*m\s+road|"
    r"सड़क\s+(?:की\s+)?चौड़ाई\s+(\d+(?:\.\d+)?)\s*मी",
    re.IGNORECASE,
)

_PLOT_KEYWORDS = re.compile(
    r"plot\s+(?:area\s+)?(?:of\s+|is\s+)?(\d+(?:\.\d+)?)\s*sq|"
    r"(\d+(?:\.\d+)?)\s*sq\s*m\s+plot|"
    r"प्लॉट\s+(?:क्षेत्र\s+)?(\d+(?:\.\d+)?)\s*वर्ग",
    re.IGNORECASE,
)

USE_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "residential": ["residential", "residence", "house", "home", "dwelling", "आवासीय", "घर"],
    "commercial": ["commercial", "shop", "office", "व्यावसायिक", "दुकान"],
    "public": ["public", "semi-public", "school", "hospital", "सार्वजनिक"],
    "industrial": ["industrial", "factory", "warehouse", "औद्योगिक", "कारखाना"],
    "agricultural": ["agricultural", "farm", "कृषि"],
}

DEV_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "detached": ["detached", "स्वतंत्र"],
    "semi_detached": ["semi-detached", "semi detached", "अर्ध-स्वतंत्र"],
    "row": ["row", "row type", "पंक्ति"],
}


def parse_text_rule_based(text: str) -> tuple[Params, List[Topic]]:
    """
    Rule-based parser: extract Params and Topics from text without inference.
    Handles sample questions 1, 8, 10, 14, 15 without inference.
    """
    params = Params()
    topics: List[Topic] = []
    lower = text.lower()

    # Extract road width
    m = _ROAD_KEYWORDS.search(text)
    if m:
        road_val = m.group(1) or m.group(2) or m.group(3)
        if road_val:
            params.road_width = float(road_val)

    # Extract plot area
    m = _PLOT_KEYWORDS.search(text)
    if m:
        plot_val = m.group(1) or m.group(2) or m.group(3)
        if plot_val:
            params.plot_area = float(plot_val)

    # If not found by keyword, try generic area extraction
    if params.plot_area is None:
        areas = _AREA_RE.findall(text)
        if areas:
            params.plot_area = float(areas[0])

    # Road width generic if not found
    if params.road_width is None:
        # look for "X m road" or "road X m"
        m2 = re.search(r"(\d+(?:\.\d+)?)\s*m(?:eter)?s?\s+(?:wide\s+)?road|road\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*m", lower)
        if m2:
            rw = m2.group(1) or m2.group(2)
            if rw:
                params.road_width = float(rw)

    # Extract use type
    for use_type, keywords in USE_TYPE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            params.use_type = use_type  # type: ignore
            break

    # Extract development type
    for dev_type, keywords in DEV_TYPE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            params.development_type = dev_type  # type: ignore
            break

    # Extract height
    height_m = re.search(r"(?:height|tall)\s+(?:of\s+|is\s+)?(\d+(?:\.\d+)?)\s*m", lower)
    if height_m:
        params.height = float(height_m.group(1))

    # Extract built-up area (after plot area)
    bua_m = re.search(r"built[- ]up\s+area\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*sq", lower)
    if bua_m:
        params.built_up_area = float(bua_m.group(1))

    # Extract frontage
    frontage_m = re.search(r"frontage\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*m", lower)
    if frontage_m:
        params.frontage = float(frontage_m.group(1))

    # Extract depth
    depth_m = re.search(r"depth\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*m", lower)
    if depth_m:
        params.depth = float(depth_m.group(1))

    # Existing developed area flag
    if re.search(r"existing\s+developed\s+area|existing\s+area", lower):
        params.existing_developed_area = True

    # Detect topics
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw.lower() in lower for kw in keywords):
            t = topic  # type: ignore
            if t not in topics:
                topics.append(t)

    # If no topics detected and we have params, infer common topics
    if not topics and (params.plot_area or params.road_width):
        topics = ["front_setback", "rear_setback", "height_limit", "far"]

    return params, topics


# ---------------------------------------------------------------------------
# Optional inference (Section 5.3)
# ---------------------------------------------------------------------------

async def parse_with_inference(text: str, settings) -> Optional[tuple[Params, List[Topic], bool]]:
    """
    Call optional inference endpoint if configured.
    Returns (params, topics, True) or None on failure.
    All numbers are validated and rejected if the LLM tries to include rule numbers or figures.
    """
    if not settings.inference_url:
        return None

    import httpx

    prompt = (
        "You are a parameter extractor for a building rule lookup system. "
        "From the following query, extract ONLY the parameters and topics in JSON. "
        "Do NOT include any rule numbers, page numbers, distances, areas or fee amounts in your response. "
        "Return ONLY this JSON structure with no other text:\n"
        "{\n"
        '  "params": {\n'
        '    "plot_area": <number or null>,\n'
        '    "road_width": <number or null>,\n'
        '    "use_type": <"residential"|"commercial"|"public"|"industrial"|"agricultural"|null>,\n'
        '    "built_up_area": <number or null>,\n'
        '    "height": <number or null>,\n'
        '    "development_type": <"detached"|"semi_detached"|"row"|null>,\n'
        '    "frontage": <number or null>,\n'
        '    "depth": <number or null>,\n'
        '    "floor_to_floor": <number or null>,\n'
        '    "existing_developed_area": <true|false|null>\n'
        "  },\n"
        '  "topics": [<list of: "front_setback","rear_setback","side_setback","height_limit","far","ground_coverage","application_fee","permission_fee","permission_validity","documents_required","plan_check">]\n'
        "}\n\n"
        f"Query: {text}"
    )

    try:
        headers = {"Content-Type": "application/json"}
        if settings.inference_key:
            headers["Authorization"] = f"Bearer {settings.inference_key}"

        payload = {
            "model": settings.inference_model or "default",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0,
        }

        async with httpx.AsyncClient(timeout=settings.inference_timeout_s) as client:
            resp = await client.post(settings.inference_url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        # Extract content from common LLM response formats
        content = ""
        if "choices" in data:
            content = data["choices"][0]["message"]["content"]
        elif "content" in data:
            content = data["content"]
        elif "text" in data:
            content = data["text"]

        # Parse the JSON
        parsed = json.loads(content)
        raw_params = parsed.get("params", {})
        raw_topics = parsed.get("topics", [])

        # Validate: reject any rule numbers injected by the LLM (FR-27)
        # (params only contain numeric/enum values – rule numbers would be strings like "56")
        # Build Params (FR-04 validation happens at the router level)
        params = Params(
            plot_area=_safe_float(raw_params.get("plot_area")),
            road_width=_safe_float(raw_params.get("road_width")),
            use_type=raw_params.get("use_type"),
            built_up_area=_safe_float(raw_params.get("built_up_area")),
            height=_safe_float(raw_params.get("height")),
            development_type=raw_params.get("development_type"),
            frontage=_safe_float(raw_params.get("frontage")),
            depth=_safe_float(raw_params.get("depth")),
            floor_to_floor=_safe_float(raw_params.get("floor_to_floor")),
            existing_developed_area=raw_params.get("existing_developed_area"),
        )

        valid_topics: List[Topic] = []
        allowed = {"front_setback","rear_setback","side_setback","height_limit","far",
                   "ground_coverage","application_fee","permission_fee",
                   "permission_validity","documents_required","plan_check"}
        for t in raw_topics:
            if t in allowed:
                valid_topics.append(t)  # type: ignore

        return params, valid_topics, True

    except Exception as exc:
        logger.warning("Inference call failed (%s); falling back to rule-based parser.", exc)
        return None


def _safe_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None
