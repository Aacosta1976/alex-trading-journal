"""
Servicio de Backtesting.
Actualizado para los campos del modelo Trade v2.
"""

import json
from apps.trades.models import Trade
from apps.dashboard.services import compute_metrics
from apps.backtesting.models import Backtest

WINNER_OUTCOMES = {"maximum_profit", "great_exit", "good_exit"}
LOSER_OUTCOMES  = {"stop_loss", "winning_turned_loser"}


def run_backtest(user, name: str, symbol: str, setup: str,
                 date_from, date_to, initial_balance: float, risk_pct: float) -> tuple:

    if not (0.01 <= risk_pct <= 10):
        return False, "El riesgo debe estar entre 0.01% y 10%.", None
    if initial_balance <= 0:
        return False, "El balance inicial debe ser positivo.", None
    if date_from >= date_to:
        return False, "La fecha inicio debe ser anterior a la fecha fin.", None

    # ── Obtener trades del período ────────────────────────────────────────
    qs = Trade.objects.filter(
        user=user, symbol=symbol,
        entry_date__range=(date_from, date_to),
    ).order_by("entry_date", "entry_time")

    if setup:
        qs = qs.filter(setup_grade=setup)

    raw_trades = list(qs.values(
        "id", "symbol", "entry_date", "outcome", "net_pnl",
        "actual_rr", "max_rr_reached", "risk_pct", "sl_pips",
        "session", "bias", "entry_timeframe", "setup_grade",
        "news_impact", "mistakes", "status",
        "trading_model__name", "account__initial_balance",
    ))

    if not raw_trades:
        return False, "No hay trades con esos criterios en el período seleccionado.", None

    # ── Simular con risk_pct dinámico ─────────────────────────────────────
    risk_decimal = risk_pct / 100
    simulated    = _simulate(raw_trades, initial_balance, risk_decimal)

    # ── Calcular métricas ─────────────────────────────────────────────────
    metrics = compute_metrics(simulated)
    monthly = _monthly_breakdown(simulated)

    results = {
        "name":            name,
        "symbol":          symbol,
        "setup":           setup or "Todos",
        "date_from":       str(date_from),
        "date_to":         str(date_to),
        "initial_balance": initial_balance,
        "risk_pct":        risk_pct,
        "total_trades":    len(simulated),
        "metrics":         metrics,
        "monthly":         monthly,
    }

    # ── Guardar en BD ─────────────────────────────────────────────────────
    Backtest.objects.create(
        user=user, name=name, symbol=symbol,
        date_from=date_from, date_to=date_to,
        initial_balance=initial_balance, risk_pct=risk_pct,
        results_json=json.dumps(results),
    )

    msg = f"Backtest completado: {len(simulated)} trades analizados. P&L: ${metrics['gross_pnl']:+.2f}"
    return True, msg, results


def _simulate(trades: list, initial: float, risk: float) -> list:
    balance   = initial
    simulated = []
    for t in trades:
        sim      = dict(t)
        usd_risk = balance * risk
        outcome  = t.get("outcome", "")
        rr       = float(t.get("actual_rr") or 1.0)

        if outcome in WINNER_OUTCOMES:
            pnl = usd_risk * rr
        elif outcome in LOSER_OUTCOMES:
            pnl = -usd_risk
        else:
            pnl = 0.0

        sim["net_pnl"]             = round(pnl, 2)
        sim["account__initial_balance"] = round(balance, 2)
        balance += pnl
        simulated.append(sim)
    return simulated


def _monthly_breakdown(trades: list) -> list:
    monthly: dict = {}
    for t in trades:
        month = str(t.get("entry_date", ""))[:7] or "N/A"
        if month not in monthly:
            monthly[month] = {"month": month, "total": 0, "wins": 0, "losses": 0, "pnl": 0.0}
        monthly[month]["total"] += 1
        outcome = t.get("outcome", "")
        if outcome in WINNER_OUTCOMES: monthly[month]["wins"]   += 1
        if outcome in LOSER_OUTCOMES:  monthly[month]["losses"] += 1
        monthly[month]["pnl"] += float(t.get("net_pnl") or 0)

    for v in monthly.values():
        v["win_rate"] = round(v["wins"] / v["total"] * 100, 1) if v["total"] else 0
        v["pnl"]      = round(v["pnl"], 2)

    return sorted(monthly.values(), key=lambda x: x["month"])
