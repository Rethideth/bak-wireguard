from .models import Interface
from .services.serverservice import ServerService
from django.db import connections
from django.db.utils import OperationalError

def servers(request):
    """ Returns all instances of servers interfaces and if a database is online. """
    db_online = True
    try:
        connections['default'].cursor()
    except OperationalError:
        return {
        "servers": servers,
        "db_online":False
    }
    try:
        servers = ServerService.getAllServerInterfaces()
    except:
        servers = ["databázeni není online"]
    return {
        "servers": servers,
        "db_online":db_online
    }