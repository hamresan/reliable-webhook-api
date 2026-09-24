from reliable_webhook_api.application.errors.base import ApplicationError


class ConflictError(ApplicationError):
    pass


class DuplicateEventError(ConflictError):
    pass
