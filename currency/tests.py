from datetime import date

from django.test import TestCase

from currency.models import Currency, CurrencyExchangeRate
from currency.validators import (
    validate_convert_params,
    validate_get_exchange_rates_history_params,
)
from currency.services.exchange_rate_loader import get_exchange_rate
from provider.models import Provider
from provider.exceptions import ProviderAPIError
from provider.adapter_registry import get_adapter_class
from unittest.mock import patch


class ValidatorTests(TestCase):
    """Tests for input validators ensuring correct parsing and validation."""

    def setUp(self):
        # Preload currencies required for validation
        self.eur = Currency.objects.create(code="EUR", name="Euro", symbol="€")
        self.usd = Currency.objects.create(code="USD", name="US Dollar", symbol="$")

    def test_validate_convert_params_success(self):
        """Valid input returns correct Currency objects + parsed amount."""
        source, [target], amount = validate_convert_params(
            "EUR", ["USD"], "100.5"
        )
        self.assertEqual(source.code, "EUR")
        self.assertEqual(target.code, "USD")
        self.assertEqual(amount, 100.5)

    def test_validate_convert_params_invalid_amount(self):
        """Invalid amount raises ValueError."""
        with self.assertRaises(ValueError):
            validate_convert_params("EUR", ["USD"], "not-a-number")

    def test_validate_get_history_success(self):
        """History validation should parse dates + resolve currency."""
        source, targets, start, end = validate_get_exchange_rates_history_params(
            "EUR", "2025-01-01", "2025-01-03"
        )
        self.assertEqual(source.code, "EUR")
        self.assertTrue(len(targets) >= 1)
        self.assertEqual(str(start), "2025-01-01")
        self.assertEqual(str(end), "2025-01-03")

    def test_validate_get_history_invalid_date(self):
        """Invalid date format raises ValueError."""
        with self.assertRaises(ValueError):
            validate_get_exchange_rates_history_params(
                "EUR", "bad-date", "2025-01-03"
            )

    def test_validate_get_history_unknown_currency(self):
        """Unknown currency code raises ValueError."""
        with self.assertRaises(ValueError):
            validate_get_exchange_rates_history_params(
                "XXX", "2025-01-01", "2025-01-03"
            )


class GetExchangeRateServiceTests(TestCase):
    """Tests for the service that retrieves/stores exchange rates."""

    def setUp(self):
        # Basic currencies needed for tests
        self.eur = Currency.objects.create(code="EUR", name="Euro", symbol="€")
        self.usd = Currency.objects.create(code="USD", name="US Dollar", symbol="$")

        # One mock provider (existing in adapter registry)
        self.provider = Provider.objects.create(
            name="Mock Provider",
            adapter_key="mockExchangeRate",
            api_url="",
            is_active=True,
            priority=0,
        )
        self.providers = [self.provider]

    def test_get_exchange_rate_uses_db_if_present(self):
        """Should not call provider if rate already exists in DB."""
        today = date.today()

        CurrencyExchangeRate.objects.create(
            source_currency=self.eur,
            exchanged_currency=self.usd,
            valuation_date=today,
            rate_value=1.2345,
        )

        with patch(
            "currency.services.exchange_rate_loader.get_exchange_rate_from_provider"
        ) as mocked_provider_call:

            rate = get_exchange_rate(self.eur, self.usd, today, self.providers)

            mocked_provider_call.assert_not_called()
            self.assertEqual(float(rate), 1.2345)

    def test_get_exchange_rate_calls_provider_and_saves_when_missing(self):
        """If rate is not in DB, provider should be called and value saved."""
        today = date.today()

        adapter_class = get_adapter_class("mockExchangeRate")

        with patch.object(
            adapter_class, "get_exchange_rate_data", return_value=1.5
        ) as mocked_get:

            rate = get_exchange_rate(self.eur, self.usd, today, self.providers)

            self.assertEqual(rate, 1.5)
            mocked_get.assert_called_once()

            saved = CurrencyExchangeRate.objects.get(
                source_currency=self.eur,
                exchanged_currency=self.usd,
                valuation_date=today,
            )
            self.assertEqual(saved.rate_value, 1.5)

    def test_get_exchange_rate_all_providers_fail_raises(self):
        """If all providers fail, a LookupError is raised."""
        today = date.today()

        adapter_class = get_adapter_class("mockExchangeRate")

        with patch.object(
            adapter_class,
            "get_exchange_rate_data",
            side_effect=ProviderAPIError("boom"),
        ):
            with self.assertRaises(LookupError):
                get_exchange_rate(self.eur, self.usd, today, self.providers)
