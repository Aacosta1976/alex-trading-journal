"""Formularios del diario de trading — basado en Notion de Alex."""

from django import forms
from .models import Trade, Account, TradingModel, AfterActionReport


class TradeForm(forms.ModelForm):
    """
    Formulario completo de registro de trade.
    Replica todos los campos de la base de datos Trades del Notion.
    """

    # Campos multi-select (guardados como texto CSV)
    confluences = forms.MultipleChoiceField(
        choices=Trade.CONFLUENCE_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        required=False,
        label="Confluencias",
    )
    key_levels = forms.MultipleChoiceField(
        choices=Trade.KEY_LEVEL_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        required=False,
        label="Niveles clave",
    )
    tp_management = forms.MultipleChoiceField(
        choices=Trade.TP_MANAGEMENT_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        required=False,
        label="Gestión TP",
    )
    mistakes = forms.MultipleChoiceField(
        choices=Trade.MISTAKE_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        required=False,
        label="Errores",
    )

    class Meta:
        model  = Trade
        fields = [
            # Identificación
            "account", "trading_model", "symbol", "is_backtest",
            # Fechas
            "entry_date", "entry_time", "exit_date", "exit_time", "duration_minutes",
            "status",
            # Contexto
            "bias", "market_conditions", "session", "news_impact",
            # Setup
            "entry_timeframe", "entry_signal", "order_type",
            "position", "type_of_trade", "setup_grade",
            # Confluencias y niveles
            "confluences", "key_levels",
            # Riesgo
            "risk_pct", "sl_pips", "sl_management", "tp_management",
            # Resultado
            "outcome", "actual_rr", "max_rr_reached",
            "gross_pnl", "fees", "net_pnl",
            # Análisis
            "mistakes", "notes", "screenshot",
        ]
        widgets = {
            "entry_date":       forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "entry_time":       forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "exit_date":        forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "exit_time":        forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "duration_minutes": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "symbol":           forms.TextInput(attrs={"class": "form-control", "placeholder": "EURUSD, USDJPY, US100..."}),
            "entry_signal":     forms.TextInput(attrs={"class": "form-control", "placeholder": "CSD, MSS, BOS..."}),
            "risk_pct":         forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0", "max": "10"}),
            "sl_pips":          forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
            "actual_rr":        forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "max_rr_reached":   forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "gross_pnl":        forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "fees":             forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "net_pnl":          forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "notes":            forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_backtest":      forms.CheckboxInput(attrs={"class": "form-check-input"}),
            # Selects con Bootstrap
            "account":          forms.Select(attrs={"class": "form-select"}),
            "trading_model":    forms.Select(attrs={"class": "form-select"}),
            "bias":             forms.Select(attrs={"class": "form-select"}),
            "market_conditions":forms.Select(attrs={"class": "form-select"}),
            "session":          forms.Select(attrs={"class": "form-select"}),
            "news_impact":      forms.Select(attrs={"class": "form-select"}),
            "entry_timeframe":  forms.Select(attrs={"class": "form-select"}),
            "order_type":       forms.Select(attrs={"class": "form-select"}),
            "position":         forms.Select(attrs={"class": "form-select"}),
            "type_of_trade":    forms.Select(attrs={"class": "form-select"}),
            "setup_grade":      forms.Select(attrs={"class": "form-select"}),
            "sl_management":    forms.Select(attrs={"class": "form-select"}),
            "outcome":          forms.Select(attrs={"class": "form-select"}),
            "status":           forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields["account"].queryset      = Account.objects.filter(user=user, is_active=True)
            self.fields["trading_model"].queryset = TradingModel.objects.filter(user=user)

        # Pre-popular multi-select desde el texto guardado
        if self.instance.pk:
            if self.instance.confluences:
                self.initial["confluences"] = self.instance.get_confluences_list()
            if self.instance.key_levels:
                self.initial["key_levels"] = self.instance.get_key_levels_list()
            if self.instance.tp_management:
                self.initial["tp_management"] = self.instance.get_tp_management_list()
            if self.instance.mistakes:
                self.initial["mistakes"] = self.instance.get_mistakes_list()

    def clean_confluences(self):
        return ", ".join(self.cleaned_data.get("confluences", []))

    def clean_key_levels(self):
        return ", ".join(self.cleaned_data.get("key_levels", []))

    def clean_tp_management(self):
        return ", ".join(self.cleaned_data.get("tp_management", []))

    def clean_mistakes(self):
        return ", ".join(self.cleaned_data.get("mistakes", []))


class AfterActionReportForm(forms.ModelForm):
    """Formulario del After-Action Report."""
    class Meta:
        model  = AfterActionReport
        fields = ["went_well", "went_wrong", "improvement", "lesson"]
        widgets = {
            "went_well":   forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "¿Qué ejecutaste correctamente?"}),
            "went_wrong":  forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "¿Qué falló o hiciste mal?"}),
            "improvement": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "¿Qué cambiarías la próxima vez?"}),
            "lesson":      forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "¿Qué aprendiste de este trade?"}),
        }


class AccountForm(forms.ModelForm):
    """Formulario de cuenta."""
    class Meta:
        model  = Account
        fields = ["name", "broker", "account_type", "initial_balance", "goal", "currency"]
        widgets = {
            "name":            forms.TextInput(attrs={"class": "form-control"}),
            "broker":          forms.TextInput(attrs={"class": "form-control"}),
            "account_type":    forms.Select(attrs={"class": "form-select"}),
            "initial_balance": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "goal":            forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "currency":        forms.TextInput(attrs={"class": "form-control", "maxlength": 3}),
        }


class TradingModelForm(forms.ModelForm):
    """Formulario para crear/editar modelos de trading."""
    class Meta:
        model  = TradingModel
        fields = ["name", "description"]
        widgets = {
            "name":        forms.TextInput(attrs={"class": "form-control", "placeholder": "Model #1"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }
