"""
Servicio de métricas y estadísticas de trading — v3.
Métricas añadidas: Ratio de Sharpe, Ratio de Sortino, Recovery Factor.
Cumple con los requisitos del TFG (OE3).
"""

from __future__ import annotations
import math
import statistics
from typing import Any


def compute_metrics(trades: list[dict]) -> dict[str, Any]:
    """
    Calcula métricas completas a partir de una lista de trades.
    Compatible con los campos del modelo Trade v2 (Notion).
    """
    if not trades:
        return _empty_metrics()

    # ── Clasificar por outcome ─────────────────────────────────────────────
    winners   = [t for t in trades if t.get("outcome") in (
        "maximum_profit", "great_exit", "good_exit"
    )]
    losers    = [t for t in trades if t.get("outcome") in (
        "stop_loss", "winning_turned_loser"
    )]
    breakevens = [t for t in trades if t.get("outcome") in (
        "capital_protected", "winner_to_be"
    )]
    total = len(trades)

    # ── P&L ───────────────────────────────────────────────────────────────
    pnl_vals  = [float(t["net_pnl"]) for t in trades  if t.get("net_pnl") is not None]
    win_pnls  = [float(t["net_pnl"]) for t in winners if t.get("net_pnl") is not None]
    loss_pnls = [float(t["net_pnl"]) for t in losers  if t.get("net_pnl") is not None]

    gross_pnl  = sum(pnl_vals)
    gross_win  = sum(win_pnls)
    gross_loss = sum(loss_pnls)

    # ── Balance ───────────────────────────────────────────────────────────
    initial_balance = 1000.0
    for t in trades:
        if t.get("account__initial_balance"):
            initial_balance = float(t["account__initial_balance"])
            break

    final_balance = initial_balance + gross_pnl
    roe = (gross_pnl / initial_balance * 100) if initial_balance else 0

    # ── Tasas ─────────────────────────────────────────────────────────────
    win_rate   = len(winners) / total if total else 0
    pf         = abs(gross_win / gross_loss) if gross_loss else 0
    avg_win    = statistics.mean(win_pnls)  if win_pnls  else 0
    avg_loss   = statistics.mean(loss_pnls) if loss_pnls else 0
    expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)

    rr_vals     = [float(t["actual_rr"])    for t in trades if t.get("actual_rr")]
    max_rr_vals = [float(t["max_rr_reached"]) for t in trades if t.get("max_rr_reached")]
    avg_rr      = statistics.mean(rr_vals)     if rr_vals     else 0
    avg_max_rr  = statistics.mean(max_rr_vals) if max_rr_vals else 0

    # ── Drawdown ──────────────────────────────────────────────────────────
    max_dd, max_dd_pct = _max_drawdown(trades, initial_balance)

    # ── Rachas ────────────────────────────────────────────────────────────
    max_win_streak  = _max_streak(trades, "winners")
    max_loss_streak = _max_streak(trades, "losers")

    # ── Ratio de Sharpe ───────────────────────────────────────────────────
    # Sharpe = (Rentabilidad media - Tasa libre de riesgo) / Desviación estándar
    # Tasa libre de riesgo = 0 (estándar en trading discrecional)
    # Se calcula sobre los retornos porcentuales por trade
    sharpe_ratio = _sharpe_ratio(pnl_vals, initial_balance)

    # ── Ratio de Sortino ──────────────────────────────────────────────────
    # Sortino = (Rentabilidad media) / Desviación estándar de pérdidas
    # Solo penaliza la volatilidad negativa (pérdidas)
    sortino_ratio = _sortino_ratio(pnl_vals, initial_balance)

    # ── Recovery Factor ───────────────────────────────────────────────────
    # Recovery Factor = Beneficio neto / Maximum Drawdown
    # Valor > 2.0 indica que los beneficios compensan holgadamente las pérdidas
    recovery_factor = round(gross_pnl / max_dd, 2) if max_dd > 0 else 0

    # ── Distribuciones ────────────────────────────────────────────────────
    model_stats   = _group_by(trades, "trading_model__name")
    symbol_stats  = _group_by(trades, "symbol")
    session_stats = _group_by(trades, "session")
    bias_stats    = _group_by(trades, "bias")
    tf_stats      = _group_by(trades, "entry_timeframe")
    outcome_stats = _frequency(trades, "outcome")
    mistake_stats = _mistake_frequency(trades)
    grade_stats   = _group_by(trades, "setup_grade")
    news_stats    = _group_by(trades, "news_impact")

    model_pnl = {
        k: round(sum(float(t["net_pnl"] or 0) for t in trades
                     if str(t.get("trading_model__name") or "") == k), 2)
        for k in model_stats
    }

    equity_curve = _equity_curve(trades, initial_balance)
    monthly_pnl  = _monthly_pnl(trades)

    return {
        # Recuento
        "total_trades":      total,
        "total_wins":        len(winners),
        "total_losses":      len(losers),
        "total_breakevens":  len(breakevens),
        # Tasas
        "win_rate":          round(win_rate * 100, 2),
        "loss_rate":         round(len(losers) / total * 100, 2) if total else 0,
        # P&L
        "gross_pnl":         round(gross_pnl,  2),
        "gross_win":         round(gross_win,  2),
        "gross_loss":        round(gross_loss, 2),
        "avg_win":           round(avg_win,    2),
        "avg_loss":          round(avg_loss,   2),
        "best_trade":        round(max(win_pnls),  2) if win_pnls  else 0,
        "worst_trade":       round(min(loss_pnls), 2) if loss_pnls else 0,
        "expectancy":        round(expectancy, 4),
        # Ratios
        "profit_factor":     round(pf,              2),
        "avg_rr":            round(avg_rr,           2),
        "avg_max_rr":        round(avg_max_rr,       2),
        "sharpe_ratio":      sharpe_ratio,
        "sortino_ratio":     sortino_ratio,
        "recovery_factor":   recovery_factor,
        # Balance
        "initial_balance":   round(initial_balance, 2),
        "final_balance":     round(final_balance,   2),
        "roe":               round(roe,              2),
        # Drawdown
        "max_drawdown":      round(max_dd,           2),
        "max_drawdown_pct":  round(max_dd_pct,       2),
        # Rachas
        "max_win_streak":    max_win_streak,
        "max_loss_streak":   max_loss_streak,
        # Distribuciones
        "model_stats":       model_stats,
        "model_pnl":         model_pnl,
        "symbol_stats":      symbol_stats,
        "session_stats":     session_stats,
        "bias_stats":        bias_stats,
        "tf_stats":          tf_stats,
        "outcome_stats":     outcome_stats,
        "mistake_stats":     mistake_stats,
        "grade_stats":       grade_stats,
        "news_stats":        news_stats,
        # Series temporales
        "equity_curve":      equity_curve,
        "monthly_pnl":       monthly_pnl,
    }


