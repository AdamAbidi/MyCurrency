from decouple import config

class BaseProviderAdapter:
    def __init__(self, provider):
        self.provider = provider
        self.api_key = self.load_api_key()

    def load_api_key(self):
        env_var = f"{self.provider.adapter_key.upper()}_API_KEY"
        return config(env_var)

    def get_exchange_rate_data(self, source_currency, exchanged_currency, date):
        raise NotImplementedError

    async def async_get_exchange_rate_data(self, source_currency, exchanged_currency, date):
        # Default sync fallback
        return self.get_exchange_rate_data(source_currency, exchanged_currency, date)