from django import forms

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from wireguardapp.models import Interface, Peer, PeerSnapshot, Key

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
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")



class ClientKeyForm(forms.Form):
    name = forms.CharField(max_length=255)



class ServerKeyForm(forms.Form):
    def checkInterface(value):
        try:
            interface = ipaddress.ip_interface(value) 
        except ValueError:
            raise forms.ValidationError("Vložte správnou ip addresu se net maskou")
        

        serverInterfaces = Interface.objects.filter(
            interface_type=Interface.SERVER).values_list('ip_address',flat=True)
        for inf in serverInterfaces:
            if ipaddress.IPv4Interface(inf).network.overlaps(interface.network):
                raise forms.ValidationError(f"Tato síť je už obsazena. (síť: {inf})")

        return interface
    

    name = forms.CharField(max_length=255)
    ip_interface = forms.CharField(help_text='Například: 10.10.0.1/24',
                                 validators=[checkInterface])
    endpoint = forms.GenericIPAddressField(protocol='ipv4')
    







    