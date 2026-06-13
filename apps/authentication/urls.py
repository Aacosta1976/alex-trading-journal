"""URLs de autenticación."""
from django.urls import path
from apps.authentication import views

app_name = "authentication"

urlpatterns = [
    path("login/",    views.LoginView.as_view(),    name="login"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("logout/",   views.logout_view,            name="logout"),
    path("profile/",  views.ProfileView.as_view(),  name="profile"),
]
