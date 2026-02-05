from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from wireguardapp.models import Interface, Peer, PeerAllowedIP, PeerSnapshot, Key
from django.http import JsonResponse
import json
<<<<<<< HEAD

from .service.wireguard import generateClientConf
from .service.dbcommands import createNewClient
=======
>>>>>>> refs/remotes/origin/main

from django.core.exceptions import PermissionDenied

from .forms import CustomUserCreationForm


from datetime import datetime
from django.utils import timezone
import os
import getpass
# Create your views here.

<<<<<<< HEAD
=======
CLIENT_ADDRESS = "10.10.0.2/24"
ENDPOINT = "127.0.0.1:51820"
ALLOWEDIPS = "10.10.0.1/32"
>>>>>>> refs/remotes/origin/main

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

<<<<<<< HEAD
@login_required
def getconfajax(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        clientkeytext = data.get('public_key')

        if not clientkeytext:
            return JsonResponse(
            {"error": "public_key is required"},
            status=400
            )

        key = Key.objects.get(public_key = clientkeytext)
        
        conf = generateClientConf(key)

        return JsonResponse({'title':request.user.username,'config': conf})
=======
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
>>>>>>> refs/remotes/origin/main


@login_required
def newkey(request):
    if request.method == 'POST':
        user = request.user
        name = str(timezone.now().time())
        createNewClient(user,name)

        
    return redirect('mykeys')

@login_required
def deletekey(request):
    if request.method == "POST":

        pass

@login_required
def viewlogs(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    path = os.getcwd()
    userDjango = getpass.getuser()
    return render(request, 'wireguardapp/logs.html', {'test1': path, "test2":userDjango} )