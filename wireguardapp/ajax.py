from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from wireguardapp.models import Interface, Peer, PeerAllowedIP, PeerSnapshot, Key
from django.http import JsonResponse
import json

from .service.client import deleteClient,generateClientConf

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
    
    conf = generateClientConf(key)

    return JsonResponse({"success": False,'body': conf})


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
    if (key.user != user and not user.is_superuser):
        return JsonResponse({"success": False, "body" : "Musíte být vlastníkem klíče nebo superuser"})
    
    result = deleteClient(user,key)
    if result:
        return JsonResponse({"success": False, "body" : "Server v tuto chvíli není online."})
    
    return JsonResponse({"success": True, "body" : "Klíč byl odstraněn"})

