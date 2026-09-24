from reliable_webhook_api.application.use_cases import ProcessDueRetries


class RetryWorker:
    def __init__(self, process_due_retries: ProcessDueRetries) -> None:
        self._process_due_retries = process_due_retries

    async def run_once(self, limit: int = 100) -> int:
        return await self._process_due_retries.execute(limit)
