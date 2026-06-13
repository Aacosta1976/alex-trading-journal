from django.urls import path
from . import views

app_name = "system"
urlpatterns = [
    path("",                          views.SystemView.as_view(),            name="index"),
    path("accounts/<int:pk>/edit/",   views.AccountUpdateView.as_view(),     name="account_edit"),
    path("accounts/<int:pk>/delete/", views.AccountDeleteView.as_view(),     name="account_delete"),
    path("models/<int:pk>/edit/",     views.TradingModelUpdateView.as_view(),name="model_edit"),
    path("models/<int:pk>/delete/",   views.TradingModelDeleteView.as_view(),name="model_delete"),
]
