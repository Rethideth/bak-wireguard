from django import forms

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from wireguardapp.models import Interface, Peer, PeerSnapshot, Key,Profile
from wireguardapp.services.serverservice import ServerService

from datetime import datetime
import ipaddress
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm,PasswordChangeForm,SetPasswordForm




class BootstrapFormMixin:
    """Automatically add Bootstrap classes to form fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for name, field in self.fields.items():
            widget = field.widget

            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = "form-check-input"
            else:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} form-control".strip()

class BootstrapAuthenticationForm(BootstrapFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['username'].label = "Uživatelské jméno"
        self.fields['password'].label = "Heslo"

class BootstrapChangePasswordForm(BootstrapFormMixin, PasswordChangeForm):
    pass

class BootstrapSetPasswordForm(BootstrapFormMixin, SetPasswordForm):
    pass


class CustomLoginView(LoginView):
    authentication_form = BootstrapAuthenticationForm


class CustomUserCreationForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(required=True, label="E-mailová adresa")
    username = forms.CharField(required=True, label="Uživatelské jméno")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name","password1", "password2")
        labels = {
            'first_name': 'Jméno',
            'last_name': 'Příjmení',
        }



class ClientKeyForm(BootstrapFormMixin,forms.Form):
    name = forms.CharField(max_length=255)
    interface = forms.ModelChoiceField(
        queryset=ServerService.getAllServerInterfaces(),
        required=True
    )


class ServerInterfaceForm(BootstrapFormMixin,forms.ModelForm):
    server_name = forms.CharField(max_length=255,required=False, label="Jméno rozhraní")
    ip_network_mask = forms.IntegerField(max_value=31, min_value=0,label="Maska sítě")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['listen_port'].required = True
        self.fields['ip_network'].required = True
        self.fields['ip_network'].help_text = "In a form of e.g. 10.10.0.0"
        if self.instance and self.instance.pk:
            del self.fields['server_name']


    class Meta:
        model = Interface
        fields = [
            "server_name",
            "ip_network",
            "ip_network_mask",
            "server_endpoint",
            "listen_port",
            "client_to_client",
        ]

    def clean(self):
        cleaned = super().clean()

        net = cleaned.get("ip_network")
        mask = cleaned.get("ip_network_mask")

        if not net or mask is None:
            return cleaned

        try:
            network = ipaddress.ip_network(f"{net}/{mask}")
        except ValueError:
            self.add_error(
                "ip_network",
                "Vložte správnou ip adresu sítě."
            )
            return cleaned

        qs = ServerService.getAllServerInterfaces()

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        for inf in qs:
            taken = ipaddress.ip_network(inf.ip_network)
            if taken.overlaps(network):
                self.add_error(
                    "ip_network",
                    f"Tato síť je už obsazena. (síť: {inf.ip_network}/{inf.ip_network_mask})"
                )

        return cleaned

    def clean_listen_port(self):
        value = self.cleaned_data["listen_port"]

        qs = ServerService.getAllServerInterfaces()

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.filter(listen_port=value).exists():
            self.add_error( 'listen_port',
                forms.ValidationError(
                    "Tento port je už obsazený."
                )
            )

        return value



class UserUpdateForm(BootstrapFormMixin,forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]



class ProfileAdminForm(BootstrapFormMixin,forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["verified", "key_limit"]