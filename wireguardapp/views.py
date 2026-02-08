from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from wireguardapp.models import Interface, Peer, PeerAllowedIP, PeerSnapshot, Key
from django.http import JsonResponse
import json

from .service.wireguard import generateClientConf
from .service.dbcommands import createNewClient,deleteClient

from django.core.exceptions import PermissionDenied

from .forms import CustomUserCreationForm


from datetime import datetime
from django.utils import timezone
import os
import getpass
# Create your views here.


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

@require_POST
@login_required
def getconfajax(request):
    data = json.loads(request.body)
    key = get_object_or_404(
        Key,
        id=data['id'],
        user=request.user
    )

    if not key:
        return JsonResponse(
        {"error": "public_key is required"},
        status=400
        )
    
    conf = generateClientConf(key)

    return JsonResponse({'title':request.user.username,'config': conf})

@require_POST
@login_required
def newkey(request):
    user = request.user
    name = str(timezone.now().time())
    createNewClient(user,name)

    return redirect('mykeys')

@require_POST
@login_required
def deletekey(request,key):
    user = request.user
    key = get_object_or_404(
        Key,
        id=key,
        user=request.user
    )
    result = deleteClient(user,key)
    if result:
        return redirect('home')
    return redirect('mykeys')

@login_required
def viewlogs(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    path = os.getcwd()
    userDjango = getpass.getuser()
    return render(request, 'wireguardapp/logs.html', {'test1': path, "test2":userDjango} )

@require_POST
@login_required
def updatekeyname(request):
    data = json.loads(request.body)

    key = get_object_or_404(
        Key,
        id=data["key_id"],
        user=request.user
    )

    key.name = data["name"]
    key.save(update_fields=["name"])

    return JsonResponse({"success": True})

def dbdown(request):
    return render(request, 'wireguardapp/dbdown.html', status=503)