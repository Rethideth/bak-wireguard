from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from wireguardapp.models import Interface, Peer, PeerAllowedIP, PeerSnapshot, Key
from django.http import JsonResponse
import json

from django.core.exceptions import PermissionDenied

from .forms import CustomUserCreationForm
# Create your views here.

CLIENT_ADDRESS = "10.10.0.2/24"
ENDPOINT = "127.0.0.1:51820"
ALLOWEDIPS = "10.10.0.1/32"

def home(request):
    return render(request, 'wireguardapp/main.html')

@login_required
def test(request):
    return render(request, 'wireguardapp/test.html')

def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # auto-login after registration
            return redirect('/')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

@login_required
def mykeys(request):
    keys = Key.objects.filter(user=request.user)

    return render(request, 'wireguardapp/mykeys.html', {'keys':keys})

def getconfajax(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        keytext = data.get('public_key')
        key = Key.objects.get(public_key = keytext)
        title = f"{request.user.username}"
        

        conf = "[Interface]\n"
        conf = conf + f"Address = {CLIENT_ADDRESS}\n"
        conf = conf + f"PrivateKey = {key.private_key}\n\n"

        conf = conf + "[Peer]\n"
        conf = conf + f"PublicKey = {Key.objects.get(key_type='server').public_key}\n"
        conf = conf + f"EndPoint = {ENDPOINT}\n"
        conf = conf + f"AllowedIPs = {ALLOWEDIPS}\n"
        conf = conf + f"PersistentKeepalive = 5\n"

        return JsonResponse({'title':title,'config': conf})
    pass


def viewlogs(request):
    if not request.user.is_authenticated:
        return redirect("login")

    if not request.user.is_superuser:
        raise PermissionDenied
    return render(request, 'wireguardapp/logs.html')