from types import TracebackType

from reliable_webhook_api.application.ports import UnitOfWork


class FakeUnitOfWork(UnitOfWork):
    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        return None
