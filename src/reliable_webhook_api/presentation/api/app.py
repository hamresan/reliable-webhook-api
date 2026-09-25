from fastapi import FastAPI

from reliable_webhook_api.config import get_settings
from reliable_webhook_api.infrastructure.observability import configure_logging
from reliable_webhook_api.presentation.api.development import configure_development_swagger
from reliable_webhook_api.presentation.api.middleware import (
    CorrelationIdMiddleware,
    PayloadSizeLimitMiddleware,
)
from reliable_webhook_api.presentation.api.routes.events import router as events_router
from reliable_webhook_api.presentation.api.routes.health import router as health_router
from reliable_webhook_api.presentation.api.routes.webhooks import router as webhook_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    settings = get_settings()
    configure_logging(settings.logging_level)

    development_swagger_enabled = settings.environment == "development"
    app = FastAPI(
        title=settings.app_name,
        docs_url=None if development_swagger_enabled else "/docs",
    )
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        PayloadSizeLimitMiddleware,
        max_payload_bytes=settings.max_payload_bytes,
    )
    app.include_router(health_router)
    app.include_router(events_router)
    app.include_router(webhook_router)

    if development_swagger_enabled:
        configure_development_swagger(
            app,
            webhook_secret=settings.webhook_secret,
            signature_header=settings.webhook_signature_header,
        )

    return app


app = create_app()
