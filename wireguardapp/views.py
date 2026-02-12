from django.shortcuts import render,redirect,get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from wireguardapp.models import Interface, Peer, PeerSnapshot, Key
from django.http import JsonResponse
import json


from .services.client import createNewClient
from .services.server import createNewServer,checkServer,getServerInterfaceWithPeers,getLatestPeerSnapshots,getServerPeerSnapshots,getServerInterface

from django.core.exceptions import PermissionDenied

from .forms import CustomUserCreationForm, ClientKeyForm,ServerKeyForm


from datetime import datetime
from django.utils import timezone
import logging
from django.conf import settings

logger = logging.getLogger('test')
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



@login_required
def newkey(request):
    if request.user.is_superuser:
        formClass = ServerKeyForm
    else:
        formClass = ClientKeyForm

    if request.method == "POST":
        form = formClass(request.POST)
        if form.is_valid():
            data = form.cleaned_data   

            if isinstance(form, ServerKeyForm):
                if Interface.objects.filter(interface_type = Interface.SERVER).count() >0:
                    form.add_error(None, "Nemohou existovat více než jeden server interface.")
                    return render(request, 'wireguardapp/newkey.html', {'form':form})
                
                result = createNewServer(
                    request.user, 
                    data['name'], 
                    str(data['ip_interface']),
                    data['endpoint'] )
                

            elif isinstance(form, ClientKeyForm):
                result = createNewClient(
                    user = request.user,
                    name = data['name'],
                )
            if result:
                form.add_error(None,result)
                return render(request, 'wireguardapp/newkey.html', {'form':form})


            return redirect("mykeys")
    else:
        form = formClass()

    return render(request, 'wireguardapp/newkey.html',{'form':form})


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

    
    interface = getServerInterface()
    grouped = getLatestPeerSnapshots()
    

    return render(request, 'wireguardapp/logs.html' , {"interface":interface, "latest_snapshots" : grouped, 'model' : PeerSnapshot})


@login_required
def serverinterfaces(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    interface, serverPeers = getServerInterfaceWithPeers()

    return render(request, 'wireguardapp/server.html' , {"interface" : interface, "peers":serverPeers, "is_up":checkServer()})


def test(request):
    return render(request, 'wireguardapp/test.html' )