from .models import Interface
from .services.serverservice import ServerService

def servers(request):

    return {
        "servers": ServerService.getAllServerInterfaces()
    }