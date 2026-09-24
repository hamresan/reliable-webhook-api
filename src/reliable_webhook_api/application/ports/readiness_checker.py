from typing import Protocol


class ReadinessChecker(Protocol):
    async def is_ready(self) -> bool: ...
