from reliable_webhook_api.application.processing import ProcessingFailureMapper


def test_maps_processor_exception_to_sanitized_failure_reason() -> None:
    failure = ProcessingFailureMapper().from_exception(
        RuntimeError("provider token=super-secret rejected event")
    )

    assert failure.code.value == "processor_error"
    assert failure.message.value == "Event processor failed."


def test_uses_same_safe_message_for_empty_exception() -> None:
    failure = ProcessingFailureMapper().from_exception(RuntimeError())

    assert failure.code.value == "processor_error"
    assert failure.message.value == "Event processor failed."
