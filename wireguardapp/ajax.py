from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from wireguardapp.models import Interface, Peer, PeerSnapshot, Key
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpRequest
import json

from django.db.models import Q

from .services.clientservice import ClientService
from .services.serverservice import ServerService

def is_admin(user : User) -> bool:
    """ Return True if user is an administrator, False if not. """
    return user.is_staff or user.is_superuser

@login_required
def getconfajax(request):
    """ 
    Ajax functions returns text of the key wireguard configuration by the given key. 
    Recieves an id ['id'] of the key.
    Returns a confirmation if it was succesful and its configuration for full and split tunel. error message if failed.
    """
    user = request.user

    keyId = request.GET.get("id")
    key = ClientService.getKeyById(keyId=keyId)

    if key == None:
        return JsonResponse(
            {"success": False, "error": "Klíč neexistuje."},
            status=404
        )
    
    if not (key.user == user or is_admin(user)):
        return JsonResponse(
            {"success": False, "error": "Nejste vlastníkem klíče nebo administrator."},
            status=403
        )
    
    confFull = ClientService.generateClientConf(user, key)
    confSplit = ClientService.generateClientConf(user, key, True)

    return JsonResponse({"success": True, 'body1': confFull, "body2": confSplit})


@require_POST
@login_required
def updatekeyname(request):
    """ 
    Updates the name of a given key. 
    Recieves an id of a key ['key_id'] and the name to change to ['name']
    Returns confirmation if the function was succesful.
    """
    data = json.loads(request.body)

    key = ClientService.getKeyById(data["key_id"])

    if not (key.user == request.user or is_admin(request.user)):
        return JsonResponse({"success": False})

    ClientService.changeKeyName(key, data["name"])

    return JsonResponse({"success": True})


@require_POST
@login_required
def deletekey(request):
    """ Removes a key based on its id ['id']."""
    user = request.user
    data = json.loads(request.body)
    key = ClientService.getKeyById(data['id'])
    
    if key.user != user:
        if not user.is_superuser or not user.is_staff:
            return JsonResponse({"success": False, "body": "Musíte být vlastníkem klíče nebo administrator."})
    
    result = ClientService.removeClient(key.user, key)
    profile = ClientService.getUserProfile(key.user)

    if result:
        return JsonResponse({"success": False, "body": result})
    
    return JsonResponse({"success": True, 
                         "body": "Klíč byl odstraněn", 
                         "key_count": profile.key_count,
                         "key_limit": profile.key_limit,})


@require_POST
@login_required
def toggleServer(request):
    """ Toggles a wireguard server interface state. """
    user = request.user
    if not is_admin(user):
        return JsonResponse({"success": False, "error": "Nejste administrator pro vypínání/zapínání serveru."})
    
    data = json.loads(request.body)

    serverInterface = ServerService.getServerInterfaceById(data['id'])

    if ServerService.checkServer(serverInterface):
        result = ServerService.stopServer(serverInterface)
    else:
        result = ServerService.startServer(serverInterface, data['interface'])

    if result:
        return JsonResponse({"success": False, "is_up" : ServerService.checkServer(serverInterface), "error": result})
    else:
        return JsonResponse({"success": True, "is_up": ServerService.checkServer(serverInterface)})


@login_required
def getpeerstate(request):
    """ Gets the wireguard server interface state. """
    user = request.user
    if not is_admin(user):
        return JsonResponse({"success": False, "error": "Nejste nejste administrator pro získání logů."})

    id = request.GET.get("interface")
    field = request.GET.get("field")
    state = request.GET.get("state")
    value = (request.GET.get("value") or "").strip().lower()
    
    serverInterface = ServerService.getServerInterfaceById(id)

    peers, count = ServerService.getWgPeerConnectionState(serverInterface, field, value, state)
    return JsonResponse({
        "success": True, 
        "peers": peers,
        "online_count" : count
    })


@require_POST
@login_required
def verifyUser(request):
    """ Switches the verify status of a user by its if ['id']. """
    user = request.user
    if not is_admin(user):
        return JsonResponse({"success": False, "error": "Nejste administrator pro získání logů."})
    
    data = json.loads(request.body)

    profile = ServerService.switchVerifyProfile(data['id'])

    return JsonResponse({"success": True, "verified": profile.verified})



@login_required
def filterUsers(request):
    user = request.user
    if not is_admin(user):
        return JsonResponse({"success": False, "error": "Nejste administrator pro získání listu uživatelů."})
    
    name = request.GET.get("name")
    username = request.GET.get("username")
    email = request.GET.get("email")
    verified = request.GET.get("verified")

    users = ServerService.getAllClientUsersFiltered(name,username,email,verified)

    data = [
        {
            "id": u.id,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "username": u.username,
            "email": u.email,
            "verified": u.profile.verified
        }
        for u in users
    ]

    return JsonResponse({"success":True,"data": data})

@login_required
def filterPeers(request):
    user = request.user
    if not is_admin(user):
        return JsonResponse({"success": False, "error": "Nejste administrator pro získání informací o peerů."})
    
    field = request.GET.get("field")
    value = request.GET.get("value")
    id = request.GET.get("interface")

    peers = ServerService.getServerInterfacePeersFiltered(serverInterface=ServerService.getServerInterfaceById(id),field=field,value=value)

    data = []
    for p in peers:
        data.append({
            "user": str(p.peer_interface.interface_key.user),
            "user_id": p.peer_interface.interface_key.user.id,
            "ip": str(p.peer_interface.ip_address),
            "name": p.peer_interface.interface_key.name,
            "rx": p.total_rx_bytes or 0,
            "tx": p.total_tx_bytes or 0,
        })

    return JsonResponse({"success":True,"data": data})


