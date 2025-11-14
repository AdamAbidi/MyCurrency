import random
from datetime import date

from .base import BaseProviderAdapter

class MockExchangeRateAdapter(BaseProviderAdapter):
    def get_exchange_rate_data(
            self,
            source_currency: str,
            exchanged_currency: str,
            date_value: date,
    ) -> float:
        """
            Return a random rate for testing purposes.
        """
        return round(random.uniform(0.5, 1.5), 4)