"""Vistas del Journal — listado, detalle, crear, editar, borrar trades."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Trade, Account, TradingModel, AfterActionReport
from .forms import TradeForm, AfterActionReportForm, AccountForm, TradingModelForm


class TradeListView(LoginRequiredMixin, ListView):
    """
    Journal — listado de todos los trades del usuario.
    Filtros: cuenta, símbolo, outcome, modelo, bias, session.
    """
    model               = Trade
    template_name       = "trades/list.html"
    context_object_name = "trades"
    paginate_by         = 25

    def get_queryset(self):
        qs = Trade.objects.filter(
            user=self.request.user,
            is_backtest=False,
        ).select_related("account", "trading_model").order_by("-entry_date", "-entry_time")

        # Filtros
        q          = self.request.GET.get("q", "")
        account_id = self.request.GET.get("account", "")
        outcome    = self.request.GET.get("outcome", "")
        model_id   = self.request.GET.get("model", "")
        session    = self.request.GET.get("session", "")
        bias       = self.request.GET.get("bias", "")

        if q:
            qs = qs.filter(Q(symbol__icontains=q) | Q(notes__icontains=q))
        if account_id:
            qs = qs.filter(account_id=account_id)
        if outcome:
            qs = qs.filter(outcome=outcome)
        if model_id:
            qs = qs.filter(trading_model_id=model_id)
        if session:
            qs = qs.filter(session=session)
        if bias:
            qs = qs.filter(bias=bias)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["accounts"]       = Account.objects.filter(user=user, is_active=True)
        ctx["trading_models"] = TradingModel.objects.filter(user=user)
        ctx["outcome_choices"]= Trade.OUTCOME_CHOICES
        ctx["session_choices"]= Trade.SESSION_CHOICES
        ctx["bias_choices"]   = Trade.BIAS_CHOICES
        ctx["filters"]        = self.request.GET

        # Fix INC-02: la columna "Acum $" (P&L acumulado) no existe como campo en el
        # modelo Trade -- se calcula aquí como suma corrida de net_pnl en orden
        # cronológico ascendente sobre TODO el conjunto filtrado (no solo la página
        # actual, para que el acumulado sea correcto independientemente de la
        # paginación), y se adjunta como atributo `cumulative_pnl` a cada trade de la
        # página actual (que se sigue mostrando en orden descendente).
        import datetime as _dt
        all_filtered = self.get_queryset().order_by("entry_date", "entry_time", "created_at")
        running_totals = {}
        running = 0
        for t in all_filtered:
            running += float(t.net_pnl or 0)
            running_totals[t.pk] = running
        for t in ctx["trades"]:
            t.cumulative_pnl = running_totals.get(t.pk)

        return ctx


class TradeDetailView(LoginRequiredMixin, DetailView):
    model               = Trade
    template_name       = "trades/detail.html"
    context_object_name = "trade"

    def get_queryset(self):
        return Trade.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        trade = self.get_object()
        # AAR
        try:
            ctx["aar"] = trade.after_action_report
        except AfterActionReport.DoesNotExist:
            ctx["aar"] = None
        ctx["aar_form"] = AfterActionReportForm(
            instance=ctx["aar"]
        )
        return ctx


class TradeCreateView(LoginRequiredMixin, CreateView):
    model         = Trade
    form_class    = TradeForm
    template_name = "trades/form.html"
    success_url   = reverse_lazy("trades:list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Nuevo Trade"
        ctx["action"] = "Registrar"
        return ctx


class TradeUpdateView(LoginRequiredMixin, UpdateView):
    model         = Trade
    form_class    = TradeForm
    template_name = "trades/form.html"

    def get_queryset(self):
        return Trade.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy("trades:detail", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"]  = f"Editar Trade #{self.object.trade_id or self.object.pk}"
        ctx["action"] = "Guardar cambios"
        return ctx


class TradeDeleteView(LoginRequiredMixin, DeleteView):
    model         = Trade
    template_name = "trades/confirm_delete.html"
    success_url   = reverse_lazy("trades:list")

    def get_queryset(self):
        return Trade.objects.filter(user=self.request.user)


# ── After-Action Report ───────────────────────────────────────────────────────

from django.views import View
from django.shortcuts import get_object_or_404, redirect

class AARSaveView(LoginRequiredMixin, View):
    """Guardar el After-Action Report de un trade."""

    def post(self, request, pk):
        trade = get_object_or_404(Trade, pk=pk, user=request.user)
        try:
            aar = trade.after_action_report
        except AfterActionReport.DoesNotExist:
            aar = AfterActionReport(trade=trade)
        form = AfterActionReportForm(request.POST, instance=aar)
        if form.is_valid():
            form.save()
        return redirect("trades:detail", pk=pk)


# ── Accounts & Models ─────────────────────────────────────────────────────────

class AccountListView(LoginRequiredMixin, ListView):
    model               = Account
    template_name       = "trades/accounts.html"
    context_object_name = "accounts"

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)


class AccountCreateView(LoginRequiredMixin, CreateView):
    model         = Account
    form_class    = AccountForm
    template_name = "trades/account_form.html"
    success_url   = reverse_lazy("trades:accounts")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class TradingModelListView(LoginRequiredMixin, ListView):
    model               = TradingModel
    template_name       = "trades/models.html"
    context_object_name = "trading_models"

    def get_queryset(self):
        return TradingModel.objects.filter(user=self.request.user)


class TradingModelCreateView(LoginRequiredMixin, CreateView):
    model         = TradingModel
    form_class    = TradingModelForm
    template_name = "trades/model_form.html"
    success_url   = reverse_lazy("trades:model_list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
