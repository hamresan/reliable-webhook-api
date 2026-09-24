from fastapi import FastAPI

from reliable_webhook_api.presentation.api.routes.health import router as health_router
from reliable_webhook_api.presentation.api.routes.webhooks import router as webhook_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(title="Reliable Webhook API")
    app.include_router(health_router)
    app.include_router(webhook_router)
    return app


app = create_app()
