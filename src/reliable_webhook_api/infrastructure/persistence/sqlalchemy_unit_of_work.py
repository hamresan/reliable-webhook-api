from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

from reliable_webhook_api.application.ports import UnitOfWork


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        if exc_type is None:
            await self._session.commit()
        else:
            await self._session.rollback()
        return None
