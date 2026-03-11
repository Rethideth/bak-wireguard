from .models import Interface
from .services.server import getServerInterfaces

def servers(request):

    return {
        "servers": getServerInterfaces()
    }