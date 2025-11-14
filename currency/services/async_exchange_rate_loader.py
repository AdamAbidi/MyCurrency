from typing import Iterable, Dict, List, Optional

from currency.models import CurrencyExchangeRate, Currency
from provider.adapter_registry import get_adapter_class

import asyncio
from datetime import timedelta, date
from asgiref.sync import sync_to_async
import logging

from provider.models import Provider

logger = logging.getLogger(__name__)

@sync_to_async
def get_existing_rate(
    source_currency: Currency,
    target_currency: Currency,
    rate_date: date
) -> Optional[CurrencyExchangeRate]:
    """
    Return an existing exchange rate from the DB, or None if not found.
    """
    try:
        return CurrencyExchangeRate.objects.get(
            source_currency=source_currency,
            exchanged_currency=target_currency,
            valuation_date=rate_date
        )
    except CurrencyExchangeRate.DoesNotExist:
        return None


@sync_to_async
def save_rate_in_db(
    source_currency: Currency,
    target_currency: Currency,
    rate_date: date,
    rate: float
) -> CurrencyExchangeRate:
    """
    Persist a newly fetched exchange rate to the database.
    """
    return CurrencyExchangeRate.objects.create(
        source_currency=source_currency,
        exchanged_currency=target_currency,
        valuation_date=rate_date,
        rate_value=rate,
    )


async def get_exchange_rate_async(
    source_currency: Currency,
    target_currency: Currency,
    date: date,
    providers: Iterable[Provider],
) -> Dict[str, object]:
    """
        Async version of get_exchange_rate for a single target.

        Returns:
            Dict with keys: source_currency, target_currency, date, rate.
    """
    if source_currency == target_currency:
        return {
            "source_currency": source_currency.code,
            "target_currency": target_currency.code,
            "date": date.isoformat(),
            "rate": 1.0,
        }

    existing = await get_existing_rate(source_currency, target_currency, date)
    if existing:
        return {
            "source_currency": source_currency.code,
            "target_currency": target_currency.code,
            "date": date.isoformat(),
            "rate": float(existing.rate_value),
        }

    for provider in providers:
        logger.info(
            f"Trying provider: {provider.name} ({provider.adapter_key}) for {source_currency.code} to {target_currency.code} on {date}")

        adapter_class = get_adapter_class(provider.adapter_key)
        adapter = adapter_class(provider)
        if not adapter_class:
            logger.warning(f"No adapter registered for key '{provider.adapter_key}'")
            continue

        try:
            rate = adapter.get_exchange_rate_data(
                source_currency.code, target_currency.code, date
            )
            if rate is None:
                raise ValueError("Provider returned no rate")

            await save_rate_in_db(source_currency, target_currency, date, rate)

            return {
                "source_currency": source_currency.code,
                "target_currency": target_currency.code,
                "date": date.isoformat(),
                "rate": float(rate),
            }

        except (ValueError, LookupError) as e:
            logger.warning(
                f"{provider.name} failed for {source_currency.code} → {target_currency.code} on {date}: {e}"
            )
            continue  # try next provider

    return {
        "source_currency": source_currency.code,
        "target_currency": target_currency.code,
        "date": date.isoformat(),
        "rate": None,
    }


async def get_exchange_rate_single_date_list_async(
    source_currency: Currency,
    target_list: Iterable[Currency],
    date: date,
    providers: Iterable[Provider],
) -> List[Dict[str, object]]:
    """
        Async helper to compute rates for all targets on a single date.
    """
    tasks = []

    for target_currency in target_list:
        task = get_exchange_rate_async(source_currency, target_currency, date, providers)
        tasks.append(task)

    return await asyncio.gather(*tasks)


async def get_exchange_rate_date_range_async(
    source_currency: Currency,
    target_list: Iterable[Currency],
    start_date: date,
    end_date: date,
    providers: Iterable[Provider],
) -> List[Dict[str, object]]:
    """
        Async helper to compute rates for a date range and multiple targets.
    """

    result = []
    current_date = start_date

    while current_date <= end_date:
        day_rates = await get_exchange_rate_single_date_list_async(
            source_currency, target_list, current_date, providers
        )
        result.extend(day_rates)
        current_date += timedelta(days=1)

    return result
