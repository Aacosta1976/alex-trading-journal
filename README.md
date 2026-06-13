# Trading Journal v2 — Basado en Notion de Alex

## Qué hay de nuevo respecto a la v0

### Nuevos campos en el modelo `Trade`

| Campo | Descripción |
|---|---|
| `bias` | Bullish / Bearish / Neutral |
| `market_conditions` | Condiciones del mercado al entrar |
| `session` | London Open, New York, Asian... |
| `news_impact` | Low / Medium / High |
| `entry_timeframe` | TF de entrada (1m, 5m, 15m, 1H...) |
| `entry_signal` | CSD, MSS, BOS... |
| `order_type` | Limit / Market / Stop |
| `type_of_trade` | Scalping, Day Trade, Swing... |
| `setup_grade` | A+, A, B, C, D |
| `confluences` | Multi-select guardado como CSV |
| `key_levels` | Multi-select guardado como CSV |
| `sl_management` | Moved to BE, Locked Profit... |
| `tp_management` | Final TP Hit, Partial 1/2/3, Pre-News Exit... |
| `outcome` | 🚀 Maximum Profit!, ✅ Great Exit!, ❌ Stop Loss... |
| `actual_rr` | RR conseguido real |
| `max_rr_reached` | RR máximo que llegó a tocar |
| `gross_pnl` | PnL bruto (antes de fees) |
| `fees` | Comisiones |
| `mistakes` | Multi-select de errores |
| `screenshot` | Imagen del trade |
| `is_backtest` | ¿Es trade de backtest? |
| `duration_minutes` | Duración en minutos |
| `status` | Open / Closed |

### Nuevo modelo: `TradingModel`
- Model #1, Model #2, etc.
- Relacionado con cada trade
- Estadísticas por modelo en Chart

### `Account` mejorada
- `account_type`: Live, Challenge, Backtest, Demo
- `goal`: meta en dólares
- Propiedades calculadas: `net_pnl`, `current_balance`, `win_rate`, `goal_progress_pct`, `goal_progress_bar`

### Nuevo modelo: `AfterActionReport`
- Por trade: What Went Well, What Went Wrong, What To Improve, Lesson Learned

### Nuevas apps
- `apps.chart` — Análisis estadístico (Profitability, WR, R&R, Trades Count)
- `apps.system` — Gestión de cuentas y modelos con métricas

---

## Estructura del proyecto

```
trading_journal/
├── apps/
│   ├── authentication/   # Login, registro, perfil
│   ├── trades/           # Journal — CRUD de trades
│   ├── dashboard/        # Dashboard principal con KPIs
│   ├── backtesting/      # Sesiones de backtest
│   ├── chart/            # Análisis estadístico (Chart page)
│   ├── system/           # Gestión de cuentas y modelos
│   └── reports/          # Export PDF/Excel
├── templates/
│   ├── base.html
│   ├── trades/
│   ├── dashboard/
│   ├── backtesting/
│   ├── chart/
│   └── system/
├── config/
│   ├── settings.py
│   └── urls.py
└── media/
    └── screenshots/      # Imágenes de trades
```

---

## Instalación desde cero

```bash
# 1. Instalar dependencias
pip install django python-dotenv pillow reportlab openpyxl

# 2. Variables de entorno
cp .env.example .env

# 3. Migraciones
python manage.py makemigrations authentication trades backtesting
python manage.py migrate

# 4. Superusuario
python manage.py createsuperuser

# 5. Arrancar
python manage.py runserver
```

## Migración desde v0

Si tienes datos en la v0, el campo `result` del trade original mapea así:

| v0 `result` | v2 `outcome` |
|---|---|
| `W` | `great_exit` |
| `L` | `stop_loss` |
| `Flat` | `capital_protected` |

Los campos `pnl_real` → `net_pnl`, `trade_date` → `entry_date`.

---

## Menú de navegación

```
🏠 Dashboard | 📙 Journal | ⏮️ Backtesting | 📊 Chart | 💻 System
```

Replicando exactamente la barra del Notion.
