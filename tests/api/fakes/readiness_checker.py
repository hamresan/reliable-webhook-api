from reliable_webhook_api.application.ports import ReadinessChecker


class FakeReadinessChecker(ReadinessChecker):
    def __init__(self, ready: bool) -> None:
        self._ready = ready

    async def is_ready(self) -> bool:
        return self._ready
