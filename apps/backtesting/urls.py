"""URLs de backtesting."""
from django.urls import path
from apps.backtesting import views

app_name = "backtesting"

urlpatterns = [
    path("",               views.BacktestListView.as_view(),   name="list"),
    path("new/",           views.BacktestCreateView.as_view(), name="create"),
    path("<int:pk>/",      views.BacktestDetailView.as_view(), name="detail"),
    path("<int:pk>/delete/",views.BacktestDeleteView.as_view(),name="delete"),
]
