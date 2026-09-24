from reliable_webhook_api.application.ports import Metrics
from reliable_webhook_api.infrastructure.observability import get_metrics


def get_metrics_dependency() -> Metrics:
    return get_metrics()
