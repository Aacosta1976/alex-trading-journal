# apps/chart/urls.py
from django.urls import path
from . import views

app_name = "chart"
urlpatterns = [
    path("", views.ChartView.as_view(), name="index"),
]
