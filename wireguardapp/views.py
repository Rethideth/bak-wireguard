from django.shortcuts import render,redirect,get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from wireguardapp.models import Interface, Peer, PeerSnapshot, Key


from .services.client import createNewClient
from .services.server import createNewServer,checkServer,getServerInterfacePeers,getLastDayDiffSnapshot, getServerInterface

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
    if request.method == "POST":
        result = createNewClient(
            user = request.user,
            name = None,
        )
        if result:
            messages.error(request = request, message = result)

    return redirect("mykeys")



def dbdown(request):
    return render(request, 'wireguardapp/dbdown.html', status=503)

@login_required
def viewlogs(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    
    interface = getServerInterface()
    grouped = getLastDayDiffSnapshot(interface)

    return render(request, 'wireguardapp/logs.html' , {"interface":interface, "last_day_snapshots" : grouped, 'model' : PeerSnapshot})


@login_required
def serverinterfaces(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    interface = getServerInterface()
    serverPeers = getServerInterfacePeers(interface)

    return render(request, 'wireguardapp/server.html' , {"interface" : interface, "peers" : serverPeers, "is_up" : checkServer(interface)})


def test(request):
    return render(request, 'wireguardapp/test.html' )