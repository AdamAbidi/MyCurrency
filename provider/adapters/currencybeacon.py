import requests
from datetime import date
from .base import BaseProviderAdapter
from ..exceptions import ProviderAPIError


class CurrencyBeaconAdapter(BaseProviderAdapter):
    def get_exchange_rate_data(
            self,
            source_currency: str,
            exchanged_currency: str,
            date_value: date,
    ) -> float:
        """
            Fetch historical rate from CurrencyBeacon API.

            Raises:
                ProviderAPIError: if the HTTP call fails or response is invalid.
        """
        url = f"{self.provider.api_url}/historical"
        params = {
            "api_key": self.api_key,
            "base": source_currency,
            "symbols": exchanged_currency,
            "date": date_value.strftime('%Y-%m-%d')
        }

        response = requests.get(url, params=params)

        data = response.json()

        if response.status_code == 200 and "rates" in data:
            return data["rates"].get(exchanged_currency)
        else:
            raise ProviderAPIError(f"CurrencyBeacon error: {data}")