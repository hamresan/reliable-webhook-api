import pytest

from reliable_webhook_api.domain import ProviderName


@pytest.mark.parametrize("value", ["", "   "])
def test_provider_name_rejects_empty_value(value: str) -> None:
    with pytest.raises(ValueError, match="Provider name"):
        ProviderName(value)
