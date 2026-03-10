from django.shortcuts import render,redirect,get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from wireguardapp.models import Interface, Peer, PeerSnapshot, Key


from .services.client import createNewClient, generateClientConf,getKeyById,getClientsServerInterface,checkUserOfKey,getUserProfile,createNewUser,getUsersKeys
from .services.server import createNewServer,checkServer,getServerInterfacePeers,getServerInterfaces,getServerInterfaceFromId,removeServer,getNetworkInterfaces,getInterfacePeersTotalBytes,getAllClientUsers,removeUser,updateServer

from django.core.exceptions import PermissionDenied

from .forms import CustomUserCreationForm, ClientKeyForm,ServerInterfaceForm

from datetime import datetime
from django.utils import timezone
from django.http import HttpRequest,HttpResponse
import logging
from django.conf import settings

logger = logging.getLogger('test')
# Create your views here.


def home(request : HttpRequest):
    return render(request, 'wireguardapp/main.html')

@login_required
def test(request : HttpRequest):
    return render(request, 'wireguardapp/test.html')


def register(request : HttpRequest):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = createNewUser(form=form)
            login(request, user)  # auto-login after registration
            return redirect('/')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

@login_required
def mykeys(request : HttpRequest):
    keys = getUsersKeys(request.user)
    form = ClientKeyForm()
    grouped = list(dict())
    for key in keys:
        inf =getClientsServerInterface(key)
        grouped.append({"key":key, 'interfaceName' : inf.interface_key.name, 'interfaceUp': checkServer(inf) })
    return render(request, 'wireguardapp/mykeys.html', {'keys':grouped, "form":form})



@login_required
def newkey(request : HttpRequest):
    if request.method == "POST":
        form = ClientKeyForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            result = createNewClient(
                user = request.user,
                name = data['name'],
                serverInterface=data['interface']
            )
            if result:
                messages.error(request = request, message = result)
        else:
            messages.error(request=request,message=form.errors.as_text())

    return redirect("mykeys")

@login_required
def serverinterfaces(request : HttpRequest):
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied

    interfaceInfo = list(dict())
    interfaces = getServerInterfaces()

    for interface in interfaces:
        interfaceInfo.append({
            "interface": interface,
            "peers":getServerInterfacePeers(interface),
            "isUp":checkServer(interface)})
        

    return render(request, 'wireguardapp/serverlist.html' , {"grouped":interfaceInfo})

@login_required
def serverinterface(request :HttpRequest, id:int):
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied
    
    interface = getServerInterfaceFromId(id)
    peers = getServerInterfacePeers(interface)
    isUp = checkServer(interface)

    networks = getNetworkInterfaces()

    return render (request, 'wireguardapp/server.html', {"interface":interface,"peers" : peers, "isUp":isUp, "networks":networks})

    


@login_required
def newinterface(request : HttpRequest):
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied
    
    if request.method == "POST":
        form = ServerInterfaceForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            name = data['server_name']
            ip_network = data['ip_network']
            mask = data['ip_network_mask']
            endpoint = data['server_endpoint']
            port = data['listen_port']

            result = createNewServer(
                name=name,
                ipNetwork=ip_network,
                networkMask=mask,
                endpoint=endpoint,
                port=port)
            if result:
                messages.error(request=request,message=result)
            else:
                return redirect('allserver')
            
    else:
        form = ServerInterfaceForm()

    return render(request, "wireguardapp/newinterface.html", {"form" : form})

@login_required
def deleteinterface(request :HttpRequest):
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied
    if request.method == "POST":
        id = request.POST.get('id')
        interface = getServerInterfaceFromId(id)
        if not checkServer(interface):
            removeServer(interface)
        else:
            messages.error(request=request,message="Vypněte server předtím, než ho odstraníte.")
    
    return redirect('allserver')
        


def dbdown(request : HttpRequest):
    return render(request, 'wireguardapp/dbdown.html', status=503)

@login_required
def viewlogs(request : HttpRequest):
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied
    
    interfacesLogs = list(dict())
    interfaces = getServerInterfaces()
    
    for interface in interfaces:
        interfacesLogs.append({"interface": interface, "peer_total": getInterfacePeersTotalBytes(interface)})

    return render(request, 'wireguardapp/logs.html' , {"interfacesLogs":interfacesLogs, 'model' : PeerSnapshot})



@login_required
def downlandConf(request : HttpRequest):
    id = request.GET.get('id')
    full = request.GET.get('full')
    user = request.user
    key = getKeyById(id)

    if not checkUserOfKey(user = user, key = key):
        raise PermissionDenied
    if not getUserProfile(user=user).verified:
        messages.info(request=request, message="Nejste ověřeni.")
        return

    if full == 'y':
        content = generateClientConf(user,key,False)
    else:
        content = generateClientConf(user,key,True)
    response = HttpResponse(content, content_type="application/octet-stream")
    response['Content-Disposition'] = 'attachment; filename="wg.conf"'
    response["Content-Transfer-Encoding"] = "binary"

    return response

@login_required
def listusers(request : HttpRequest):
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied
    
    users = getAllClientUsers()

    grouped = list(dict())
    for user in users:
        grouped.append({"user":user, "profile": getUserProfile(user=user)})

    return render(request, 'wireguardapp/userlist.html', {"users":grouped})
    
@login_required
def newuser(request :HttpRequest):
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied
    
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            createNewUser(form=form)

            return redirect('listusers')

    else:
        form = CustomUserCreationForm()

    return render(request, 'wireguardapp/newuser.html',{'form':form})

@login_required
def deleteuser(request :HttpRequest):
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied
    
    if request.method == "POST":
        id = request.POST['id']
        result = removeUser(id)
        if result:
            messages.error(request=request,message=result)

    return redirect('listusers')

@login_required
def alterserver(request:HttpRequest, id:int):
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied
    
    interface = getServerInterfaceFromId(id)

    if request.method == "POST":
        form = ServerInterfaceForm(request.POST,instance=interface)
        if form.is_valid():
            result = updateServer(interface=interface,changed=form.changed_data)
            if result:
                pass
            else:
                return redirect('server',id=interface.pk)
    else:
        form = ServerInterfaceForm(instance=interface)
        form.server_name = interface.interface_key.name
        

    return render(request, 'wireguardapp/alterserver.html',{'form':form})

@login_required
def userprofile(request:HttpRequest, id:int):
    pass