import inspect

from reliable_webhook_api.application.use_cases import ReceiveWebhookEvent


def test_receive_webhook_event_does_not_depend_on_event_processor() -> None:
    parameters = inspect.signature(ReceiveWebhookEvent.__init__).parameters

    assert "processor" not in parameters
    assert "event_processor" not in parameters
