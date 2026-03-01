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
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")



class ClientKeyForm(forms.Form):
    name = forms.CharField(max_length=255)
    interface = forms.ModelChoiceField(
        queryset=selectAllServerInterfaces(),
        required=True
    )



class ServerInterfaceForm(forms.Form):
    def checkInterface(value):
        try:
            network = ipaddress.ip_network(value) 
        except ValueError:
            raise forms.ValidationError("Vložte správnou ip adresu sítě s net maskou.")
        

        serverInterfaces = selectAllServerInterfaces().values_list('ip_address',flat=True)
        for inf in serverInterfaces:
            taken = ipaddress.ip_interface(inf)
            if taken.network.overlaps(network):
                raise forms.ValidationError(f"Tato síť je už obsazena. (síť: {inf})")

        return network
    
    def checkPort(value):
        serverPorts = selectAllServerInterfaces().values_list('listen_port',flat=True)
        for port in serverPorts:
            if port == value:
                raise forms.ValidationError(f"Tento port je už obsazený jiným serverem.")
        

    name = forms.CharField(max_length=255)
    ip_network = forms.CharField(help_text='Například: 10.10.0.0/24',
                                 validators=[checkInterface])
    endpoint = forms.CharField(max_length=64)
    port = forms.IntegerField(min_value=0,max_value=65535,initial=51820,validators=[checkPort])







    