from datetime import date

from django.test import TestCase
from unittest.mock import patch

from provider.adapter_registry import get_adapter_class
from provider.adapters.currencybeacon import CurrencyBeaconAdapter
from provider.exceptions import ProviderAPIError
from provider.models import Provider


class AdapterRegistryTests(TestCase):
    """Ensure the adapter registry loads adapters correctly."""

    def test_get_adapter_class_success(self):
        """Known adapter key must return a class."""
        cls = get_adapter_class("mockExchangeRate")
        self.assertIsNotNone(cls)

    def test_get_adapter_class_unknown_key_raises(self):
        """Unknown key should raise LookupError."""
        with self.assertRaises(LookupError):
            get_adapter_class("unknown_key")


class CurrencyBeaconAdapterTests(TestCase):
    """Tests for the CurrencyBeacon provider adapter."""

    def setUp(self):
        # Provider configured for this adapter
        self.provider = Provider.objects.create(
            name="CurrencyBeacon",
            adapter_key="currencybeacon",
            api_url="https://api.currencybeacon.com/v1",
            is_active=True,
            priority=0,
        )

    @patch("provider.adapters.currencybeacon.requests.get")
    def test_currency_beacon_non_200_raises_provider_error(self, mock_get):
        """Non-200 responses must raise ProviderAPIError."""

        mock_get.return_value.status_code = 400
        mock_get.return_value.json.return_value = {"error": "bad request"}

        adapter = CurrencyBeaconAdapter(provider=self.provider)

        with self.assertRaises(ProviderAPIError):
            adapter.get_exchange_rate_data("EUR", "USD", date.today())
