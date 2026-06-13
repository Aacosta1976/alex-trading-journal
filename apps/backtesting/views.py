"""Vistas de backtesting."""
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, DeleteView, FormView
from django.urls import reverse_lazy

from apps.backtesting.models import Backtest
from apps.backtesting.services import run_backtest
from apps.backtesting.forms import BacktestForm


class BacktestListView(LoginRequiredMixin, ListView):
    template_name       = "backtesting/list.html"
    context_object_name = "backtests"

    def get_queryset(self):
        return Backtest.objects.filter(user=self.request.user)


class BacktestCreateView(LoginRequiredMixin, FormView):
    template_name = "backtesting/form.html"
    form_class    = BacktestForm
    success_url   = reverse_lazy("backtesting:list")

    def form_valid(self, form):
        d  = form.cleaned_data
        ok, msg, results = run_backtest(
            user=self.request.user,
            name=d["name"], symbol=d["symbol"].upper(), setup=d["setup"],
            date_from=d["date_from"], date_to=d["date_to"],
            initial_balance=float(d["initial_balance"]),
            risk_pct=float(d["risk_pct"]),
        )
        messages.success(self.request, msg) if ok else messages.error(self.request, msg)
        return redirect(self.success_url) if ok else self.form_invalid(form)


class BacktestDetailView(LoginRequiredMixin, DetailView):
    template_name       = "backtesting/detail.html"
    context_object_name = "bt"

    def get_queryset(self):
        return Backtest.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.object.results_json:
            results = json.loads(self.object.results_json)
            ctx["results"]  = results
            ctx["metrics"]  = results.get("metrics", {})
            ctx["monthly"]  = results.get("monthly", [])
            equity = results.get("metrics", {}).get("equity_curve", [])
            ctx["charts_json"] = json.dumps({
                "eq_labels":  [str(e["index"])   for e in equity],
                "eq_balance": [e["balance"]      for e in equity],
                "eq_dd":      [e["drawdown_pct"] for e in equity],
                "mon_labels": [m["month"] for m in results.get("monthly", [])],
                "mon_pnl":    [m["pnl"]   for m in results.get("monthly", [])],
            })
        return ctx


class BacktestDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "backtesting/confirm_delete.html"
    success_url   = reverse_lazy("backtesting:list")

    def get_queryset(self):
        return Backtest.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.warning(self.request, "Backtest eliminado.")
        return super().form_valid(form)
