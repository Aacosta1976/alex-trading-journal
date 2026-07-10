import random
from datetime import timedelta, date, time, datetime
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from apps.trades.models import Account, Trade, TradingModel

SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "US100", "US30", "XAUUSD", "GBPJPY", "AUDUSD", "USDCAD", "NAS100"]
SIGNALS = ["CSD", "MSS", "BOS", "Liquidity Grab", "CHOCH"]


def random_choice(choices):
    return random.choice(choices)[0]


class Command(BaseCommand):
    help = "Genera operaciones de prueba (reales y backtest) para una cuenta existente."

    def add_arguments(self, parser):
        parser.add_argument("--account", type=int, required=True, help="ID de la cuenta (ver: python manage.py list_users)")
        parser.add_argument("--live", type=int, default=500, help="Numero de operaciones reales (is_backtest=False)")
        parser.add_argument("--backtest", type=int, default=500, help="Numero de operaciones de backtest (is_backtest=True)")
        parser.add_argument("--start-date", type=str, default="2024-01-01", help="Fecha inicial YYYY-MM-DD")
        parser.add_argument("--end-date", type=str, default=None, help="Fecha final YYYY-MM-DD (por defecto hoy)")
        parser.add_argument("--wipe", action="store_true", help="Borra antes las operaciones existentes de esa cuenta")

    def handle(self, *args, **options):
        try:
            account = Account.objects.get(pk=options["account"])
        except Account.DoesNotExist:
            raise CommandError(f"No existe ninguna cuenta con id={options['account']}. Ejecuta: python manage.py list_users")

        user = account.user
        trading_models = list(TradingModel.objects.filter(user=user))

        start = datetime.strptime(options["start_date"], "%Y-%m-%d").date()
        end = datetime.strptime(options["end_date"], "%Y-%m-%d").date() if options["end_date"] else date.today()
        span_days = (end - start).days
        if span_days <= 0:
            raise CommandError("El rango de fechas debe ser positivo (start-date < end-date).")

        if options["wipe"]:
            deleted, _ = account.trades.all().delete()
            self.stdout.write(self.style.WARNING(f"Borradas {deleted} operaciones previas de la cuenta \"{account.name}\"."))

        def make_trade(is_backtest):
            entry_date = start + timedelta(days=random.randint(0, span_days))
            entry_time = time(hour=random.randint(0, 23), minute=random.randint(0, 59))
            duration = random.randint(5, 480)
            exit_minutes = entry_time.hour * 60 + entry_time.minute + duration
            exit_date = entry_date + timedelta(days=exit_minutes // 1440)
            exit_time = time(hour=(exit_minutes // 60) % 24, minute=exit_minutes % 60)

            outcome = random_choice(Trade.OUTCOME_CHOICES)
            is_win = outcome in ("maximum_profit", "great_exit", "good_exit", "partial_win")

            risk_pct = Decimal(random.uniform(0.25, 2.0)).quantize(Decimal("0.01"))
            actual_rr = Decimal(random.uniform(0.5, 5.0) if is_win else random.uniform(-1.2, -0.2)).quantize(Decimal("0.01"))
            gross_pnl = (Decimal(account.initial_balance) * risk_pct / 100 * actual_rr).quantize(Decimal("0.01"))
            fees = Decimal(random.uniform(0, 8)).quantize(Decimal("0.01"))
            net_pnl = gross_pnl - fees
            max_rr = (actual_rr if actual_rr > 0 else Decimal("0")) + Decimal(random.uniform(0, 1.5)).quantize(Decimal("0.01"))

            mistakes = [] if is_win else random.sample([c[0] for c in Trade.MISTAKE_CHOICES], k=random.randint(0, 2))
            confluences = random.sample([c[0] for c in Trade.CONFLUENCE_CHOICES], k=random.randint(1, 3))
            key_levels = random.sample([c[0] for c in Trade.KEY_LEVEL_CHOICES], k=random.randint(0, 2))
            tp_mgmt = random.sample([c[0] for c in Trade.TP_MANAGEMENT_CHOICES], k=random.randint(1, 2))

            return Trade(
                account=account,
                user=user,
                trading_model=random.choice(trading_models) if trading_models and random.random() > 0.2 else None,
                symbol=random.choice(SYMBOLS),
                entry_date=entry_date,
                entry_time=entry_time,
                exit_date=exit_date,
                exit_time=exit_time,
                duration_minutes=duration,
                status="Closed",
                is_backtest=is_backtest,
                bias=random_choice(Trade.BIAS_CHOICES),
                market_conditions=random_choice(Trade.MARKET_CONDITIONS_CHOICES),
                session=random_choice(Trade.SESSION_CHOICES),
                news_impact=random_choice(Trade.NEWS_IMPACT_CHOICES),
                entry_timeframe=random_choice(Trade.TIMEFRAME_CHOICES),
                entry_signal=random.choice(SIGNALS),
                order_type=random_choice(Trade.ORDER_TYPE_CHOICES),
                position=random_choice(Trade.POSITION_CHOICES),
                type_of_trade=random_choice(Trade.TYPE_OF_TRADE_CHOICES),
                setup_grade=random_choice(Trade.SETUP_GRADE_CHOICES),
                confluences=", ".join(confluences),
                key_levels=", ".join(key_levels),
                risk_pct=risk_pct,
                sl_pips=Decimal(random.uniform(3, 60)).quantize(Decimal("0.1")),
                sl_management=random_choice(Trade.SL_MANAGEMENT_CHOICES),
                tp_management=", ".join(tp_mgmt),
                outcome=outcome,
                actual_rr=actual_rr,
                max_rr_reached=max_rr,
                gross_pnl=gross_pnl,
                fees=fees,
                net_pnl=net_pnl,
                mistakes=", ".join(mistakes),
                notes=f"Operacion de prueba generada automaticamente ({'backtest' if is_backtest else 'real'}).",
            )

        n_live = options["live"]
        n_bt = options["backtest"]

        self.stdout.write(f"Generando {n_live} operaciones reales y {n_bt} de backtest para \"{account.name}\" (usuario: {user.username})...")

        batch = [make_trade(False) for _ in range(n_live)] + [make_trade(True) for _ in range(n_bt)]
        Trade.objects.bulk_create(batch, batch_size=200)

        self.stdout.write(self.style.SUCCESS(f"Listo: {len(batch)} operaciones creadas en la cuenta \"{account.name}\"."))