from django.shortcuts import render,redirect,get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm,SetPasswordForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from wireguardapp.models import Interface, Peer, PeerSnapshot, Key,Profile

from .services.clientservice import ClientService
from .services.serverservice import ServerService
from django.core.exceptions import PermissionDenied

from .forms import CustomUserCreationForm, ClientKeyForm,ServerInterfaceForm,UserUpdateForm,ProfileAdminForm,BootstrapChangePasswordForm,BootstrapSetPasswordForm

from datetime import datetime
from django.utils import timezone
from django.http import HttpRequest,HttpResponse, HttpResponseNotFound
import logging
from django.conf import settings

logger = logging.getLogger('test')
# Create your views here.


def home(request : HttpRequest):
    """ Home page view. Has a introduction of this """
    return render(request, 'wireguardapp/main.html')

@login_required
def test(request : HttpRequest):
    return render(request, 'wireguardapp/test.html')

def register(request : HttpRequest):
    """ Register view. Will create a user with a profile and log in the user."""
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user = ClientService.createUser(user)
            form.save_m2m()
            login(request, user)  # auto-login after registration
            return redirect('/')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

@login_required
def mykeys(request : HttpRequest):
    """ View that shows all keys which the user owns. Can add,remove and generate configuration for a key. """
    keys = ClientService.getUserKeys(request.user)
    form = ClientKeyForm()
    grouped = list(dict())
    profile = ClientService.getUserProfile(request.user)
    for key in keys:
        inf = ClientService.getClientsServerInterface(key)
        grouped.append({"key":key, 'interfaceName' : inf.interface_key.name, 'interfaceUp': ServerService.checkServer(inf) })
    return render(request, 'wireguardapp/mykeys.html', {'keys':grouped, "form":form, "profile" : profile})



@login_required
def newkey(request : HttpRequest):
    """ Form reciever that creates a new key for the user. """
    if request.method == "POST":
        form = ClientKeyForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            result = ClientService.createNewClient(
                user=request.user,
                name=data['name'],
                serverInterface=data['interface'])
            if result:
                messages.error(request = request, message = result)
        else:
            messages.error(request=request,message=form.errors.as_text())

    return redirect("mykeys")

@login_required
def serverinterfaces(request : HttpRequest):
    """ View that shows all server interfaces and their basic information. """
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied

    interfaceInfo = list(dict())
    interfaces = ServerService.getAllServerInterfaces()

    for interface in interfaces:
        interfaceInfo.append({
            "interface": interface,
            "peers": ServerService.getServerInterfacePeers(interface) ,
            "isUp":ServerService.checkServer(serverInterface=interface)})
        

    return render(request, 'wireguardapp/serverlist.html' , {"grouped":interfaceInfo})

@login_required
def serverinterface(request :HttpRequest, id:int):
    """ View that shows the server interface dashboard. Information about interface configuration, its peers and current connection state. """
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied
    
    interface = ServerService.getServerInterfaceById(id)
    peers = ServerService.getServerInterfacePeers(interface)
    isUp = ServerService.checkServer(interface)

    networks = ServerService.getNetworkInterfaces()

    return render (request, 'wireguardapp/server.html', {"interface":interface,"peers" : peers, "isUp":isUp, "networks":networks})

def serverinterfaceform(request, id=None):
    """
    View and form reciever that handles create and update of a server interface.
    If pk is provided, edits an existing interface.
    """

    if id:
        interface = ServerService.getServerInterfaceById(id)
        if ServerService.checkServer(interface):
            messages.error(request=request, message="Nejdřív vypněte server než změníte nastavení rozhraní.")
            return redirect('server', id=id)
    else:
        interface = None

    if request.method == "POST":
        form = ServerInterfaceForm(request.POST, instance=interface)
        if form.is_valid():
            if id:
                result = ServerService.updateServer(interface=interface,changed=form.changed_data)
                if result:
                    messages.error(request=request,message=result)
                else:
                    return redirect('server', id=id)
            else:
                data = form.cleaned_data
                name = data['server_name']
                ip_network = data['ip_network']
                mask = data['ip_network_mask']
                endpoint = data['server_endpoint']
                port = data['listen_port']
                clienttoclient = data['client_to_client']

                result = ServerService.createNewServer(
                    name=name,
                    ipNetwork=ip_network,
                    networkMask=mask,
                    endpoint=endpoint,
                    port=port,
                    clientToClient=clienttoclient)
                if result:
                    messages.error(request=request,message=result)
                else:
                    return redirect("allservers") 
        
            
    else:
        form = ServerInterfaceForm(instance=interface)

    return render(request, "wireguardapp/forminterface.html", {"form": form, "id": id})   


@login_required
def deleteinterface(request :HttpRequest):
    """ Removes a server interface. """
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied
    if request.method == "POST":
        id = request.POST.get('id')
        interface = ServerService.getServerInterfaceById(id)
        if not ServerService.checkServer(interface):
            ServerService.removeServer(interface)
        else:
            messages.error(request=request,message="Vypněte server předtím, než ho odstraníte.")
            return redirect('server', id=id)
    
    return redirect('allservers')
        


