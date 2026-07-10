"""Vistas del dashboard principal con métricas y gráficos."""

import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from apps.trades.models import Trade, Account
from apps.dashboard.services import compute_metrics


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        ctx      = super().get_context_data(**kwargs)
        user     = self.request.user
        trades_qs = Trade.objects.filter(user=user).order_by("entry_date", "entry_time")

        # Filtro opcional por cuenta
        account_id = self.request.GET.get("account")
        if account_id:
            trades_qs = trades_qs.filter(account_id=account_id)

        trades  = list(trades_qs.values(
            "id", "symbol", "entry_date", "outcome", "net_pnl",
            "actual_rr", "max_rr_reached", "risk_pct", "sl_pips",
            "session", "bias", "entry_timeframe", "setup_grade",
            "news_impact", "mistakes", "status", "is_backtest",
            "position",
            "trading_model__name", "account__initial_balance",
        ))
        metrics = compute_metrics(trades)

        # ── Datos para Chart.js ───────────────────────────────────────────
        equity     = metrics["equity_curve"]
        eq_labels  = [str(e["index"])   for e in equity]
        eq_balance = [e["balance"]      for e in equity]
        eq_dd      = [e["drawdown_pct"] for e in equity]

        # Model W/L
        model_stats = metrics["model_stats"]
        s_labels    = list(model_stats.keys())
        s_wins      = [v["wins"]   for v in model_stats.values()]
        s_losses    = [v["losses"] for v in model_stats.values()]
        s_flats     = [v["breakevens"] for v in model_stats.values()]

        # Symbol P&L
        sym_stats  = metrics["symbol_stats"]
        sym_labels = list(sym_stats.keys())
        sym_pnl    = [v["pnl"]      for v in sym_stats.values()]
        sym_wr     = [v["win_rate"] for v in sym_stats.values()]

        # Win/Loss/Flat pie
        wlf_data = [metrics["total_wins"], metrics["total_losses"], metrics["total_breakevens"]]

        # Errores
        err_stats  = metrics["mistake_stats"]
        err_labels = list(err_stats.keys())[:8]
        err_counts = list(err_stats.values())[:8]

        # P&L mensual
        monthly    = metrics["monthly_pnl"]
        mon_labels = [m["month"] for m in monthly]
        mon_pnl    = [m["pnl"]   for m in monthly]

        charts = {
            "eq_labels":   eq_labels,
            "eq_balance":  eq_balance,
            "eq_dd":       eq_dd,
            "s_labels":    s_labels,
            "s_wins":      s_wins,
            "s_losses":    s_losses,
            "s_flats":     s_flats,
            "sym_labels":  sym_labels,
            "sym_pnl":     sym_pnl,
            "sym_wr":      sym_wr,
            "wlf_data":    wlf_data,
            "err_labels":  err_labels,
            "err_counts":  err_counts,
            "mon_labels":  mon_labels,
            "mon_pnl":     mon_pnl,
        }

        ctx["metrics"]          = metrics
        ctx["charts_json"]      = json.dumps(charts)
        ctx["accounts"]         = Account.objects.filter(user=user)
        ctx["selected_account"] = account_id

        # NOTA (fix incidencia Dashboard): "recent_trades" viene de un .values(),
        # es decir son diccionarios, no instancias de Trade, por lo que no tienen
        # los metodos/propiedades del modelo (get_setup_grade_display, is_winner...).
        # Aqui se calcula manualmente el resultado W/L a partir de "outcome".
        WIN_OUTCOMES  = ("maximum_profit", "great_exit", "good_exit", "partial_win")
        LOSS_OUTCOMES = ("stop_loss", "winning_turned_loser")
        recent = list(reversed(trades))[:10]
        for t in recent:
            if t["outcome"] in WIN_OUTCOMES:
                t["wl"] = "W"
            elif t["outcome"] in LOSS_OUTCOMES:
                t["wl"] = "L"
            else:
                t["wl"] = "—"
        ctx["recent_trades"] = recent
        return ctx