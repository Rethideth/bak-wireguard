from django.contrib import admin
from .models import Interface, Peer,  PeerSnapshot, PeerEvent,Key

# Register your models here.
admin.site.register(Key)
admin.site.register(Interface)
admin.site.register(Peer)
admin.site.register(PeerSnapshot)

