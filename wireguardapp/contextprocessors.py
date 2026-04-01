from .models import Interface
from .services.serverservice import ServerService

def servers(request):
    try:
        servers = ServerService.getAllServerInterfaces()
    except:
        servers = {"servers" : ["databázeni není online"]}
    return {
        "servers": servers
    }