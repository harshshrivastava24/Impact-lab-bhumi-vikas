"""FastAPI application. Run: uvicorn backend.app.main:app"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .services import corpus, inference, plan_check

app = FastAPI(title="Bhumi Vikas Sahayak", description="Rule lookup and compliance decision-support tool")


@app.post("/api/plan-check")
async def post_plan_check(request: Request):
    try:
        body = await request.json()
    except ValueError:
        return JSONResponse(status_code=422, content={"detail": "Request body must be JSON", "field": "body"})
    try:
        return plan_check.run(body if isinstance(body, dict) else {})
    except plan_check.PlanCheckError as e:
        return JSONResponse(status_code=422, content={"detail": e.reason, "field": e.field})


@app.post("/api/lookup")
@app.post("/api/parse")
def not_built():
    return JSONResponse(status_code=501, content={"detail": "Rule lookup and parsing are built in Phase 2."})


@app.get("/api/rules/{rule}")
def get_rule(rule: str):
    c = corpus.citation(rule)
    if c is None:
        raise HTTPException(404, f"Rule {rule} not in the loaded corpus")
    return c


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "rules_loaded": len(corpus.records()),
        "version": config.settings()["version"]["consolidated_to"],
        "inference_configured": inference.configured(),
    }


@app.get("/pdf/{lang}")
def pdf(lang: str):
    if lang not in ("en", "hi"):
        raise HTTPException(404)
    p = config.path(f"pdf_{lang}")
    if not p.exists():
        raise HTTPException(404, f"{p.name} not present in resources/")
    return FileResponse(p, media_type="application/pdf")


_dist = config.path("frontend_dist")
if _dist.exists():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
