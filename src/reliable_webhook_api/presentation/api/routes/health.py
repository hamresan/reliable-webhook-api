from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from reliable_webhook_api.application.ports import Metrics
from reliable_webhook_api.infrastructure.health import DatabaseReadinessChecker
from reliable_webhook_api.infrastructure.observability import get_metrics
from reliable_webhook_api.presentation.api.dependencies.health import get_readiness_checker

router = APIRouter()


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    status: Literal["ready"]


ReadinessDependency = Annotated[DatabaseReadinessChecker, Depends(get_readiness_checker)]
MetricsDependency = Annotated[Metrics, Depends(get_metrics)]


@router.get("/health", response_model=HealthResponse)
async def health(metrics: MetricsDependency) -> HealthResponse:
    """Return the API liveness status."""

    metrics.increment("health_liveness_requests")
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={503: {"description": "Database is unavailable."}},
)
async def readiness(
    checker: ReadinessDependency,
    metrics: MetricsDependency,
) -> ReadinessResponse | JSONResponse:
    """Return readiness separately from liveness."""

    if not await checker.is_ready():
        metrics.increment("health_readiness_failures")
        return JSONResponse(status_code=503, content={"detail": "Service is not ready."})

    metrics.increment("health_readiness_success")
    return ReadinessResponse(status="ready")