# ── Cálculo de ratios ─────────────────────────────────────────────────────────

def _sharpe_ratio(pnl_vals: list[float], initial_balance: float,
                  risk_free_rate: float = 0.0) -> float:
    """
    Ratio de Sharpe = (Rentabilidad media - Tasa libre de riesgo) / Desviación estándar
    Calculado sobre retornos porcentuales por trade.
    Ref: Sharpe (1966).
    """
    if len(pnl_vals) < 2 or initial_balance <= 0:
        return 0.0
    returns = [p / initial_balance * 100 for p in pnl_vals]
    mean_r  = statistics.mean(returns)
    std_r   = statistics.stdev(returns)
    if std_r == 0:
        return 0.0
    return round((mean_r - risk_free_rate) / std_r, 2)


def _sortino_ratio(pnl_vals: list[float], initial_balance: float,
                   risk_free_rate: float = 0.0) -> float:
    """
    Ratio de Sortino = (Rentabilidad media) / Desviación estándar de pérdidas (downside).
    Solo penaliza la volatilidad negativa, a diferencia del Sharpe.
    Ref: TFG sección 2.1.7.
    """
    if len(pnl_vals) < 2 or initial_balance <= 0:
        return 0.0
    returns      = [p / initial_balance * 100 for p in pnl_vals]
    mean_r       = statistics.mean(returns)
    downside     = [r for r in returns if r < 0]
    if len(downside) < 2:
        return 0.0
    downside_std = statistics.stdev(downside)
    if downside_std == 0:
        return 0.0
    return round((mean_r - risk_free_rate) / downside_std, 2)


# ── Helpers privados ──────────────────────────────────────────────────────────

def _empty_metrics() -> dict[str, Any]:
    base = {k: 0 for k in [
        "total_trades", "total_wins", "total_losses", "total_breakevens",
        "win_rate", "loss_rate", "gross_pnl", "gross_win", "gross_loss",
        "avg_win", "avg_loss", "best_trade", "worst_trade", "expectancy",
        "profit_factor", "avg_rr", "avg_max_rr",
        "sharpe_ratio", "sortino_ratio", "recovery_factor",
        "initial_balance", "final_balance", "roe",
        "max_drawdown", "max_drawdown_pct",
        "max_win_streak", "max_loss_streak",
    ]}
    base.update({
        "model_stats": {}, "model_pnl": {}, "symbol_stats": {},
        "session_stats": {}, "bias_stats": {}, "tf_stats": {},
        "outcome_stats": {}, "mistake_stats": {}, "grade_stats": {},
        "news_stats": {}, "equity_curve": [], "monthly_pnl": [],
    })
    return base


