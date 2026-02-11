from wireguardapp.models import Interface, Peer, PeerAllowedIP, PeerSnapshot, Key
from django.contrib.auth.models import User

def getServerInterface():
    """
    Returns the server interface.
    """
    return Interface.objects.get(interface_type = Interface.SERVER)
