from django.contrib import admin
from .models import Interface, Peer,  PeerSnapshot,Key,Profile

# Register your models here.
admin.site.register(Key)
admin.site.register(Interface)
admin.site.register(Peer)
admin.site.register(PeerSnapshot)
#admin.site.register(Profile)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "verified",
        "key_limit",
        "key_count",
    )

    search_fields = ("user__username",)