def _max_streak(trades: list[dict], kind: str) -> int:
    winner_outcomes = {"maximum_profit", "great_exit", "good_exit"}
    loser_outcomes  = {"stop_loss", "winning_turned_loser"}
    max_s = current = 0
    for t in trades:
        outcome = t.get("outcome", "")
        hit = outcome in winner_outcomes if kind == "winners" else outcome in loser_outcomes
        if hit:
            current += 1
            max_s = max(max_s, current)
        else:
            current = 0
    return max_s


def _max_drawdown(trades: list[dict], initial: float) -> tuple[float, float]:
    balance = initial
    peak    = initial
    max_dd  = 0.0
    for t in trades:
        balance += float(t.get("net_pnl") or 0)
        if balance > peak:
            peak = balance
        dd = peak - balance
        if dd > max_dd:
            max_dd = dd
    max_dd_pct = (max_dd / peak * 100) if peak > 0 else 0
    return max_dd, max_dd_pct


def _group_by(trades: list[dict], field: str) -> dict[str, dict]:
    winner_outcomes = {"maximum_profit", "great_exit", "good_exit"}
    loser_outcomes  = {"stop_loss", "winning_turned_loser"}
    groups: dict[str, dict] = {}
    for t in trades:
        key = str(t.get(field) or "N/A")
        if key not in groups:
            groups[key] = {"total": 0, "wins": 0, "losses": 0, "breakevens": 0, "pnl": 0.0}
        groups[key]["total"] += 1
        outcome = t.get("outcome", "")
        if outcome in winner_outcomes:
            groups[key]["wins"] += 1
        elif outcome in loser_outcomes:
            groups[key]["losses"] += 1
        else:
            groups[key]["breakevens"] += 1
        groups[key]["pnl"] += float(t.get("net_pnl") or 0)
    for v in groups.values():
        v["win_rate"] = round(v["wins"] / v["total"] * 100, 1) if v["total"] else 0
        v["pnl"]      = round(v["pnl"], 2)
    return dict(sorted(groups.items(), key=lambda x: -x[1]["total"]))


def _frequency(trades: list[dict], field: str) -> dict[str, int]:
    freq: dict[str, int] = {}
    for t in trades:
        key = str(t.get(field) or "Sin definir")
        freq[key] = freq.get(key, 0) + 1
    return dict(sorted(freq.items(), key=lambda x: -x[1]))


def _mistake_frequency(trades: list[dict]) -> dict[str, int]:
    freq: dict[str, int] = {}
    for t in trades:
        for m in str(t.get("mistakes") or "").split(","):
            m = m.strip()
            if m:
                freq[m] = freq.get(m, 0) + 1
    return dict(sorted(freq.items(), key=lambda x: -x[1]))


def _equity_curve(trades: list[dict], initial: float) -> list[dict]:
    curve   = []
    balance = initial
    peak    = initial
    for i, t in enumerate(trades):
        pnl      = float(t.get("net_pnl") or 0)
        balance += pnl
        if balance > peak:
            peak = balance
        dd_pct = (peak - balance) / peak * 100 if peak > 0 else 0
        curve.append({
            "index":        i + 1,
            "trade_id":     t.get("id", i + 1),
            "date":         str(t.get("entry_date", "")),
            "symbol":       str(t.get("symbol", "")),
            "outcome":      str(t.get("outcome", "")),
            "model":        str(t.get("trading_model__name") or ""),
            "pnl":          round(pnl, 2),
            "balance":      round(balance, 2),
            "drawdown_pct": round(dd_pct, 2),
        })
    return curve


def _monthly_pnl(trades: list[dict]) -> list[dict]:
    monthly: dict[str, dict] = {}
    winner_outcomes = {"maximum_profit", "great_exit", "good_exit"}
    loser_outcomes  = {"stop_loss", "winning_turned_loser"}
    for t in trades:
        date  = str(t.get("entry_date", ""))
        month = date[:7] if len(date) >= 7 else "N/A"
        if month not in monthly:
            monthly[month] = {"month": month, "total": 0, "wins": 0, "losses": 0, "pnl": 0.0}
        monthly[month]["total"] += 1
        outcome = t.get("outcome", "")
        if outcome in winner_outcomes:
            monthly[month]["wins"] += 1
        elif outcome in loser_outcomes:
            monthly[month]["losses"] += 1
        monthly[month]["pnl"] += float(t.get("net_pnl") or 0)
    result = []
    for v in sorted(monthly.values(), key=lambda x: x["month"]):
        v["win_rate"] = round(v["wins"] / v["total"] * 100, 1) if v["total"] else 0
        v["pnl"]      = round(v["pnl"], 2)
        result.append(v)
    return result
