"""
Vistas de autenticación.
Login, registro, logout y perfil de usuario.
"""

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.utils.decorators import method_decorator

from apps.authentication.forms import LoginForm, RegisterForm, ProfileForm
from apps.trades.models import Account


class LoginView(View):
    """Vista de inicio de sesión."""

    template_name = "authentication/login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard:index")
        return render(request, self.template_name, {"form": LoginForm()})

    def post(self, request):
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"¡Bienvenido, {user.username}!")
            return redirect(request.GET.get("next", "dashboard:index"))
        messages.error(request, "Usuario o contraseña incorrectos.")
        return render(request, self.template_name, {"form": form})


class RegisterView(View):
    """Vista de registro de nuevo usuario."""

    template_name = "authentication/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard:index")
        return render(request, self.template_name, {"form": RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Crear cuenta de trading por defecto
            Account.objects.create(
                user=user,
                name="Cuenta Principal",
                initial_balance=1000.00,
            )
            login(request, user)
            messages.success(request, "¡Registro exitoso! Bienvenido al Trading Journal.")
            return redirect("dashboard:index")
        return render(request, self.template_name, {"form": form})


@method_decorator(login_required, name="dispatch")
class ProfileView(View):
    """Vista de perfil y edición de datos del usuario."""

    template_name = "authentication/profile.html"

    def get(self, request):
        form = ProfileForm(instance=request.user)
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil actualizado correctamente.")
            return redirect("authentication:profile")
        return render(request, self.template_name, {"form": form})


def logout_view(request):
    """Cierra la sesión del usuario."""
    logout(request)
    messages.info(request, "Sesión cerrada. ¡Hasta pronto!")
    return redirect("authentication:login")
