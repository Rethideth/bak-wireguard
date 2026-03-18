from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from wireguardapp.models import Interface, Peer, PeerSnapshot, Key
from django.http import JsonResponse, HttpRequest
import json

from .services.clientservice import ClientService
from .services.serverservice import ServerService


@require_POST
@login_required
def getconfajax(request):
    """ 
    Ajax functions returns text of the key wireguard configuration by the given key. 
    Recieves an id ['id'] of the key.
    Returns a confirmation if it was succesful and its configuration for full and split tunel. error message if failed.
    """
    data = json.loads(request.body)
    user = request.user

    key = ClientService.getKeyById(data['id'])

    if not key:
        return JsonResponse(
            {"success": False, "error": "Klíč neexistuje."},
            status=404
        )
    
    if not (key.user == user or user.is_superuser or user.is_staff):
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

    if not (key.user == request.user or request.user.is_superuser):
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

    if result:
        return JsonResponse({"success": False, "body": result})
    
    return JsonResponse({"success": True, "body": "Klíč byl odstraněn"})


@require_POST
@login_required
def toggleServer(request):
    """ Toggles a wireguard server interface state. """
    user = request.user
    if not user.is_superuser or not user.is_staff:
        return JsonResponse({"success": False, "error": "Nejste administrator pro vypínání/zapínání serveru."})
    
    data = json.loads(request.body)

    serverInterface = ServerService.getServerInterfaceById(data['id'])

    if ServerService.checkServer(serverInterface):
        result = ServerService.stopServer(serverInterface)
    else:
        result = ServerService.startServer(serverInterface, data['interface'])

    if result:
        return JsonResponse({"success": False, "error": result})
    else:
        return JsonResponse({"success": True, "is_up": ServerService.checkServer(serverInterface)})


@require_POST
@login_required
def getpeerstate(request):
    """ Gets the wireguard server interface state. """
    user = request.user
    if not user.is_superuser or not user.is_staff:
        return JsonResponse({"success": False, "error": "Nejste nejste administrator pro získání logů."})
    
    data = json.loads(request.body)

    serverInterface = ServerService.getServerInterfaceById(data['id'])
    return JsonResponse({
        "success": True, 
        "peers": ServerService.getWgPeerConnectionState(serverInterface)
    })


@require_POST
@login_required
def verifyUser(request):
    """ Switches the verify status of a user by its if ['id']. """
    user = request.user
    if not user.is_superuser or not user.is_staff:
        return JsonResponse({"success": False, "error": "Nejste administrator pro získání logů."})
    
    data = json.loads(request.body)

    profile = ServerService.switchVerifyProfile(data['id'])

    return JsonResponse({"success": True, "verified": profile.verified})