from django.shortcuts import render,redirect,get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from wireguardapp.models import Interface, Peer, PeerAllowedIP, PeerSnapshot, Key
from django.http import JsonResponse
import json


from .service.client import createNewClient,deleteClient

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
def newkey(request):
    user = request.user
    name = str(timezone.now())
    result = createNewClient(user,name)
    if result:
        messages.error(request, 'Error, interface serveru je nyní offline. Skuste znova za chvíli.\n'+result)

    return redirect('mykeys')



def dbdown(request):
    return render(request, 'wireguardapp/dbdown.html', status=503)

@login_required
def viewlogs(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    snapshots = PeerSnapshot.objects.select_related(
        "peer", "peer__interface", "peer__peer_key"
    ).filter(
        peer__interface__interface_type='server'
    ).order_by("peer__interface__name", "peer__peer_key", "-collected_at")

    
    # Group snapshots by interface
    grouped = dict()
    for snap in snapshots:
        interface = snap.peer.interface.name
        if interface not in grouped:
            grouped[interface] = {
                "snapshots": [],
            }
        grouped[interface]['snapshots'].append(snap)

    return render(request, 'wireguardapp/logs.html' , {"grouped_snapshots" : grouped, 'model' : PeerSnapshot})


@login_required
def serverinterfaces(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    interfaces = Interface.objects.select_related(
        "interface_key",
    ).filter(interface_type = Interface.SERVER)

    grouped = dict()
    for face in interfaces:
        serverPeers = Peer.objects.filter(peer_key = face.interface_key)
        grouped[face] = serverPeers


    return render(request, 'wireguardapp/server.html' , {"interfaces" : grouped})

