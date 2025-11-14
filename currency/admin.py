from django.contrib import admin

# Register your models here.
from .models import Currency, CurrencyExchangeRate

admin.site.register(Currency)
admin.site.register(CurrencyExchangeRate)
