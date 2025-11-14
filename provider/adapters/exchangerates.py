import requests
from datetime import date
from .base import BaseProviderAdapter
from ..exceptions import ProviderAPIError


class ExchangeRateAdapter(BaseProviderAdapter):
    def get_exchange_rate_data(
            self,
            source_currency: str,
            exchanged_currency: str,
            valuation_date: date,
    ) -> float:
        """
            Fetch a rate from ExchangeRates API (apilayer).

            Raises:
                ProviderAPIError: when the API call fails or the response is invalid.
        """
        url = f"{self.provider.api_url}/{valuation_date.strftime('%Y-%m-%d')}"
        params = {
            "access_key": self.api_key,
            "base": source_currency,
            "symbols": exchanged_currency,
        }

        response = requests.get(url, params=params)

        data = response.json()

        if response.status_code == 200 and "rates" in data:
            return data["rates"].get(exchanged_currency)
        else:
            raise ProviderAPIError(f"ExchangeRate error: {data}")