import logging


def configure_logging(level: str) -> None:
    """Configure structured key-value friendly application logging."""

    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
