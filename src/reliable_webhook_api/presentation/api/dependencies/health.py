from functools import lru_cache

from reliable_webhook_api.infrastructure.health import DatabaseReadinessChecker
from reliable_webhook_api.presentation.api.dependencies.webhooks import get_database_engine


@lru_cache
def get_readiness_checker() -> DatabaseReadinessChecker:
    return DatabaseReadinessChecker(get_database_engine())
