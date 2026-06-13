"""Exportador PDF profesional con ReportLab."""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Colores del tema
GOLD   = colors.HexColor("#F0B429")
CYAN   = colors.HexColor("#58A6FF")
GREEN  = colors.HexColor("#3FB950")
RED    = colors.HexColor("#F85149")
ORANGE = colors.HexColor("#DB6D28")
PURPLE = colors.HexColor("#BC8CFF")
DARK   = colors.HexColor("#0D1117")
CARD   = colors.HexColor("#161B22")
HEADER = colors.HexColor("#1C2333")
TEXT   = colors.HexColor("#E6EDF3")
SUBTLE = colors.HexColor("#8B949E")
BORDER = colors.HexColor("#30363D")


def export_pdf(trades: list[dict], metrics: dict, username: str) -> bytes:
    """Genera reporte PDF completo con métricas y diario."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm,  bottomMargin=1.5*cm,
    )
    story = []
    _add_header(story, metrics, username)
    _add_kpis(story, metrics)
    _add_setup_stats(story, metrics)
    _add_trades_table(story, trades)
    doc.build(story)
    return buf.getvalue()


def _style(name, **kwargs):
    base = getSampleStyleSheet()["Normal"]
    return ParagraphStyle(name, parent=base, **kwargs)


def _add_header(story, metrics, username):
    title_s = _style("T", fontSize=16, textColor=GOLD, alignment=TA_CENTER, spaceAfter=4)
    sub_s   = _style("S", fontSize=9,  textColor=SUBTLE, alignment=TA_CENTER, spaceAfter=10)

    story.append(Paragraph(f"⚡  TRADING JOURNAL — {username.upper()}", title_s))
    story.append(Paragraph(
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}  •  "
        f"Trades: {metrics.get('total_trades',0)}  •  "
        f"P&L: ${metrics.get('gross_pnl',0):+,.2f}  •  "
        f"Win Rate: {metrics.get('win_rate',0):.1f}%  •  "
        f"Profit Factor: {metrics.get('profit_factor',0):.2f}×",
        sub_s,
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=GOLD, spaceAfter=10))


def _add_kpis(story, metrics):
    sec_s = _style("SEC", fontSize=10, textColor=CYAN, spaceBefore=8, spaceAfter=6,
                   fontName="Helvetica-Bold")
    story.append(Paragraph("MÉTRICAS DE RENDIMIENTO", sec_s))

    gross = metrics.get("gross_pnl", 0)
    roe   = metrics.get("roe", 0)

    data = [
        ["Métrica", "Valor", "Métrica", "Valor", "Métrica", "Valor"],
        ["Total Trades",    str(metrics.get("total_trades",0)),
         "Balance Inicial", f"${metrics.get('initial_balance',0):,.2f}",
         "Avg Win",         f"${metrics.get('avg_win',0):.2f}"],
        ["W / L / Flat",    f"{metrics.get('total_wins',0)}/{metrics.get('total_losses',0)}/{metrics.get('total_flats',0)}",
         "Balance Final",   f"${metrics.get('final_balance',0):,.2f}",
         "Avg Loss",        f"${metrics.get('avg_loss',0):.2f}"],
        ["Win Rate",        f"{metrics.get('win_rate',0):.1f}%",
         "P&L Neto",        f"${gross:+,.2f}",
         "Mejor Trade",     f"${metrics.get('best_trade',0):.2f}"],
        ["Profit Factor",   f"{metrics.get('profit_factor',0):.2f}×",
         "ROE",             f"{roe:+.2f}%",
         "Peor Trade",      f"${metrics.get('worst_trade',0):.2f}"],
        ["Avg R:R",         f"{metrics.get('avg_rr',0):.2f}R",
         "Max Drawdown",    f"{metrics.get('max_drawdown_pct',0):.1f}%",
         "Sharpe",          f"{metrics.get('sharpe_ratio',0):.2f}"],
        ["Racha Win máx.",  str(metrics.get("max_win_streak",0)),
         "Racha Loss máx.", str(metrics.get("max_loss_streak",0)),
         "Expectancy",      f"${metrics.get('expectancy',0):.4f}"],
    ]

    t = Table(data, colWidths=[4.5*cm, 3.5*cm, 4.5*cm, 3.5*cm, 4.5*cm, 3.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),   HEADER),
        ("TEXTCOLOR",     (0,0),(-1,0),   CYAN),
        ("FONTNAME",      (0,0),(-1,0),   "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,-1),  8.5),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),  [CARD, DARK]),
        ("TEXTCOLOR",     (0,1),(0,-1),   SUBTLE),
        ("TEXTCOLOR",     (2,1),(2,-1),   SUBTLE),
        ("TEXTCOLOR",     (4,1),(4,-1),   SUBTLE),
        ("TEXTCOLOR",     (1,1),(1,-1),   CYAN),
        ("TEXTCOLOR",     (3,1),(3,-1),   GREEN if gross >= 0 else RED),
        ("TEXTCOLOR",     (5,1),(5,-1),   CYAN),
        ("FONTNAME",      (1,1),(1,-1),   "Helvetica-Bold"),
        ("FONTNAME",      (3,1),(3,-1),   "Helvetica-Bold"),
        ("FONTNAME",      (5,1),(5,-1),   "Helvetica-Bold"),
        ("GRID",          (0,0),(-1,-1),  0.4, BORDER),
        ("ALIGN",         (0,0),(-1,-1),  "CENTER"),
        ("VALIGN",        (0,0),(-1,-1),  "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1),  4),
        ("BOTTOMPADDING", (0,0),(-1,-1),  4),
    ]))
    story.append(t)


def _add_setup_stats(story, metrics):
    sec_s = _style("SEC2", fontSize=10, textColor=PURPLE, spaceBefore=12, spaceAfter=6,
                   fontName="Helvetica-Bold")
    story.append(Paragraph("PERFORMANCE POR SETUP", sec_s))

    data = [["Setup", "Trades", "Wins", "Losses", "Win Rate", "P&L ($)"]]
    for k, v in metrics.get("setup_stats", {}).items():
        pnl = v["pnl"]
        data.append([k, str(v["total"]), str(v["wins"]), str(v["losses"]),
                      f"{v['win_rate']:.1f}%", f"${pnl:+.2f}"])

    if len(data) > 1:
        t = Table(data, colWidths=[4*cm, 3*cm, 3*cm, 3*cm, 3*cm, 4*cm])
        ts = [
            ("BACKGROUND", (0,0),(-1,0),  HEADER),
            ("TEXTCOLOR",  (0,0),(-1,0),  PURPLE),
            ("FONTNAME",   (0,0),(-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",   (0,0),(-1,-1), 8.5),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[CARD, DARK]),
            ("TEXTCOLOR",  (0,1),(-1,-1), TEXT),
            ("GRID",       (0,0),(-1,-1), 0.4, BORDER),
            ("ALIGN",      (0,0),(-1,-1), "CENTER"),
            ("TOPPADDING", (0,0),(-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ]
        t.setStyle(TableStyle(ts))
        story.append(t)


def _add_trades_table(story, trades):
    sec_s = _style("SEC3", fontSize=10, textColor=GOLD, spaceBefore=12, spaceAfter=6,
                   fontName="Helvetica-Bold")
    story.append(Paragraph("DIARIO DE OPERACIONES", sec_s))

    headers = ["#","Fecha","Símbolo","Pos.","Setup","TF","Risk%","P&L","W/L","Acum $","Error"]
    data    = [headers]

    for i, t in enumerate(trades):
        pnl  = float(t.get("pnl_real") or 0)
        risk = t.get("risk_pct")
        acum = float(t.get("profit_cumul") or 0)
        data.append([
            str(i+1),
            str(t.get("trade_date","")),
            str(t.get("symbol","")),
            str(t.get("position","")),
            str(t.get("setup","")),
            str(t.get("timeframe","")),
            f"{float(risk)*100:.1f}%" if risk else "",
            f"${pnl:+.2f}",
            str(t.get("result","")),
            f"${acum:.2f}",
            (str(t.get("error_type") or ""))[:22],
        ])

    cw = [1*cm, 2.5*cm, 2.5*cm, 1.8*cm, 1.8*cm, 1.5*cm, 1.8*cm, 2.5*cm, 1.5*cm, 2.5*cm, 5.5*cm]
    t  = Table(data, colWidths=cw, repeatRows=1)

    ts = [
        ("BACKGROUND",    (0,0),(-1,0),   HEADER),
        ("TEXTCOLOR",     (0,0),(-1,0),   GOLD),
        ("FONTNAME",      (0,0),(-1,0),   "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,-1),  7.5),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),  [CARD, DARK]),
        ("TEXTCOLOR",     (0,1),(-1,-1),  TEXT),
        ("GRID",          (0,0),(-1,-1),  0.3, BORDER),
        ("ALIGN",         (0,0),(-1,-1),  "CENTER"),
        ("VALIGN",        (0,0),(-1,-1),  "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1),  3),
        ("BOTTOMPADDING", (0,0),(-1,-1),  3),
    ]
    # Colorear columna W/L
    for i, tr in enumerate(trades):
        r   = i + 1
        res = tr.get("result","")
        col = GREEN if res=="W" else (RED if res=="L" else ORANGE)
        ts += [("TEXTCOLOR",(8,r),(8,r),col), ("FONTNAME",(8,r),(8,r),"Helvetica-Bold")]
        pnl = float(tr.get("pnl_real") or 0)
        ts += [("TEXTCOLOR",(7,r),(7,r), GREEN if pnl>0 else (RED if pnl<0 else ORANGE))]

    t.setStyle(TableStyle(ts))
    story.append(t)
