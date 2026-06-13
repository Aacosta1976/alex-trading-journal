"""
Vistas del System — gestión de cuentas y modelos de trading.
Replica la página System del Notion con la tabla de accounts.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from apps.trades.models import Account, TradingModel, Trade
from apps.trades.forms import AccountForm, TradingModelForm


class SystemView(LoginRequiredMixin, TemplateView):
    """
    Página System: resumen de todas las cuentas y modelos,
    con métricas por cuenta (estilo Notion).
    """
    template_name = "system/index.html"

    def get_context_data(self, **kwargs):
        ctx  = super().get_context_data(**kwargs)
        user = self.request.user

        accounts = Account.objects.filter(user=user).prefetch_related("trades")
        models   = TradingModel.objects.filter(user=user)

        # Enriquecer cuentas con estadísticas
        enriched_accounts = []
        for acc in accounts:
            trades = acc.trades.all()
            total  = trades.count()
            winner_outcomes = {"maximum_profit", "great_exit", "good_exit"}
            wins   = trades.filter(outcome__in=winner_outcomes).count()
            wr     = round(wins / total * 100, 1) if total else 0

            enriched_accounts.append({
                "account":       acc,
                "total_trades":  total,
                "win_rate":      wr,
                "net_pnl":       acc.net_pnl,
                "current_balance": acc.current_balance,
                "goal_pct":      acc.goal_progress_pct,
                "goal_bar":      acc.goal_progress_bar,
            })

        ctx["enriched_accounts"] = enriched_accounts
        ctx["trading_models"]    = models
        ctx["account_form"]      = AccountForm()
        ctx["model_form"]        = TradingModelForm()
        return ctx


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    model         = Account
    form_class    = AccountForm
    template_name = "system/account_edit.html"
    success_url   = reverse_lazy("system:index")

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)


class AccountDeleteView(LoginRequiredMixin, DeleteView):
    model         = Account
    template_name = "system/account_confirm_delete.html"
    success_url   = reverse_lazy("system:index")

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)


class TradingModelUpdateView(LoginRequiredMixin, UpdateView):
    model         = TradingModel
    form_class    = TradingModelForm
    template_name = "system/model_edit.html"
    success_url   = reverse_lazy("system:index")

    def get_queryset(self):
        return TradingModel.objects.filter(user=self.request.user)


class TradingModelDeleteView(LoginRequiredMixin, DeleteView):
    model         = TradingModel
    template_name = "system/model_confirm_delete.html"
    success_url   = reverse_lazy("system:index")

    def get_queryset(self):
        return TradingModel.objects.filter(user=self.request.user)
