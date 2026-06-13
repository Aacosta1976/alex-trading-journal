"""Modelo de Backtest."""
from django.db import models
from django.conf import settings


class Backtest(models.Model):
    """Resultado de una simulación de backtesting."""

    user            = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="backtests")
    name            = models.CharField(max_length=100, verbose_name="Nombre")
    symbol          = models.CharField(max_length=20,  verbose_name="Símbolo")
    setup           = models.CharField(max_length=5,   blank=True, verbose_name="Setup")
    date_from       = models.DateField(verbose_name="Fecha inicio")
    date_to         = models.DateField(verbose_name="Fecha fin")
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Balance inicial")
    risk_pct        = models.DecimalField(max_digits=5,  decimal_places=2, verbose_name="Riesgo (%)")
    results_json    = models.TextField(blank=True, verbose_name="Resultados JSON")
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Backtest"
        verbose_name_plural = "Backtests"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.symbol} ({self.date_from} → {self.date_to})"
