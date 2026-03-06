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



#class ServerInterfaceForm(forms.Form):
#    def checkInterface(value): 
#        try: 
#            network = ipaddress.ip_network(value) 
#        except ValueError: 
#            raise forms.ValidationError("Vložte správnou ip adresu sítě s net maskou.")
#         
#        serverInterfaces = selectAllServerInterfaces().values_list('ip_network',flat=True)
#        for inf in serverInterfaces: 
#            taken = ipaddress.ip_network(inf)
#            if taken.overlaps(network):
#                raise forms.ValidationError(f"Tato síť je už obsazena. (síť: {inf})")
#            return network 
#    
#    def checkPort(value): 
#        serverPorts = selectAllServerInterfaces().values_list('listen_port',flat=True) 
#    
#        for port in serverPorts: 
#            if port == value: 
#                raise forms.ValidationError(f"Tento port je už obsazený jiným serverem.") 
#    
#    name = forms.CharField(max_length=255) 
#    ip_network = forms.CharField(help_text='Například: 10.10.0.0', validators=[checkInterface])
#    ip_network_mask = forms.IntegerField(min_value=0,max_value=31)
#    endpoint = forms.CharField(max_length=64)
#    port = forms.IntegerField(min_value=0,max_value=65535,initial=51820,validators=[checkPort])


class ServerInterfaceForm(forms.ModelForm):
    server_name = forms.CharField(max_length=255,required=False)
    ip_network_mask = forms.IntegerField(max_value=31, min_value=0)

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
                "Vložte správnou ip adresu s net maskou."
            )
            return cleaned

        qs = selectAllServerInterfaces()

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

        qs = selectAllServerInterfaces()

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.filter(listen_port=value).exists():
            self.add_error( 'listen_port',
                forms.ValidationError(
                    "Tento port je už obsazený."
                )
            )

        return value




    