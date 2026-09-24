from reliable_webhook_api.domain import FailureCode, FailureMessage, FailureReason


class ProcessingFailureMapper:
    _fallback_message = "Event processor failed."

    def from_exception(self, error: Exception) -> FailureReason:
        message = str(error).strip() or self._fallback_message
        return FailureReason(
            code=FailureCode("processor_error"),
            message=FailureMessage(message),
        )