def dbdown(request : HttpRequest):
    """ View that shows, when database service is unreachable. """
    return render(request, 'wireguardapp/dbdown.html', status=503)


@login_required
def downlandConf(request : HttpRequest):
    """ Downland a configuration of the given key by id and if full or split tunel. """
    id = request.GET.get('id')
    full = request.GET.get('full')
    user = request.user
    key = ClientService.getKeyById(id)

    if not ClientService.checkUserOfKey(user = user, key = key):
        raise PermissionDenied
    if not ClientService.getUserProfile(user=user).verified:
        messages.info(request=request, message="Nejste ověřeni.")
        return

    if full == 'y':
        content = ClientService.generateClientConf(user,key,False)
    else:
        content = ClientService.generateClientConf(user,key,True)
    response = HttpResponse(content, content_type="application/octet-stream")
    response['Content-Disposition'] = 'attachment; filename="wg.conf"'
    response["Content-Transfer-Encoding"] = "binary"

    return response

@login_required
def listusers(request : HttpRequest):
    """ Lists all users, their basic information and link to ther user options view. """
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied
    
    users = ServerService.getAllClientUsers()

    grouped = list(dict())
    for user in users:
        grouped.append({"user":user, "profile": ClientService.getUserProfile(user=user)})

    return render(request, 'wireguardapp/userlist.html', {"users":grouped})
    
@login_required
def newuser(request :HttpRequest):
    """ Admin based form view that creates an user. """
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied
    
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            ClientService.createUser(user=user)
            form.save_m2m()

            return redirect('listusers')

    else:
        form = CustomUserCreationForm()

    return render(request, 'wireguardapp/newuser.html',{'form':form})


@login_required
def usersettings(request: HttpRequest, id):
    """ 
    View that shows the target user setting. Allow changing of user information and reset their password. 
    If admin uses this page, changes change password (need current password to change) to set password.
    Also allows setting key limit and verified status.
    """

    target_user = ClientService.getUserFromId(id)
    profile = ClientService.getUserProfile(target_user)

    # security
    if request.user != target_user and not request.user.is_staff:
        return redirect("/")

    password_form = None
    profile_form = None
    user_form = None

    if request.method == "POST":

        # Initialize all forms correctly
        user_form = UserUpdateForm(request.POST, instance=target_user)
        if request.user.is_staff:
            password_form = BootstrapSetPasswordForm(target_user, request.POST)
            profile_form = ProfileAdminForm(request.POST, instance=profile)
        else:
            password_form = BootstrapChangePasswordForm(target_user, request.POST)

        # Detect which form was submitted
        if "update_profile" in request.POST:
            if user_form.is_valid():
                user = user_form.save()
                if request.user.is_staff and profile_form.is_valid():
                    profile = profile_form.save()
                    if profile.verified:
                        ServerService.connectUserToWg(user)
                    else:
                        ServerService.disconnectUserFromWg(user)

                messages.success(request, "Profil uložen.")
                return redirect("usersettings", id=id)

        elif "change_password" in request.POST:
            if password_form.is_valid():
                user = password_form.save()
                if request.user == target_user:
                    update_session_auth_hash(request, user)
                messages.success(request, "Heslo změněno.")
                return redirect("usersettings", id=id)
            # else: errors will show

        elif "delete_user" in request.POST:
            ServerService.removeUser(target_user.pk)
            if request.user.is_superuser or request.user.is_staff:
                return redirect("listusers")
            else:
                return redirect("/")

    else:
        # GET request, instantiate empty forms
        user_form = UserUpdateForm(instance=target_user)
        password_form = BootstrapSetPasswordForm(target_user) if request.user.is_staff else BootstrapChangePasswordForm(target_user)
        if request.user.is_staff:
            profile_form = ProfileAdminForm(instance=profile)

    return render(request, "wireguardapp/usersettings.html", {
        "user_form": user_form,
        "password_form": password_form,
        "profile_form": profile_form,
        "target_user": target_user,
        "profile": profile
    })

@login_required
def userkeys(request :HttpRequest, id:int):
    """ View that shows a list of user keys and all their information """
    user = ClientService.getUserFromId(id)
    
    if request.user != user and not request.user.is_staff:
        return redirect("/")
    
    keys = ClientService.getUserKeys(user)
    grouped = list(dict())
    for key in keys:
        peer = ClientService.getPeerFromKey(key)
        interface = ClientService.getInterfaceFromKey(key)
        server = ClientService.getClientsServerInterface(key)
        endpoints = ClientService.getEndpointOfPeer(peer)
        grouped.append({
            "key": key,
            "interface":interface,
            "server":server,
            "peer": peer,
            "endpoints": endpoints,
        })
    return render(request, 'wireguardapp/userkeys.html', {"infos": grouped, "user":user})

def help(request :HttpRequest):
    """ View that shows instruction for how to use this web managment interface for wireguard. """
    return render(request, 'wireguardapp/help.html', {})