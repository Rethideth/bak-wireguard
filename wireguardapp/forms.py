from django import forms

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from wireguardapp.models import Interface, Peer, PeerSnapshot, Key
from wireguardapp.services.server import selectAllServerInterfaces

from datetime import datetime
import ipaddress




class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            "autocomplete": "email"
        }),
        required=True
    )

    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "autocomplete": "username"
        }),
        required=True

    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name", "last_name","password1", "password2")



class ClientKeyForm(forms.Form):
    name = forms.CharField(max_length=255)
    interface = forms.ModelChoiceField(
        queryset=selectAllServerInterfaces(),
        required=True
    )


class ServerInterfaceForm(forms.ModelForm):

    class Meta:
        model = Interface
        fields = [
            "name",
            "ip_address",
            "server_endpoint",
            "listen_port",
        ]

    def clean_ip_address(self):
        value = self.cleaned_data["ip_address"]

        try:
            network = ipaddress.ip_network(value)
        except ValueError:
            raise forms.ValidationError(
                "Vložte správnou ip adresu s net maskou."
            )

        qs = selectAllServerInterfaces()

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        for inf in qs.values_list("ip_address", flat=True):
            taken = ipaddress.ip_interface(inf)
            if taken.network.overlaps(network):
                raise forms.ValidationError(
                    f"Tato síť je už obsazena. (síť: {inf})"
                )

        return value

    def clean_listen_port(self):
        value = self.cleaned_data["listen_port"]

        qs = selectAllServerInterfaces()

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.filter(listen_port=value).exists():
            raise forms.ValidationError(
                "Tento port je už obsazený."
            )

        return value




    