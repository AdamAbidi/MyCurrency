from datetime import datetime, date
from typing import Tuple, List

from currency.models import Currency


def validate_convert_params(
    source_currency_code: str,
    target_currency_codes: List[str],
    amount: str,
) -> Tuple[Currency, List[Currency], float]:
    """
    Validates and parses parameters for currency conversion.
    Returns source_currency, target_currency, amount (float)
    """
    # Check for missing parameters
    if not source_currency_code or not target_currency_codes or not amount:
        raise ValueError("Missing source_currency, target_currencies, amount parameters.")

    # Validate the amount to convert
    try:
        amount = float(amount)
    except ValueError:
        raise ValueError("Invalid amount format.")

    # Check the currencies exist in DB
    try:
        source_currency = Currency.objects.get(code=source_currency_code.upper())
        target_currencies = Currency.objects.filter(code__in=[code.upper() for code in target_currency_codes])

    except Currency.DoesNotExist:
        raise ValueError("Invalid currency code.")

    return source_currency, target_currencies, amount


def validate_get_exchange_rates_history_params(
    source_currency_code: str,
    start_date_str: str,
    end_date_str: str,
) -> Tuple[Currency, List[Currency], date, date]:
    """
    Validates and parses parameters for historical rate loading.
    Returns source_currency, start_date, end_date.
    """
    # Check for missing parameters
    if not source_currency_code or not start_date_str or not end_date_str:
        raise ValueError("Missing source_currency, start_date, or end_date.")

    # Validate both dates format
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.")

    # Validate start date is before end date
    if start_date > end_date:
        raise ValueError("start_date must be before or equal to end_date.")

    # Check the source currency exists in DB
    try:
        source_currency = Currency.objects.get(code=source_currency_code.upper())
    except Currency.DoesNotExist:
        raise ValueError(f"Currency '{source_currency_code}' not found.")

    target_currencies = Currency.objects.exclude(code=source_currency_code.upper())
    return source_currency, list(target_currencies), start_date, end_date
