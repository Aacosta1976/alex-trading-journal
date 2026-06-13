from django.urls import path
from . import views

app_name = "trades"

urlpatterns = [
    # Journal (Live trades)
    path("",                    views.TradeListView.as_view(),        name="list"),
    path("new/",                views.TradeCreateView.as_view(),      name="create"),
    path("<int:pk>/",           views.TradeDetailView.as_view(),      name="detail"),
    path("<int:pk>/edit/",      views.TradeUpdateView.as_view(),      name="update"),
    path("<int:pk>/delete/",    views.TradeDeleteView.as_view(),      name="delete"),
    path("<int:pk>/aar/",       views.AARSaveView.as_view(),          name="aar_save"),
    # Accounts
    path("accounts/",           views.AccountListView.as_view(),      name="accounts"),
    path("accounts/new/",       views.AccountCreateView.as_view(),    name="account_create"),
    # Trading Models
    path("models/",             views.TradingModelListView.as_view(), name="model_list"),
    path("models/new/",         views.TradingModelCreateView.as_view(),name="model_create"),
]
