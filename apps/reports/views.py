"""Vistas de reportes — exportación Excel y PDF."""

import io
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views import View
from django.utils import timezone

from apps.trades.models import Trade
from apps.dashboard.services import compute_metrics
from apps.reports.excel_exporter import export_excel
from apps.reports.pdf_exporter import export_pdf


class ExportExcelView(LoginRequiredMixin, View):
    """Genera y descarga el diario en formato Excel."""

    def get(self, request):
        trades  = list(Trade.objects.filter(user=request.user)
                       .order_by("entry_date", "entry_time").values())
        metrics = compute_metrics(trades)
        content = export_excel(trades, metrics, request.user.username)
        filename = f"trading_journal_{timezone.now().strftime('%Y%m%d')}.xlsx"

        response = HttpResponse(
            content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ExportPDFView(LoginRequiredMixin, View):
    """Genera y descarga el reporte en formato PDF."""

    def get(self, request):
        trades  = list(Trade.objects.filter(user=request.user)
                       .order_by("entry_date", "entry_time").values())
        metrics = compute_metrics(trades)
        content = export_pdf(trades, metrics, request.user.username)
        filename = f"trading_report_{timezone.now().strftime('%Y%m%d')}.pdf"

        response = HttpResponse(content, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
