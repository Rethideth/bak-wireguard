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

from .forms import CustomUserCreationForm, ClientKeyForm,ServerInterfaceForm,UserUpdateForm,ProfileAdminForm

from datetime import datetime
from django.utils import timezone
from django.http import HttpRequest,HttpResponse, HttpResponseNotFound
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
            user = ClientService.create_user(form=form)
            login(request, user)  # auto-login after registration
            return redirect('/')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

@login_required
def mykeys(request : HttpRequest):
    keys = ClientService.get_user_keys(request.user)
    form = ClientKeyForm()
    grouped = list(dict())
    profile = ClientService.get_user_profile(request.user)
    for key in keys:
        inf = ClientService.get_clients_server_interface(key)
        grouped.append({"key":key, 'interfaceName' : inf.interface_key.name, 'interfaceUp': ServerService.check_server(inf) })
    return render(request, 'wireguardapp/mykeys.html', {'keys':grouped, "form":form, "profile" : profile})



@login_required
def newkey(request : HttpRequest):
    if request.method == "POST":
        form = ClientKeyForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            result = ClientService.create_new_client(
                user=request.user,
                name=data['name'],
                server_interface=data['interface'])
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
    interfaces = ServerService.get_all_server_interfaces()

    for interface in interfaces:
        interfaceInfo.append({
            "interface": interface,
            "peers": ServerService.get_server_interface_peers(interface) ,
            "isUp":ServerService.check_server(server_interface=interface)})
        

    return render(request, 'wireguardapp/serverlist.html' , {"grouped":interfaceInfo})

@login_required
def serverinterface(request :HttpRequest, id:int):
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied
    
    interface = ServerService.get_server_interface_by_id(id)
    peers = ServerService.get_server_interface_peers(interface)
    isUp = ServerService.check_server(interface)

    networks = ServerService.get_network_interfaces()

    return render (request, 'wireguardapp/server.html', {"interface":interface,"peers" : peers, "isUp":isUp, "networks":networks})

def serverinterfaceform(request, id=None):
    """
    Handles create and update of a Server Interface.
    If pk is provided, edits an existing interface.
    """

    if id:
        interface = ServerService.get_server_interface_by_id(id)
        if ServerService.check_server(interface):
            messages.error(request=request, message="Nejdřív vypněte server než změníte nastavení rozhraní.")
            return redirect('server', id=id)
    else:
        interface = None

    if request.method == "POST":
        form = ServerInterfaceForm(request.POST, instance=interface)
        if form.is_valid():
            if id:
                result = ServerService.update_server(interface=interface,changed=form.changed_data)
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

                result = ServerService.create_new_server(
                    name=name,
                    ip_network=ip_network,
                    network_mask=mask,
                    endpoint=endpoint,
                    port=port)
                if result:
                    messages.error(request=request,message=result)
                else:
                    return redirect("allservers") 
        
            
    else:
        form = ServerInterfaceForm(instance=interface)

    return render(request, "wireguardapp/forminterface.html", {"form": form, "id": id})   


@login_required
def deleteinterface(request :HttpRequest):
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied
    if request.method == "POST":
        id = request.POST.get('id')
        interface = ServerService.get_server_interface_by_id(id)
        if not ServerService.check_server(interface):
            ServerService.remove_server(interface)
        else:
            messages.error(request=request,message="Vypněte server předtím, než ho odstraníte.")
    
    return redirect('allserver')
        


def dbdown(request : HttpRequest):
    return render(request, 'wireguardapp/dbdown.html', status=503)


@login_required
def downlandConf(request : HttpRequest):
    id = request.GET.get('id')
    full = request.GET.get('full')
    user = request.user
    key = ClientService.get_key_by_id(id)

    if not ClientService.check_user_of_key(user = user, key = key):
        raise PermissionDenied
    if not ClientService.get_user_profile(user=user).verified:
        messages.info(request=request, message="Nejste ověřeni.")
        return

    if full == 'y':
        content = ClientService.generate_client_conf(user,key,False)
    else:
        content = ClientService.generate_client_conf(user,key,True)
    response = HttpResponse(content, content_type="application/octet-stream")
    response['Content-Disposition'] = 'attachment; filename="wg.conf"'
    response["Content-Transfer-Encoding"] = "binary"

    return response

@login_required
def listusers(request : HttpRequest):
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied
    
    users = ServerService.get_all_client_users()

    grouped = list(dict())
    for user in users:
        grouped.append({"user":user, "profile": ClientService.get_user_profile(user=user)})

    return render(request, 'wireguardapp/userlist.html', {"users":grouped})
    
@login_required
def newuser(request :HttpRequest):
    if not request.user.is_superuser or not request.user.is_staff:
        raise PermissionDenied
    
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            ClientService.create_user(form=form)

            return redirect('listusers')

    else:
        form = CustomUserCreationForm()

    return render(request, 'wireguardapp/newuser.html',{'form':form})


@login_required
def usersettings(request: HttpRequest, id):

    target_user = ClientService.get_user_from_id(id)
    profile = ClientService.get_user_profile(target_user)

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
            password_form = SetPasswordForm(target_user, request.POST)
            profile_form = ProfileAdminForm(request.POST, instance=profile)
        else:
            password_form = PasswordChangeForm(target_user, request.POST)

        # Detect which form was submitted
        if "update_profile" in request.POST:
            if user_form.is_valid():
                user_form.save()
                if request.user.is_staff and profile_form.is_valid():
                    profile_form.save()
                messages.success(request, "Profil uložen.")
                return redirect("usersettings", id=id)
            # If invalid, we stay on page and errors will render

        elif "change_password" in request.POST:
            if password_form.is_valid():
                user = password_form.save()
                if request.user == target_user:
                    update_session_auth_hash(request, user)
                messages.success(request, "Heslo změněno.")
                return redirect("usersettings", id=id)
            # else: errors will show

        elif "delete_user" in request.POST:
            ServerService.remove_user(target_user.pk)
            if request.user.is_superuser or request.user.is_staff:
                return redirect("listusers")
            else:
                return redirect("/")

    else:
        # GET request, instantiate empty forms
        user_form = UserUpdateForm(instance=target_user)
        password_form = SetPasswordForm(target_user) if request.user.is_staff else PasswordChangeForm(target_user)
        if request.user.is_staff:
            profile_form = ProfileAdminForm(instance=profile)

    return render(request, "wireguardapp/usersettings.html", {
        "user_form": user_form,
        "password_form": password_form,
        "profile_form": profile_form,
        "target_user": target_user,
        "profile": profile
    })