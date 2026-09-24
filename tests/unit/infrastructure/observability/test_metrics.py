from reliable_webhook_api.infrastructure.observability import InMemoryMetrics


def test_metrics_increment_counts_named_events() -> None:
    metrics = InMemoryMetrics()

    metrics.increment("accepted")
    metrics.increment("accepted")

    assert metrics.value("accepted") == 2
    assert metrics.value("missing") == 0
