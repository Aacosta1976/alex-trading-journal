"""URLs de reportes."""
from django.urls import path
from apps.reports import views

app_name = "reports"

urlpatterns = [
    path("excel/", views.ExportExcelView.as_view(), name="excel"),
    path("pdf/",   views.ExportPDFView.as_view(),   name="pdf"),
]
