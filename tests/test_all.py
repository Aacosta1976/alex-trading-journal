"""
Suite de pruebas — Trading Journal v3 (corregida)
Correcciones:
  - Dashboard URL es / (redirige a /dashboard/)
  - test_user_creation usa email único
  - reports tests usan entry_date
"""

from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from apps.trades.models import Account, Trade, TradingModel, AfterActionReport
from apps.backtesting.models import Backtest
from apps.dashboard.services import compute_metrics

User = get_user_model()


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures comunes
# ══════════════════════════════════════════════════════════════════════════════

def make_user(username="testuser", password="TestPass123!", email="test@test.com"):
    return User.objects.create_user(username=username, password=password, email=email)


def make_account(user, name="Test Account", account_type="Live",
                 initial_balance=Decimal("10000.00")):
    return Account.objects.create(
        user=user, name=name,
        account_type=account_type,
        initial_balance=initial_balance,
    )


def make_trade(user, account, **kwargs):
    defaults = {
        "symbol":      "EURUSD",
        "entry_date":  "2024-08-14",
        "status":      "Closed",
        "position":    "Buy",
        "outcome":     "great_exit",
        "net_pnl":     Decimal("500.00"),
        "actual_rr":   Decimal("2.0"),
        "risk_pct":    Decimal("1.0"),
        "is_backtest": False,
    }
    defaults.update(kwargs)
    return Trade.objects.create(user=user, account=account, **defaults)


# ══════════════════════════════════════════════════════════════════════════════
# OE1 — Autenticación
# ══════════════════════════════════════════════════════════════════════════════

class AuthenticationTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user   = make_user()

    def test_login_page_loads(self):
        response = self.client.get("/auth/login/")
        self.assertEqual(response.status_code, 200)

    def test_login_correct_credentials(self):
        response = self.client.post("/auth/login/", {
            "username": "testuser", "password": "TestPass123!",
        })
        self.assertIn(response.status_code, [200, 302])

    def test_login_wrong_password(self):
        response = self.client.post("/auth/login/", {
            "username": "testuser", "password": "WrongPassword",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_register_page_loads(self):
        response = self.client.get("/auth/register/")
        self.assertEqual(response.status_code, 200)

    def test_logout_redirects(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post("/auth/logout/")
        self.assertIn(response.status_code, [200, 302])

    def test_dashboard_requires_login(self):
        """Raíz redirige cuando no hay sesión."""
        response = self.client.get("/")
        self.assertIn(response.status_code, [302, 301])

    def test_user_creation(self):
        """Se puede crear un usuario con email único."""
        user = User.objects.create_user(
            username="newuser",
            password="Pass1234!",
            email="newuser@test.com",
        )
        self.assertEqual(User.objects.filter(username="newuser").count(), 1)
        self.assertTrue(user.check_password("Pass1234!"))

    def test_password_is_hashed(self):
        user = User.objects.get(username="testuser")
        self.assertNotEqual(user.password, "TestPass123!")
        self.assertTrue(user.password.startswith("pbkdf2_"))


# ══════════════════════════════════════════════════════════════════════════════
# OE2 — Trades CRUD
# ══════════════════════════════════════════════════════════════════════════════

class TradeModelTests(TestCase):

    def setUp(self):
        self.user    = make_user()
        self.account = make_account(self.user)

    def test_create_trade(self):
        trade = make_trade(self.user, self.account)
        self.assertEqual(Trade.objects.count(), 1)
        self.assertEqual(trade.symbol, "EURUSD")

    def test_trade_str(self):
        trade = make_trade(self.user, self.account)
        self.assertIn("EURUSD", str(trade))

    def test_trade_is_winner(self):
        trade = make_trade(self.user, self.account, outcome="maximum_profit")
        self.assertTrue(trade.is_winner)

    def test_trade_is_loser(self):
        trade = make_trade(self.user, self.account, outcome="stop_loss")
        self.assertTrue(trade.is_loser)

    def test_trade_outcome_color_winner(self):
        trade = make_trade(self.user, self.account, outcome="great_exit")
        self.assertEqual(trade.outcome_color, "success")

    def test_trade_outcome_color_loser(self):
        trade = make_trade(self.user, self.account, outcome="stop_loss")
        self.assertEqual(trade.outcome_color, "danger")

    def test_trade_confluences_list(self):
        trade = make_trade(self.user, self.account,
                           confluences="SMT Divergence with DXY, HTF Trend Alignment")
        lst = trade.get_confluences_list()
        self.assertEqual(len(lst), 2)
        self.assertIn("SMT Divergence with DXY", lst)

    def test_trade_mistakes_list(self):
        trade = make_trade(self.user, self.account,
                           mistakes="Wrong Entry Point, Overconfidence")
        self.assertEqual(len(trade.get_mistakes_list()), 2)

    def test_trade_delete(self):
        trade = make_trade(self.user, self.account)
        pk = trade.pk
        trade.delete()
        self.assertEqual(Trade.objects.filter(pk=pk).count(), 0)

    def test_trade_update(self):
        trade = make_trade(self.user, self.account, net_pnl=Decimal("100.00"))
        trade.net_pnl = Decimal("200.00")
        trade.save()
        self.assertEqual(Trade.objects.get(pk=trade.pk).net_pnl, Decimal("200.00"))

    def test_backtest_flag(self):
        live = make_trade(self.user, self.account, is_backtest=False)
        bt   = make_trade(self.user, self.account, is_backtest=True, symbol="USDJPY")
        self.assertFalse(live.is_backtest)
        self.assertTrue(bt.is_backtest)


# ══════════════════════════════════════════════════════════════════════════════
# OE2 — Account y TradingModel
# ══════════════════════════════════════════════════════════════════════════════

class AccountModelTests(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_create_account(self):
        self.assertEqual(make_account(self.user) and Account.objects.count(), 1)

    def test_account_net_pnl_empty(self):
        acc = make_account(self.user)
        self.assertEqual(acc.net_pnl, Decimal("0"))

    def test_account_net_pnl_with_trades(self):
        acc = make_account(self.user)
        make_trade(self.user, acc, net_pnl=Decimal("500.00"))
        make_trade(self.user, acc, net_pnl=Decimal("-200.00"), outcome="stop_loss")
        self.assertEqual(acc.net_pnl, Decimal("300.00"))

    def test_account_current_balance(self):
        acc = make_account(self.user, initial_balance=Decimal("10000.00"))
        make_trade(self.user, acc, net_pnl=Decimal("1000.00"))
        self.assertEqual(acc.current_balance, Decimal("11000.00"))

    def test_account_win_rate(self):
        acc = make_account(self.user)
        make_trade(self.user, acc, outcome="maximum_profit", net_pnl=Decimal("500"))
        make_trade(self.user, acc, outcome="stop_loss",      net_pnl=Decimal("-100"))
        make_trade(self.user, acc, outcome="great_exit",     net_pnl=Decimal("300"))
        self.assertAlmostEqual(acc.win_rate, 66.7, places=0)

    def test_account_goal_progress(self):
        acc = make_account(self.user, initial_balance=Decimal("5000.00"))
        acc.goal = Decimal("10000.00")
        acc.save()
        self.assertAlmostEqual(acc.goal_progress_pct, 50.0, places=0)

    def test_account_goal_bar(self):
        acc = make_account(self.user, initial_balance=Decimal("5000.00"))
        acc.goal = Decimal("10000.00")
        acc.save()
        bar = acc.goal_progress_bar
        self.assertEqual(len(bar), 10)
        self.assertTrue(all(c in "●○" for c in bar))

    def test_trading_model_creation(self):
        model = TradingModel.objects.create(
            user=self.user, name="Model #1", description="OB strategy"
        )
        self.assertEqual(str(model), "Model #1")


# ══════════════════════════════════════════════════════════════════════════════
# OE2 — After-Action Report
# ══════════════════════════════════════════════════════════════════════════════

class AfterActionReportTests(TestCase):

    def setUp(self):
        self.user    = make_user()
        self.account = make_account(self.user)
        self.trade   = make_trade(self.user, self.account)

    def test_create_aar(self):
        aar = AfterActionReport.objects.create(
            trade=self.trade,
            went_well="Seguí el plan.",
            went_wrong="Entré tarde.",
            improvement="Más paciencia.",
            lesson="La disciplina supera la intuición.",
        )
        self.assertEqual(AfterActionReport.objects.count(), 1)
        self.assertEqual(aar.trade, self.trade)

    def test_aar_one_to_one(self):
        AfterActionReport.objects.create(trade=self.trade, went_well="OK")
        with self.assertRaises(Exception):
            AfterActionReport.objects.create(trade=self.trade, went_well="Duplicado")


# ══════════════════════════════════════════════════════════════════════════════
# OE3 — Métricas del dashboard
# ══════════════════════════════════════════════════════════════════════════════

class MetricsServiceTests(TestCase):

    def _sample_trades(self):
        return [
            {"net_pnl": 500,  "outcome": "maximum_profit",     "entry_date": "2024-01-01",
             "symbol": "EURUSD", "actual_rr": 2.5, "max_rr_reached": 3.0,
             "trading_model__name": "Model #1", "account__initial_balance": 10000,
             "session": "London", "bias": "Bullish", "entry_timeframe": "15 minutes",
             "setup_grade": "A+", "news_impact": "Low", "mistakes": "", "status": "Closed"},
            {"net_pnl": 300,  "outcome": "great_exit",          "entry_date": "2024-01-02",
             "symbol": "USDJPY", "actual_rr": 1.5, "max_rr_reached": 2.0,
             "trading_model__name": "Model #1", "account__initial_balance": 10000,
             "session": "New York", "bias": "Bullish", "entry_timeframe": "1 Hour",
             "setup_grade": "A", "news_impact": "Medium", "mistakes": "", "status": "Closed"},
            {"net_pnl": 200,  "outcome": "good_exit",           "entry_date": "2024-01-03",
             "symbol": "EURUSD", "actual_rr": 1.0, "max_rr_reached": 1.5,
             "trading_model__name": "Model #2", "account__initial_balance": 10000,
             "session": "London", "bias": "Bearish", "entry_timeframe": "15 minutes",
             "setup_grade": "B", "news_impact": "Low", "mistakes": "Overconfidence",
             "status": "Closed"},
            {"net_pnl": -200, "outcome": "stop_loss",           "entry_date": "2024-01-04",
             "symbol": "USDJPY", "actual_rr": -1.0, "max_rr_reached": 0.5,
             "trading_model__name": "Model #1", "account__initial_balance": 10000,
             "session": "New York", "bias": "Bearish", "entry_timeframe": "1 Hour",
             "setup_grade": "C", "news_impact": "High", "mistakes": "Wrong Entry Point",
             "status": "Closed"},
            {"net_pnl": -100, "outcome": "winning_turned_loser","entry_date": "2024-01-05",
             "symbol": "EURUSD", "actual_rr": -0.5, "max_rr_reached": 0.8,
             "trading_model__name": "Model #2", "account__initial_balance": 10000,
             "session": "London", "bias": "Bullish", "entry_timeframe": "15 minutes",
             "setup_grade": "D", "news_impact": "Low",
             "mistakes": "Emotional Trading, Wrong Entry Point", "status": "Closed"},
        ]

    def test_empty_trades_returns_zeros(self):
        m = compute_metrics([])
        self.assertEqual(m["total_trades"], 0)
        self.assertEqual(m["win_rate"],     0)
        self.assertEqual(m["gross_pnl"],    0)

    def test_total_trades(self):
        self.assertEqual(compute_metrics(self._sample_trades())["total_trades"], 5)

    def test_win_rate(self):
        self.assertAlmostEqual(compute_metrics(self._sample_trades())["win_rate"], 60.0, places=1)

    def test_gross_pnl(self):
        self.assertAlmostEqual(compute_metrics(self._sample_trades())["gross_pnl"], 700.0, places=1)

    def test_profit_factor(self):
        self.assertAlmostEqual(compute_metrics(self._sample_trades())["profit_factor"], 3.33, places=1)

    def test_total_wins_and_losses(self):
        m = compute_metrics(self._sample_trades())
        self.assertEqual(m["total_wins"],   3)
        self.assertEqual(m["total_losses"], 2)

    def test_avg_win(self):
        self.assertAlmostEqual(compute_metrics(self._sample_trades())["avg_win"], 333.33, places=1)

    def test_avg_loss(self):
        self.assertAlmostEqual(compute_metrics(self._sample_trades())["avg_loss"], -150.0, places=1)

    def test_expectancy_positive(self):
        self.assertGreater(compute_metrics(self._sample_trades())["expectancy"], 0)

    def test_max_drawdown(self):
        self.assertGreaterEqual(compute_metrics(self._sample_trades())["max_drawdown"], 0)

    def test_sharpe_ratio_calculated(self):
        self.assertIsInstance(compute_metrics(self._sample_trades())["sharpe_ratio"], float)

    def test_sortino_ratio_calculated(self):
        self.assertIsInstance(compute_metrics(self._sample_trades())["sortino_ratio"], float)

    def test_recovery_factor_positive(self):
        m = compute_metrics(self._sample_trades())
        if m["max_drawdown"] > 0:
            self.assertGreater(m["recovery_factor"], 0)

    def test_equity_curve_length(self):
        trades = self._sample_trades()
        self.assertEqual(len(compute_metrics(trades)["equity_curve"]), len(trades))

    def test_equity_curve_final_balance(self):
        m = compute_metrics(self._sample_trades())
        self.assertAlmostEqual(m["equity_curve"][-1]["balance"], 10700.0, places=1)

    def test_monthly_pnl_structure(self):
        for item in compute_metrics(self._sample_trades())["monthly_pnl"]:
            self.assertIn("month",    item)
            self.assertIn("pnl",      item)
            self.assertIn("win_rate", item)

    def test_model_stats_keys(self):
        m = compute_metrics(self._sample_trades())
        self.assertIn("Model #1", m["model_stats"])
        self.assertIn("Model #2", m["model_stats"])

    def test_mistake_frequency(self):
        m = compute_metrics(self._sample_trades())
        self.assertGreaterEqual(m["mistake_stats"].get("Wrong Entry Point", 0), 2)

    def test_win_streak(self):
        self.assertGreaterEqual(compute_metrics(self._sample_trades())["max_win_streak"], 1)

    def test_loss_streak(self):
        self.assertGreaterEqual(compute_metrics(self._sample_trades())["max_loss_streak"], 1)

    def test_single_trade_metrics(self):
        m = compute_metrics([self._sample_trades()[0]])
        self.assertEqual(m["total_trades"], 1)
        self.assertEqual(m["win_rate"], 100.0)


# ══════════════════════════════════════════════════════════════════════════════
# OE4 — Backtesting
# ══════════════════════════════════════════════════════════════════════════════

class BacktestModelTests(TestCase):

    def setUp(self):
        self.user    = make_user()
        self.account = make_account(self.user, account_type="Backtest",
                                    initial_balance=Decimal("1000.00"))

    def test_create_backtest(self):
        bt = Backtest.objects.create(
            user=self.user, name="Backtest #1", symbol="EURUSD",
            date_from="2024-01-01", date_to="2024-12-31",
            initial_balance=Decimal("1000.00"), risk_pct=Decimal("1.0"),
        )
        self.assertEqual(Backtest.objects.count(), 1)
        self.assertIn("Backtest #1", str(bt))

    def test_backtest_trades_filter(self):
        make_trade(self.user, self.account, is_backtest=True,  symbol="EURUSD")
        make_trade(self.user, self.account, is_backtest=False, symbol="EURUSD")
        self.assertEqual(Trade.objects.filter(user=self.user, is_backtest=True).count(),  1)
        self.assertEqual(Trade.objects.filter(user=self.user, is_backtest=False).count(), 1)

    def test_backtest_account_type(self):
        self.assertEqual(self.account.account_type, "Backtest")


# ══════════════════════════════════════════════════════════════════════════════
# OE5 — Exportación
# ══════════════════════════════════════════════════════════════════════════════

class ReportsViewTests(TestCase):

    def setUp(self):
        self.client  = Client()
        self.user    = make_user()
        self.account = make_account(self.user)
        make_trade(self.user, self.account)
        self.client.login(username="testuser", password="TestPass123!")

    def test_excel_export_returns_200(self):
        response = self.client.get("/reports/excel/")
        self.assertEqual(response.status_code, 200)

    def test_excel_export_content_type(self):
        response = self.client.get("/reports/excel/")
        self.assertIn("spreadsheetml", response.get("Content-Type", ""))

    def test_pdf_export_returns_200(self):
        response = self.client.get("/reports/pdf/")
        self.assertEqual(response.status_code, 200)

    def test_pdf_export_content_type(self):
        response = self.client.get("/reports/pdf/")
        self.assertIn("pdf", response.get("Content-Type", ""))

    def test_reports_require_login(self):
        self.client.logout()
        response = self.client.get("/reports/excel/")
        self.assertIn(response.status_code, [302, 301])


# ══════════════════════════════════════════════════════════════════════════════
# OE1+OE2 — Vistas con autenticación
# ══════════════════════════════════════════════════════════════════════════════

class ViewAccessTests(TestCase):

    def setUp(self):
        self.client  = Client()
        self.user    = make_user()
        self.account = make_account(self.user)
        self.client.login(username="testuser", password="TestPass123!")

    def test_dashboard_loads(self):
        """La raíz redirige al dashboard y carga con 200."""
        response = self.client.get("/", follow=True)
        self.assertEqual(response.status_code, 200)

    def test_journal_list_loads(self):
        response = self.client.get("/journal/")
        self.assertEqual(response.status_code, 200)

    def test_journal_new_form_loads(self):
        response = self.client.get("/journal/new/")
        self.assertEqual(response.status_code, 200)

    def test_backtesting_list_loads(self):
        response = self.client.get("/backtesting/")
        self.assertEqual(response.status_code, 200)

    def test_chart_page_loads(self):
        response = self.client.get("/chart/")
        self.assertEqual(response.status_code, 200)

    def test_system_page_loads(self):
        response = self.client.get("/system/")
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_redirected(self):
        self.client.logout()
        for url in ["/journal/", "/chart/", "/system/", "/backtesting/"]:
            response = self.client.get(url)
            self.assertIn(response.status_code, [301, 302],
                          msg=f"{url} debería redirigir sin sesión")

    def test_create_trade_via_post(self):
        response = self.client.post("/journal/new/", {
            "account":     self.account.pk,
            "symbol":      "USDJPY",
            "entry_date":  "2024-08-15",
            "status":      "Closed",
            "position":    "Buy",
            "outcome":     "great_exit",
            "net_pnl":     "300.00",
            "is_backtest": False,
        })
        self.assertIn(response.status_code, [200, 302])
