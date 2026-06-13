"""
Vistas de Chart — análisis estadístico de trades.
Replica las secciones del Notion:
- Profitability Analysis
- Win Rate Breakdown
- Risk & Reward Analysis
- Trades Count Overview
"""

import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from apps.trades.models import Trade, Account, TradingModel
from apps.dashboard.services import compute_metrics


class ChartView(LoginRequiredMixin, TemplateView):
    template_name = "chart/index.html"

    def get_context_data(self, **kwargs):
        ctx  = super().get_context_data(**kwargs)
        user = self.request.user

        qs = Trade.objects.filter(user=user).select_related(
            "account", "trading_model"
        ).order_by("entry_date", "entry_time")

        # Filtros
        account_id = self.request.GET.get("account", "")
        model_id   = self.request.GET.get("model", "")
        period     = self.request.GET.get("period", "")  # "this_month", "this_year"

        if account_id:
            qs = qs.filter(account_id=account_id)
        if model_id:
            qs = qs.filter(trading_model_id=model_id)
        if period == "this_month":
            from django.utils import timezone
            now = timezone.now()
            qs  = qs.filter(entry_date__year=now.year, entry_date__month=now.month)
        elif period == "this_year":
            from django.utils import timezone
            qs  = qs.filter(entry_date__year=timezone.now().year)

        trades  = list(qs.values(
            "id", "symbol", "entry_date", "outcome", "net_pnl",
            "actual_rr", "max_rr_reached", "risk_pct", "sl_pips",
            "session", "bias", "entry_timeframe", "setup_grade",
            "news_impact", "mistakes", "status",
            "trading_model__name", "account__initial_balance",
        ))
        metrics = compute_metrics(trades)

        # ── Datos para Chart.js ───────────────────────────────────────────

        # 1. Equity curve
        equity     = metrics["equity_curve"]
        eq_labels  = [e["date"] or str(e["index"]) for e in equity]
        eq_balance = [e["balance"]      for e in equity]
        eq_dd      = [e["drawdown_pct"] for e in equity]

        # 2. Profitability by Model
        model_stats  = metrics["model_stats"]
        model_labels = list(model_stats.keys())
        model_wins   = [v["wins"]   for v in model_stats.values()]
        model_losses = [v["losses"] for v in model_stats.values()]
        model_pnl    = [metrics["model_pnl"].get(k, 0) for k in model_labels]

        # 3. Win Rate by Session
        sess_stats   = metrics["session_stats"]
        sess_labels  = list(sess_stats.keys())
        sess_wr      = [v["win_rate"] for v in sess_stats.values()]
        sess_total   = [v["total"]    for v in sess_stats.values()]

        # 4. Win Rate by Symbol
        sym_stats    = metrics["symbol_stats"]
        sym_labels   = list(sym_stats.keys())
        sym_wr       = [v["win_rate"] for v in sym_stats.values()]
        sym_pnl      = [v["pnl"]     for v in sym_stats.values()]

        # 5. Outcomes pie
        outcome_stats  = metrics["outcome_stats"]
        outcome_labels = list(outcome_stats.keys())
        outcome_counts = list(outcome_stats.values())

        # 6. Mistakes frequency
        mistake_stats  = metrics["mistake_stats"]
        mistake_labels = list(mistake_stats.keys())[:8]
        mistake_counts = list(mistake_stats.values())[:8]

        # 7. Risk & Reward by Model
        rr_by_model = {
            k: round(
                sum(float(t["actual_rr"] or 0) for t in trades
                    if str(t.get("trading_model__name") or "") == k) /
                max(1, sum(1 for t in trades
                           if str(t.get("trading_model__name") or "") == k)),
                2
            )
            for k in model_labels
        }

        # 8. Setup Grade breakdown
        grade_stats  = metrics["grade_stats"]
        grade_labels = list(grade_stats.keys())
        grade_wr     = [v["win_rate"] for v in grade_stats.values()]
        grade_total  = [v["total"]    for v in grade_stats.values()]

        # 9. Monthly P&L
        monthly     = metrics["monthly_pnl"]
        mon_labels  = [m["month"]   for m in monthly]
        mon_pnl     = [m["pnl"]     for m in monthly]
        mon_wr      = [m["win_rate"]for m in monthly]

        # 10. Bias breakdown
        bias_stats   = metrics["bias_stats"]
        bias_labels  = list(bias_stats.keys())
        bias_wr      = [v["win_rate"] for v in bias_stats.values()]
        bias_total   = [v["total"]    for v in bias_stats.values()]

        charts = {
            "eq_labels":       eq_labels,
            "eq_balance":      eq_balance,
            "eq_dd":           eq_dd,
            "model_labels":    model_labels,
            "model_wins":      model_wins,
            "model_losses":    model_losses,
            "model_pnl":       model_pnl,
            "sess_labels":     sess_labels,
            "sess_wr":         sess_wr,
            "sess_total":      sess_total,
            "sym_labels":      sym_labels,
            "sym_wr":          sym_wr,
            "sym_pnl":         sym_pnl,
            "outcome_labels":  outcome_labels,
            "outcome_counts":  outcome_counts,
            "mistake_labels":  mistake_labels,
            "mistake_counts":  mistake_counts,
            "rr_by_model":     list(rr_by_model.values()),
            "grade_labels":    grade_labels,
            "grade_wr":        grade_wr,
            "grade_total":     grade_total,
            "mon_labels":      mon_labels,
            "mon_pnl":         mon_pnl,
            "mon_wr":          mon_wr,
            "bias_labels":     bias_labels,
            "bias_wr":         bias_wr,
            "bias_total":      bias_total,
        }

        ctx["metrics"]          = metrics
        ctx["charts_json"]      = json.dumps(charts)
        ctx["accounts"]         = Account.objects.filter(user=user)
        ctx["trading_models"]   = TradingModel.objects.filter(user=user)
        ctx["selected_account"] = account_id
        ctx["selected_model"]   = model_id
        ctx["selected_period"]  = period
        return ctx
