from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.viewsets import ReadOnlyModelViewSet

from currency.models import CurrencyExchangeRate, Currency
from currency.serializers import CurrencyExchangeRateSerializer, CurrencySerializer
from currency.services.async_exchange_rate_loader import get_exchange_rate_date_range_async
from currency.services.exchange_rate_loader import get_exchange_rate_date_range, get_exchange_rate, \
    get_exchange_rate_single_date_list
from currency.validators import validate_convert_params, validate_get_exchange_rates_history_params
from provider.models import Provider

import asyncio
from rest_framework.decorators import action
from rest_framework import viewsets
from datetime import date
from rest_framework.request import Request
from rest_framework.response import Response


class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer

class CurrencyExchangeRateViewSet(ReadOnlyModelViewSet):
    queryset = (
        CurrencyExchangeRate.objects
        .select_related('source_currency', 'exchanged_currency')
        .order_by('-valuation_date')
    )
    serializer_class = CurrencyExchangeRateSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name='source_currency', type=str),
            OpenApiParameter(name='start_date', type=date),
            OpenApiParameter(name='end_date', type=date),
        ],
    )
    @action(detail=False, methods=['get'], url_path='history')
    def get_exchange_rates(self, request: Request) -> Response:
        try:
            # Extract query parameters from the request
            source_currency = request.query_params.get('source_currency')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            # Validate and parse input parameters
            source_currency, target_list, start_date, end_date = validate_get_exchange_rates_history_params(source_currency,start_date, end_date)

            # Get a list of active providers, ordered by priority
            providers = list(Provider.objects.filter(is_active=True).order_by('priority'))

            # Build the exchange rate response for each target and date
            response_data = get_exchange_rate_date_range(source_currency, target_list, start_date, end_date, providers)

        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        except (LookupError, RuntimeError) as e:
            return Response({'error': str(e)}, status=502)

        return Response(response_data, status=200)



    @extend_schema(
        parameters=[
            OpenApiParameter(name='source_currency', type=str),
            OpenApiParameter(name='target_currency', type=str),
            OpenApiParameter(name='amount', type=float),
        ],
    )
    @action(detail=False, methods=['get'], url_path='convert')
    def convert_currency(self, request: Request) -> Response:
        try:
            # Extract query parameters from the request
            source_code = request.query_params.get('source_currency')
            target_code = request.query_params.get('target_currency')
            amount = request.query_params.get('amount')

            # Validate input parameters
            source_currency, [target_currency], amount = validate_convert_params(source_code, [target_code], amount)

            # Get today date
            date_val = date.today()

            # Extract all active providers ordered by priority
            providers = list(Provider.objects.filter(is_active=True).order_by('priority'))

            # Get today rate
            rate = get_exchange_rate(source_currency, target_currency, date_val, providers)

            # Calculate the converted amount
            converted_amount = round( float(rate) * amount, 4)

        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        except (LookupError, RuntimeError) as e:
            return Response({'error': str(e)}, status=502)

        return Response({
            "source_currency": source_currency.code,
            "target_currency": target_currency.code,
            "amount": amount,
            "rate": float(rate),
            "converted_amount": converted_amount,
            "date": date_val.isoformat()
        }, status=200)



    @extend_schema(
        parameters=[
            OpenApiParameter(name='source_currency', type=str),
            OpenApiParameter(name='target_currencies', type=str),
            OpenApiParameter(name='amount', type=float),
        ],
    )
    @action(detail=False, methods=['get'], url_path='convert-multi')
    def convert_currencies(self, request: Request) -> Response:
        try:
            # Extract query parameters from the request
            source_code = request.query_params.get('source_currency')
            target_codes = request.query_params.get('target_currencies').split(',')
            amount = request.query_params.get('amount')

            # Validate input parameters
            source_currency, target_currencies, amount = validate_convert_params(source_code, target_codes, amount)

            # Get today date
            date_val = date.today()

            # Extract all active providers ordered by priority
            providers = list(Provider.objects.filter(is_active=True).order_by('priority'))

            # Get converted amounts by currencies
            rates_data = get_exchange_rate_single_date_list(source_currency, target_currencies, date_val, providers)

        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        except (LookupError, RuntimeError) as e:
            return Response({'error': str(e)}, status=502)

        # Build response data
        response_data = []
        for rate_data in rates_data:
            response_data.append({
                "target_currency": rate_data["target_currency"],
                "rate": rate_data["rate"],
                "converted_amount": round(float(rate_data["rate"]) * amount, 4),
            })

        return Response({
            "source_currency": source_currency.code,
            "results": response_data,
            "amount": amount,
            "date": date_val.isoformat()
        }, status=200)



    @extend_schema(
        parameters=[
            OpenApiParameter(name='source_currency', type=str),
            OpenApiParameter(name='start_date', type=date),
            OpenApiParameter(name='end_date', type=date),
        ],
    )
    @action(detail=False, methods=['get'], url_path='history-async')
    def get_exchange_rates_async(self, request: Request) -> Response:
        """
        Triggers the async task to load historical exchange rates asynchronously.
        """
        try:
            # Extract query parameters from the request
            source_currency = request.query_params.get('source_currency')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')

            # Validate input parameters
            source_currency, target_list, start_date, end_date = validate_get_exchange_rates_history_params(source_currency, start_date, end_date)

            # Get all active providers ordered by priority
            providers = list(Provider.objects.filter(is_active=True).order_by('priority'))

            # Get historic exchange rate data asynchronously
            results =  asyncio.run( get_exchange_rate_date_range_async(
                source_currency,
                list(target_list),
                start_date,
                end_date,
                list(providers)
            ))

            return Response(results, status=200)

        except ValueError as e:
            return Response({"error": str(e)}, status=400)