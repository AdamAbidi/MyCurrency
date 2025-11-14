from typing import Iterable, List

from currency.models import CurrencyExchangeRate, Currency
from provider.adapter_registry import get_adapter_class

from datetime import timedelta, date
import logging

from provider.exceptions import ProviderAPIError
from provider.models import Provider

logger = logging.getLogger(__name__)


def get_exchange_rate_date_range(
    source_currency: Currency,
    target_list: Iterable[Currency],
    start_date: date,
    end_date: date,
    providers: Iterable[Provider],
) -> List[dict]:

    """
    Get exchange rates for a source currency to multiple target currencies
    over a date range. Returns a list of daily rate entries for each currency.
    """

    exchange_rate_date_range = []

    # Start loop from the start date to the end date
    current_date = start_date
    while current_date <= end_date:
        # Get the exchange rate for current_date
        exchange_rate_date = get_exchange_rate_single_date_list(source_currency, target_list, current_date, providers)

        # Add rate to output data
        exchange_rate_date_range.extend(exchange_rate_date)

        # Move to the next day
        current_date += timedelta(days=1)

    return exchange_rate_date_range



def get_exchange_rate_single_date_list(
    source_currency: Currency,
    target_list: Iterable[Currency],
    single_date: date,
    providers: Iterable[Provider],
) -> List[dict]:
    """
    Get exchange rates for a single date between the source currency and
    each target currency. Returns a list of entries for that date.
    """

    result = []
    for target_currency in target_list:
        # Get the exchange rate for current_date
        rate = get_exchange_rate(source_currency, target_currency, single_date, providers)

        entry = {
            "source_currency": source_currency.code,
            "target_currency": target_currency.code,
            "date": single_date.isoformat(),
            "rate": rate
        }

        # Append the entry to the results list
        result.append(entry)

    return result



def get_exchange_rate(
    source_currency: Currency,
    target_currency: Currency,
    date: date,
    providers: Iterable[Provider],
) -> float:
    """
    Get a single exchange rate based on a source currency and target currency and a date.
    - First checks the database.
    - If not found, attempts to get from available providers in order of priority.
    """

    # If source and target currencies are the same, return a fixed rate of 1.0
    if source_currency == target_currency:
        return 1.0

    # Try to get the exchange rate from the database
    try:
        rate = CurrencyExchangeRate.objects.get(
            source_currency=source_currency,
            exchanged_currency=target_currency,
            valuation_date=date
        ).rate_value
        logger.info(f"Rate found in DB for {source_currency.code} to {target_currency.code} on {date}: {rate}")
        return rate
    except CurrencyExchangeRate.DoesNotExist:

        # If not found, loop through the available providers by priority
        for provider in providers:
            logger.info(f"Trying provider: {provider.name} ({provider.adapter_key}) for {source_currency.code} to {target_currency.code} on {date}")
            try:
                return get_exchange_rate_from_provider(
                    source_currency, target_currency, date, provider
                )
            except (ProviderAPIError,LookupError, ValueError) as e:
                logger.warning(f"{provider.name} failed to get rate for {source_currency.code} → {target_currency.code} on {date}: {e}")
                continue  # try the next provider

        raise LookupError(
            f"No provider could return a rate for {source_currency.code} → {target_currency.code} on {date}")



def get_exchange_rate_from_provider(
    source_currency: Currency,
    target_currency: Currency,
    date: date,
    provider: Provider,
) ->  float:
    """
    Uses a specific provider's adapter to get the exchange rate.
    - Saves the rate to the database.
    - Returns rate.
    """

    # Get the adapter class from the registry using the provider adapter key
    adapter_class = get_adapter_class(provider.adapter_key)
    if not adapter_class:
        raise LookupError(f"No adapter registered for key '{provider.adapter_key}'")
    adapter = adapter_class(provider=provider)

    # Use the adapter to get the exchange rate from the external API
    rate = adapter.get_exchange_rate_data(source_currency.code, target_currency.code, date)
    if rate is None:
        raise ValueError("Provider returned no rate")

    # Save the new rate to the database for future use
    CurrencyExchangeRate.objects.create(
        source_currency=source_currency,
        exchanged_currency=target_currency,
        valuation_date=date,
        rate_value=rate
    )

    logger.info(f"Provider {provider.name} succeeded.")
    logger.debug(f"Found and saved rate {rate} for {source_currency.code} to {target_currency.code} from {provider.name}")

    return rate