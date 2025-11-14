from currency.admin_views import currency_converter_view

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


urlpatterns = [
    path('admin/converter/', currency_converter_view, name='currency-converter'),
    path('admin/', admin.site.urls),
    path('api/v1/', include('mysite.api_urls')),
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
