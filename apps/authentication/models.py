"""
Modelos de la app authentication.

Extiende el modelo User de Django para añadir campos
específicos del diario de trading.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Usuario personalizado del sistema.

    Extiende AbstractUser añadiendo campos propios del trader.
    Usar AUTH_USER_MODEL = 'authentication.User' en settings.
    """

    email = models.EmailField(
        unique=True,
        verbose_name="Email",
    )
    bio = models.TextField(
        blank=True,
        verbose_name="Biografía",
        help_text="Descripción breve del trader.",
    )
    default_risk_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
        verbose_name="Riesgo por defecto (%)",
        help_text="Porcentaje de riesgo por operación que se pre-rellena en el formulario.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name        = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering            = ["-date_joined"]

    def __str__(self) -> str:
        return f"{self.username} ({self.email})"

    @property
    def full_name(self) -> str:
        """Nombre completo o username si no está definido."""
        return self.get_full_name() or self.username
