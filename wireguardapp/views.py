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
CZ_ADDRESS = ""
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

@login_required
def getconfajax(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        keytext = data.get('public_key')
        key = Key.objects.get(public_key = keytext)
        title = f"{request.user.username}"

        clientAddress = f"10.10.0.{key.pk}/32"
        serverPeer = Peer.objects.get(peer_type = 'server')
        clientInterface = Interface.objects.get(public_key = key)

        conf = f"""
[Interface]
PrivateKey = {clientInterface.public_key.private_key}
Address = {clientInterface.ip_address}

[Peer]
PublicKey = {serverPeer.public_key.public_key}
EndPoint = {ENDPOINT}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = {serverPeer.persistent_keepalive}
""".strip()

        return JsonResponse({'title':title,'config': conf})


@login_required
def newkey(request):
    if request.method == 'POST':
        pass

@login_required
def viewlogs(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    
    return render(request, 'wireguardapp/logs.html')