"""Optional Hindi explanatory rendering of traces (FR-30, Section 5.3).

Only runs when BVS_INFERENCE_URL is set. The output is a rendering, never official text: any rendering
whose numbers differ from the English trace is discarded, so no figure can originate here (FR-21).
"""
import json
import os
import re
import urllib.request

from .. import plan_config as config

_NUM = re.compile(r"\d+(?:\.\d+)?")


def configured() -> bool:
    return bool(os.environ.get("BVS_INFERENCE_URL"))


def render_hi(traces: list[str]) -> list[str] | None:
    if not configured() or not traces:
        return None
    prompt = (
        "Render each English line below as a plain Hindi explanation. Keep every number, rule number and page "
        "exactly as written in Western digits. Return only a JSON array of strings, one per line.\n"
        + json.dumps(traces, ensure_ascii=False)
    )
    body = json.dumps(
        {"model": os.environ.get("BVS_INFERENCE_MODEL", ""), "messages": [{"role": "user", "content": prompt}]}
    ).encode()
    headers = {"Content-Type": "application/json"}
    if os.environ.get("BVS_INFERENCE_KEY"):
        headers["Authorization"] = f"Bearer {os.environ['BVS_INFERENCE_KEY']}"
    try:
        req = urllib.request.Request(os.environ["BVS_INFERENCE_URL"], data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=config.app_settings().inference_timeout_s) as resp:
            content = json.load(resp)["choices"][0]["message"]["content"]
        out = json.loads(content)
    except Exception:
        return None
    if not isinstance(out, list) or len(out) != len(traces):
        return None
    if any(not isinstance(h, str) or _NUM.findall(h) != _NUM.findall(e) for h, e in zip(out, traces)):
        return None
    return out
