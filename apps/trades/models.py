"""
Modelos de operaciones de trading.

Replicado desde Notion: Alex Trading Journal
Secciones: Journal, Backtesting, Chart, System
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Account(models.Model):
    """
    Cuenta de trading. Tipos: Live (Challenge), Backtest, Demo.
    Replica la tabla Accounts del Notion con Goal y Goal Progress.
    """

    ACCOUNT_TYPE_CHOICES = [
        ("Live",      "Live"),
        ("Challange", "Challenge (Prop Firm)"),
        ("Backtest",  "Backtest"),
        ("Demo",      "Demo"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="accounts",
    )
    name            = models.CharField(max_length=100, verbose_name="Nombre")
    broker          = models.CharField(max_length=100, blank=True, verbose_name="Broker")
    account_type    = models.CharField(
        max_length=20, choices=ACCOUNT_TYPE_CHOICES,
        default="Live", verbose_name="Tipo",
    )
    initial_balance = models.DecimalField(
        max_digits=14, decimal_places=2,
        default=Decimal("1000.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Balance inicial ($)",
    )
    goal            = models.DecimalField(
        max_digits=14, decimal_places=2,
        null=True, blank=True,
        verbose_name="Meta ($)",
    )
    currency        = models.CharField(max_length=3, default="USD")
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Cuenta"
        verbose_name_plural = "Cuentas"
        ordering            = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"

    # ── Propiedades calculadas ────────────────────────────────────────────

    @property
    def net_pnl(self) -> Decimal:
        from django.db.models import Sum
        total = self.trades.aggregate(t=Sum("net_pnl"))["t"] or Decimal("0")
        return total

    @property
    def current_balance(self) -> Decimal:
        return self.initial_balance + self.net_pnl

    @property
    def win_rate(self) -> float:
        total = self.trades.count()
        if not total:
            return 0.0
        wins = self.trades.filter(outcome__in=[
            "maximum_profit", "great_exit", "good_exit"
        ]).count()
        return round(wins / total * 100, 1)

    @property
    def goal_progress_pct(self) -> float:
        if not self.goal or self.goal <= 0:
            return 0.0
        return round(float(self.current_balance) / float(self.goal) * 100, 1)

    @property
    def goal_progress_bar(self) -> str:
        """Genera barra de progreso estilo Notion: ●●●○○○○○○○"""
        pct = self.goal_progress_pct
        filled = round(pct / 10)
        filled = max(0, min(10, filled))
        return "●" * filled + "○" * (10 - filled)


class TradingModel(models.Model):
    """
    Modelo de trading del usuario (Model #1, Model #2, etc.)
    Referenciado desde los trades.
    """
    user        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trading_models")
    name        = models.CharField(max_length=100, verbose_name="Nombre del modelo")
    description = models.TextField(blank=True, verbose_name="Descripción")
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Modelo de trading"
        verbose_name_plural = "Modelos de trading"
        ordering            = ["name"]

    def __str__(self):
        return self.name


class Trade(models.Model):
    """
    Operación individual. Replica exactamente los campos
    de la base de datos Trades del Notion de Alex.
    """

    # ── Choices extraídos del Notion ──────────────────────────────────────

    BIAS_CHOICES = [
        ("Bullish", "Bullish 🟢"),
        ("Bearish", "Bearish 🔴"),
        ("Neutral", "Neutral ⚪"),
    ]
    POSITION_CHOICES = [
        ("Buy",  "Buy  ▲"),
        ("Sell", "Sell ▼"),
    ]
    STATUS_CHOICES = [
        ("Open",   "Open 🟡"),
        ("Closed", "Closed ✅"),
    ]
    OUTCOME_CHOICES = [
        ("maximum_profit",          "🚀 Maximum Profit!"),
        ("great_exit",              "✅ Great Exit!"),
        ("good_exit",               "🎯 Good Exit"),
        ("winner_to_be",            "⚠️ Winner to BE but Fees Lost"),
        ("capital_protected",       "🔵 Capital Protected"),
        ("winning_turned_loser",    "💔 Winning Trade Turned Loser"),
        ("stop_loss",               "❌ Stop Loss"),
        ("partial_win",             "🟡 Partial Win"),
    ]
    SESSION_CHOICES = [
        ("London Open",     "London Open"),
        ("London",          "London"),
        ("London Close",    "London Close"),
        ("New York",        "New York"),
        ("New York AM",     "New York AM"),
        ("New York PM",     "New York PM"),
        ("Asian",           "Asian"),
        ("Asian Open",      "Asian Open"),
    ]
    TIMEFRAME_CHOICES = [
        ("1 minute",   "1 Minute"),
        ("5 minutes",  "5 Minutes"),
        ("15 minutes", "15 Minutes"),
        ("30 minutes", "30 Minutes"),
        ("1 Hour",     "1 Hour"),
        ("4 Hours",    "4 Hours"),
        ("Daily",      "Daily"),
        ("Weekly",     "Weekly"),
    ]
    NEWS_IMPACT_CHOICES = [
        ("Low",    "Low 🟢"),
        ("Medium", "Medium 🟡"),
        ("High",   "High 🔴"),
        ("None",   "No News"),
    ]
    SETUP_GRADE_CHOICES = [
        ("A+", "A+ ⭐"),
        ("A",  "A"),
        ("B",  "B"),
        ("C",  "C"),
        ("D",  "D — No Setup"),
    ]
    ORDER_TYPE_CHOICES = [
        ("Limit Order",  "Limit Order"),
        ("Market Order", "Market Order"),
        ("Stop Order",   "Stop Order"),
    ]
    TYPE_OF_TRADE_CHOICES = [
        ("Scalping",         "Scalping"),
        ("Day Trade",        "Day Trade"),
        ("Short Term Trade", "Short Term Trade"),
        ("Swing Trade",      "Swing Trade"),
    ]
    SL_MANAGEMENT_CHOICES = [
        ("Moved to BE",    "Moved to BE"),
        ("Locked Profit",  "Locked Profit"),
        ("Trailing Stop",  "Trailing Stop"),
        ("Full Stop Loss", "Full Stop Loss"),
        ("Manual Close",   "Manual Close"),
    ]
    TP_MANAGEMENT_CHOICES = [
        ("Final TP Hit",        "Final TP Hit"),
        ("Partial 1 Taken",     "Partial 1 Taken"),
        ("Partial 2 Taken",     "Partial 2 Taken"),
        ("Partial 3 Taken",     "Partial 3 Taken"),
        ("Let Runner Go",       "Let Runner Go"),
        ("Pre-News Exit",       "Pre-News Exit"),
        ("Manual Close",        "Manual Close"),
    ]
    MISTAKE_CHOICES = [
        ("Wrong Entry Point",       "Wrong Entry Point"),
        ("Overconfidence",          "Overconfidence"),
        ("Emotional Trading",       "Emotional Trading"),
        ("Revenge Trading",         "Revenge Trading"),
        ("Bad Stop Placement",      "Bad Stop Placement"),
        ("No Setup",                "No Setup"),
        ("Entry on News",           "Entry on News"),
        ("Too Many Partials",       "Too Many Partials"),
        ("Poor Market Read",        "Poor Market Read"),
        ("FOMO Entry",              "FOMO Entry"),
        ("Bad Trade Management",    "Bad Trade Management"),
    ]
    CONFLUENCE_CHOICES = [
        ("SMT Divergence with DXY",   "SMT Divergence with DXY"),
        ("HTF Trend Alignment",        "HTF Trend Alignment"),
        ("Aligned with Seasonal",      "Aligned with Seasonal"),
        ("Open Interest Rising",       "Open Interest Rising"),
        ("Liquidity Sweep",            "Liquidity Sweep"),
        ("FVG",                        "Fair Value Gap"),
        ("VWAP Support",               "VWAP Support"),
        ("Volume Profile",             "Volume Profile"),
        ("Market Structure Shift",     "Market Structure Shift"),
    ]
    KEY_LEVEL_CHOICES = [
        ("Order Block (1D)",   "Order Block (1D)"),
        ("Order Block (H4)",   "Order Block (H4)"),
        ("Order Block (H1)",   "Order Block (H1)"),
        ("Rejection Block (H4)", "Rejection Block (H4)"),
        ("FVG (H4)",           "FVG (H4)"),
        ("PDL",                "PDL — Previous Day Low"),
        ("PDH",                "PDH — Previous Day High"),
        ("Weekly Low",         "Weekly Low"),
        ("Weekly High",        "Weekly High"),
        ("Support",            "Support"),
        ("Resistance",         "Resistance"),
    ]
    MARKET_CONDITIONS_CHOICES = [
        ("Strong uptrend (LTF)",        "Strong Uptrend (LTF)"),
        ("Pullback in uptrend",          "Pullback in Uptrend"),
        ("Strong downtrend (LTF)",      "Strong Downtrend (LTF)"),
        ("Pullback in downtrend",        "Pullback in Downtrend"),
        ("Consolidation before reversal","Consolidation Before Reversal"),
        ("Ranging market",              "Ranging Market"),
        ("High volatility",             "High Volatility"),
    ]

    # ── Relaciones ────────────────────────────────────────────────────────
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE,
        related_name="trades", verbose_name="Cuenta",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="trades",
    )
    trading_model = models.ForeignKey(
        TradingModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="trades", verbose_name="Modelo",
    )

    # ── Identificación ────────────────────────────────────────────────────
    trade_id        = models.PositiveIntegerField(null=True, blank=True, verbose_name="ID")
    symbol          = models.CharField(max_length=20, verbose_name="Símbolo")
    entry_date      = models.DateField(verbose_name="Fecha entrada")
    entry_time      = models.TimeField(null=True, blank=True, verbose_name="Hora entrada")
    exit_date       = models.DateField(null=True, blank=True, verbose_name="Fecha salida")
    exit_time       = models.TimeField(null=True, blank=True, verbose_name="Hora salida")
    duration_minutes= models.PositiveIntegerField(null=True, blank=True, verbose_name="Duración (min)")
    status          = models.CharField(
        max_length=10, choices=STATUS_CHOICES,
        default="Open", verbose_name="Estado",
    )
    is_backtest     = models.BooleanField(default=False, verbose_name="¿Es backtest?")

    # ── Contexto de mercado ───────────────────────────────────────────────
    bias                = models.CharField(
        max_length=10, choices=BIAS_CHOICES,
        blank=True, verbose_name="Bias",
    )
    market_conditions   = models.CharField(
        max_length=60, choices=MARKET_CONDITIONS_CHOICES,
        blank=True, verbose_name="Condiciones de mercado",
    )
    session             = models.CharField(
        max_length=20, choices=SESSION_CHOICES,
        blank=True, verbose_name="Sesión",
    )
    news_impact         = models.CharField(
        max_length=10, choices=NEWS_IMPACT_CHOICES,
        blank=True, verbose_name="Impacto noticias",
    )

    # ── Setup & Entrada ───────────────────────────────────────────────────
    entry_timeframe     = models.CharField(
        max_length=20, choices=TIMEFRAME_CHOICES,
        blank=True, verbose_name="Timeframe entrada",
    )
    entry_signal        = models.CharField(max_length=50, blank=True, verbose_name="Señal de entrada")
    order_type          = models.CharField(
        max_length=20, choices=ORDER_TYPE_CHOICES,
        blank=True, verbose_name="Tipo de orden",
    )
    position            = models.CharField(
        max_length=4, choices=POSITION_CHOICES,
        blank=True, verbose_name="Posición",
    )
    type_of_trade       = models.CharField(
        max_length=20, choices=TYPE_OF_TRADE_CHOICES,
        blank=True, verbose_name="Tipo de trade",
    )
    setup_grade         = models.CharField(
        max_length=5, choices=SETUP_GRADE_CHOICES,
        blank=True, verbose_name="Calidad del setup",
    )

    # ── Confluencias y niveles (multi-valor guardado como texto separado por comas) ──
    confluences         = models.TextField(blank=True, verbose_name="Confluencias")
    key_levels          = models.TextField(blank=True, verbose_name="Niveles clave")

    # ── Gestión de riesgo ─────────────────────────────────────────────────
    risk_pct            = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal("0.01")), MaxValueValidator(Decimal("10"))],
        verbose_name="Riesgo (%)",
    )
    sl_pips             = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True, verbose_name="S/L Pips",
    )
    sl_management       = models.CharField(
        max_length=20, choices=SL_MANAGEMENT_CHOICES,
        blank=True, verbose_name="Gestión del SL",
    )
    tp_management       = models.TextField(blank=True, verbose_name="Gestión del TP")

    # ── Resultado ─────────────────────────────────────────────────────────
    outcome             = models.CharField(
        max_length=30, choices=OUTCOME_CHOICES,
        blank=True, verbose_name="Resultado",
    )
    actual_rr           = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True, verbose_name="RR conseguido",
    )
    max_rr_reached      = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True, verbose_name="RR máx. alcanzado",
    )
    gross_pnl           = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True, verbose_name="Gross PnL ($)",
    )
    fees                = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=Decimal("0.00"), verbose_name="Fees ($)",
    )
    net_pnl             = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True, verbose_name="Net PnL ($)",
    )

    # ── Análisis post-trade ───────────────────────────────────────────────
    mistakes            = models.TextField(blank=True, verbose_name="Errores cometidos")
    notes               = models.TextField(blank=True, verbose_name="Notas")
    screenshot          = models.ImageField(
        upload_to="screenshots/", null=True, blank=True,
        verbose_name="Screenshot",
    )

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Operación"
        verbose_name_plural = "Operaciones"
        ordering            = ["-entry_date", "-entry_time", "-created_at"]
        indexes = [
            models.Index(fields=["user", "entry_date"]),
            models.Index(fields=["user", "symbol"]),
            models.Index(fields=["user", "outcome"]),
            models.Index(fields=["account", "entry_date"]),
            models.Index(fields=["user", "is_backtest"]),
        ]

    def __str__(self):
        return f"#{self.trade_id or self.pk} {self.symbol} {self.entry_date} — {self.get_outcome_display() or '?'}"

    # ── Helpers ───────────────────────────────────────────────────────────

    @property
    def is_winner(self) -> bool:
        return self.outcome in ("maximum_profit", "great_exit", "good_exit")

    @property
    def is_loser(self) -> bool:
        return self.outcome in ("stop_loss", "winning_turned_loser")

    @property
    def outcome_color(self) -> str:
        if self.is_winner:   return "success"
        if self.is_loser:    return "danger"
        if self.outcome == "capital_protected": return "info"
        return "warning"

    @property
    def position_icon(self) -> str:
        if self.position == "Buy":  return "▲"
        if self.position == "Sell": return "▼"
        return "—"

    def get_confluences_list(self) -> list:
        if not self.confluences:
            return []
        return [c.strip() for c in self.confluences.split(",") if c.strip()]

    def get_key_levels_list(self) -> list:
        if not self.key_levels:
            return []
        return [k.strip() for k in self.key_levels.split(",") if k.strip()]

    def get_tp_management_list(self) -> list:
        if not self.tp_management:
            return []
        return [t.strip() for t in self.tp_management.split(",") if t.strip()]

    def get_mistakes_list(self) -> list:
        if not self.mistakes:
            return []
        return [m.strip() for m in self.mistakes.split(",") if m.strip()]


class AfterActionReport(models.Model):
    """
    Reporte post-trade (After-Action Report).
    Replica la base de datos AAR del Notion.
    """
    SECTION_CHOICES = [
        ("went_well",      "✅ What Went Well"),
        ("went_wrong",     "❌ What Went Wrong"),
        ("improvement",    "💡 What To Improve"),
        ("lesson",         "📚 Lesson Learned"),
    ]

    trade   = models.OneToOneField(
        Trade, on_delete=models.CASCADE,
        related_name="after_action_report",
    )
    went_well   = models.TextField(blank=True, verbose_name="¿Qué salió bien?")
    went_wrong  = models.TextField(blank=True, verbose_name="¿Qué salió mal?")
    improvement = models.TextField(blank=True, verbose_name="¿Qué mejorar?")
    lesson      = models.TextField(blank=True, verbose_name="Lección aprendida")
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "After-Action Report"

    def __str__(self):
        return f"AAR — {self.trade}"
