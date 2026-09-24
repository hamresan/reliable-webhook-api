from types import TracebackType

from reliable_webhook_api.application.ports import Transaction


class NoopTransaction(Transaction):
    async def __aenter__(self) -> "NoopTransaction":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        return None
