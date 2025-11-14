from rest_framework.routers import DefaultRouter

# import both viewsets
from currency.views import CurrencyViewSet, CurrencyExchangeRateViewSet
from provider.views import ProviderViewSet

router = DefaultRouter()
router.register(r'currencies', CurrencyViewSet)
router.register(r'exchange-rates', CurrencyExchangeRateViewSet)
router.register(r'providers', ProviderViewSet)

urlpatterns = router.urls