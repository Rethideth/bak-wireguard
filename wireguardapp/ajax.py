from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from wireguardapp.models import Interface, Peer, PeerSnapshot, Key
from django.http import JsonResponse,HttpRequest
import json

from .services.client import removeClient,generateClientConf,getKeyById
from .services.server import checkServer,startServer,stopServer,getWGPeerConnectionState,getServerInterface,getServerInterfaceFromId

@require_POST
@login_required
def getconfajax(request:HttpRequest):
    data = json.loads(request.body)

    key = getKeyById(data['id'])

    if not key:
        return JsonResponse(
        {"success": False,"body": "Key does not exist."},
        status=404
        )
    
    if key.user != request.user and not request.user.is_superuser:
        return JsonResponse(
        {"success": False,"body": "You arent the owner of the key or superuser."},
        status=403
        )
    

    confFull = generateClientConf(key)
    confSplit = generateClientConf(key,True)

    return JsonResponse({"success": False,'body1': confFull, "body2":confSplit})


@require_POST
@login_required
def updatekeyname(request:HttpRequest):
    data = json.loads(request.body)

    key = getKeyById(data["key_id"])

    if not(key.user == request.user or request.user.is_superuser):
        return JsonResponse({"success":False})

    key.name = data["name"]
    key.save(update_fields=["name"])

    return JsonResponse({"success": True})

@require_POST
@login_required
def deletekey(request):
    user = request.user
    data = json.loads(request.body)
    key = getKeyById(data['id'])
    
    if key.user != user:
        if not user.is_superuser:
            return JsonResponse({"success": False, "body" : "Musíte být vlastníkem klíče nebo superuser."})
    
    result = removeClient(user,key)
    if result:
        return JsonResponse({"success": True, "body" : "Server v tuto chvíli není online."})
    
    return JsonResponse({"success": True, "body" : "Klíč byl odstraněn"})

@require_POST
@login_required
def toggleServer(request):
    user = request.user
    if not user.is_superuser:
        return JsonResponse({"success" : False, "error" : "Nejste supersuper pro vypínání/zapínání serveru."})
    
    data = json.loads(request.body)

    serverInterface = getServerInterfaceFromId(data['id'])

    if checkServer(serverInterface):
        result = stopServer(serverInterface)
    else:
        result = startServer(serverInterface,data['interface'])

    if result:
        return JsonResponse({"success" : False, "error" : result})
    else:
        return JsonResponse({"success" : True, "is_up": checkServer(serverInterface)})

@require_POST
@login_required
def getpeerstate(request):
    serverInterface = getServerInterface()
    return JsonResponse({"peers":getWGPeerConnectionState(serverInterface=serverInterface)})