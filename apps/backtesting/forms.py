"""Formulario de backtesting."""
from django import forms
from apps.trades.models import Trade


class BacktestForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Mi estrategia OB en NQ!"}),
        label="Nombre del backtest",
    )
    symbol = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "NQ!, XAUUSD..."}),
        label="Símbolo",
    )
    setup = forms.ChoiceField(
        choices=[("", "Todos los setups")] + Trade.SETUP_GRADE_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Setup",
    )
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        label="Fecha inicio",
    )
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        label="Fecha fin",
    )
    initial_balance = forms.DecimalField(
        min_value=1, max_digits=12, decimal_places=2, initial=1000,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        label="Balance inicial ($)",
    )
    risk_pct = forms.DecimalField(
        min_value=0.01, max_value=10, decimal_places=2, initial=1.0,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        label="Riesgo por trade (%)",
        help_text="Porcentaje del balance a arriesgar en cada operación.",
    )

    def clean(self):
        cleaned = super().clean()
        df = cleaned.get("date_from")
        dt = cleaned.get("date_to")
        if df and dt and df >= dt:
            raise forms.ValidationError("La fecha inicio debe ser anterior a la fecha fin.")
        return cleaned
