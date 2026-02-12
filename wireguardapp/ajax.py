from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from wireguardapp.models import Interface, Peer, PeerSnapshot, Key
from django.http import JsonResponse
import json


from .services.client import deleteClient,generateClientConf
from .services.server import checkServer,startServer,stopServer,getWGPeerConnectionState

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
        {"success": False,"body": "Error getting key"},
        status=400
        )
    
    confFull = generateClientConf(key)
    confSplit = generateClientConf(key,True)

    return JsonResponse({"success": False,'body1': confFull, "body2":confSplit})


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

@require_POST
@login_required
def deletekey(request):
    user = request.user
    data = json.loads(request.body)
    keyId = data['id']
    key = get_object_or_404(
        Key,
        id=keyId
    )
    if (key.user != user or not user.is_superuser):
        return JsonResponse({"success": False, "body" : "Musíte být vlastníkem klíče nebo superuser"})
    
    result = deleteClient(user,key)
    if result:
        return JsonResponse({"success": False, "body" : "Server v tuto chvíli není online."})
    
    return JsonResponse({"success": True, "body" : "Klíč byl odstraněn"})

@require_POST
@login_required
def toggleServer(request):
    user = request.user
    if not user.is_superuser:
        return JsonResponse({"success" : False, "error" : "Nejste supersuper pro vypínání/zapínání serveru."})

    if checkServer():
        result = stopServer()
    else:
        result = startServer()

    if result:
        return JsonResponse({"success" : False, "error" : result})
    else:
        return JsonResponse({"success" : True, "is_up": checkServer()})

@require_POST
@login_required
def getpeerstate(request):
    return JsonResponse({"peers":getWGPeerConnectionState()})