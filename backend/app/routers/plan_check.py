"""POST /api/plan-check (Phase 3, FR-39 to FR-51)."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from backend.app.services import plan_check

router = APIRouter()


@router.post("/plan-check")
async def post_plan_check(request: Request):
    try:
        body = await request.json()
    except ValueError:
        return JSONResponse(status_code=422, content={"detail": "Request body must be JSON", "field": "body"})
    try:
        return plan_check.run(body if isinstance(body, dict) else {})
    except plan_check.PlanCheckError as e:
        return JSONResponse(status_code=422, content={"detail": e.reason, "field": e.field})
