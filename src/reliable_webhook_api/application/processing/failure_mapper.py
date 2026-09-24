from reliable_webhook_api.domain import FailureCode, FailureMessage, FailureReason


class ProcessingFailureMapper:
    _safe_message = "Event processor failed."

    def from_exception(self, error: Exception) -> FailureReason:
        del error
        return FailureReason(
            code=FailureCode("processor_error"),
            message=FailureMessage(self._safe_message),
        )
