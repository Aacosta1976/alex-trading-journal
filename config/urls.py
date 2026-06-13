"""URLs principales del proyecto Trading Journal v2."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/",          admin.site.urls),
    path("",                include("apps.dashboard.urls")),
    path("journal/",        include("apps.trades.urls",      namespace="trades")),
    path("backtesting/",    include("apps.backtesting.urls", namespace="backtesting")),
    path("chart/",          include("apps.chart.urls",       namespace="chart")),
    path("system/",         include("apps.system.urls",      namespace="system")),
    path("reports/",        include("apps.reports.urls",     namespace="reports")),
    path("auth/",           include("apps.authentication.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
