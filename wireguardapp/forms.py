from django import forms

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from wireguardapp.models import Interface, Peer, PeerAllowedIP, PeerSnapshot, Key

from datetime import datetime

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


<<<<<<< HEAD
class NewKeyForm(forms.ModelForm):
    name = forms.CharField(
        max_length=64,
    )
=======
class CustomKeyList(forms.ModelForm):
    
>>>>>>> refs/remotes/origin/main
    pass