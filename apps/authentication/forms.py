"""
Formularios de autenticación.
Usan Django Forms con validación personalizada.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginForm(AuthenticationForm):
    """Formulario de inicio de sesión con estilos Bootstrap."""

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "class":       "form-control",
            "placeholder": "Usuario",
            "autofocus":   True,
        }),
        label="Usuario",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class":       "form-control",
            "placeholder": "Contraseña",
        }),
        label="Contraseña",
    )


class RegisterForm(UserCreationForm):
    """Formulario de registro con campos extra del trader."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "class":       "form-control",
            "placeholder": "correo@ejemplo.com",
        }),
        label="Email",
    )
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class":       "form-control",
            "placeholder": "Nombre",
        }),
        label="Nombre",
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class":       "form-control",
            "placeholder": "Apellidos",
        }),
        label="Apellidos",
    )
    default_risk_pct = forms.DecimalField(
        min_value=0.01,
        max_value=10.0,
        decimal_places=2,
        initial=1.0,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "step":  "0.01",
        }),
        label="Riesgo por defecto (%)",
        help_text="Porcentaje de riesgo por operación (recomendado: 1-2%).",
    )

    class Meta:
        model  = User
        fields = ("username", "email", "first_name", "last_name",
                  "default_risk_pct", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicar clase Bootstrap a todos los campos restantes
        for field_name in ("username", "password1", "password2"):
            self.fields[field_name].widget.attrs.update({"class": "form-control"})

    def clean_email(self):
        """Verifica que el email no esté ya registrado."""
        email = self.cleaned_data.get("email", "").lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está registrado.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email           = self.cleaned_data["email"].lower()
        user.default_risk_pct= self.cleaned_data["default_risk_pct"]
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """Formulario de edición del perfil de usuario."""

    class Meta:
        model  = User
        fields = ("first_name", "last_name", "email", "bio", "default_risk_pct")
        widgets = {
            "first_name":       forms.TextInput(attrs={"class": "form-control"}),
            "last_name":        forms.TextInput(attrs={"class": "form-control"}),
            "email":            forms.EmailInput(attrs={"class": "form-control"}),
            "bio":              forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "default_risk_pct": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }
        labels = {
            "first_name":       "Nombre",
            "last_name":        "Apellidos",
            "email":            "Email",
            "bio":              "Biografía",
            "default_risk_pct": "Riesgo por defecto (%)",
        }
