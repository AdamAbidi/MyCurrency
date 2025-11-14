from currency.models import Currency

from django.shortcuts import render
import requests

def currency_converter_view(request):
    # Load all available currencies to populate the dropdowns in the form
    context = {"currencies": Currency.objects.all()}

    if request.method == "POST":
        try:
            source_code, target_codes, amount = parse_conversion_form(request)
        except ValueError:
            context["error"] = "Invalid amount format."
            return render(request, "admin/converter.html", context)

        context["converted"] = convert_currency_api_call(source_code, target_codes, amount)
    return render(request, "admin/converter.html", context)


def parse_conversion_form(request):
    # Extract request parameters
    source = request.POST.get("source_currency")
    targets = ','.join(request.POST.getlist("target_currencies"))
    amount_raw = request.POST.get("amount", 0)

    # Validate amount
    try:
        amount = float(amount_raw)
    except ValueError:
        raise ValueError("Invalid amount format.")

    return source, targets, amount


def convert_currency_api_call(source_code, target_codes, amount):
    try:
        # Make http request to our API convert multiple currencies
        response = requests.get(
            "http://localhost:8000/api/v1/exchange-rates/convert-multi/",
            params={
                "source_currency": source_code,
                "target_currencies": target_codes,
                "amount": amount,
            }
        )
        data = response.json()

        if response.status_code == 200:
            return {
                "source_currency": data.get("source_currency"),
                "rates": data.get("results"),
                "amount": data.get("amount"),
                "date": data.get("date")
            }
        else:
            return {
                "error": data.get("error", "Unknown error")
            }

    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {str(e)}"}

    except ValueError as e:
        return {"error": f"Invalid response: {str(e)}"}
