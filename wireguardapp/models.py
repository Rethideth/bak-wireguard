from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Key(models.Model):
    TYPE_KEY = [('server', 'Server'), ('client', 'Client')]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=255,
        null=True
    )
<<<<<<< HEAD
=======
    key_type = models.CharField(
        max_length=64,
        choices=TYPE_KEY,
    )
>>>>>>> refs/remotes/origin/main
    public_key = models.CharField(
        max_length=44,
        null=False,
        unique=True
    )
    private_key = models.CharField(
        max_length=44,
        null=True
    )
    def __str__(self):
        return f"{self.user}:{self.public_key[:8]}"
    


class Interface(models.Model):
    SERVER = 'server'
    CLIENT = 'client'
    TYPE_CONNECTION = [(SERVER, 'Server'), (CLIENT, 'Client')]
    
    name = models.CharField(
        max_length=32,
        unique=True,
        db_index=True
    )
    interface_key = models.ForeignKey(
        Key,
        on_delete=models.CASCADE,
    )
    listen_port = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    fwmark = models.CharField(
        max_length=16,
        null=True,
        blank=True
    )
    ip_address = models.CharField(
        max_length=32,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    interface_type = models.CharField(
        max_length=32,
        choices=TYPE_CONNECTION,
        null=True
    )

    def __str__(self):
        return self.name


class Peer(models.Model):
    interface = models.ForeignKey(
        Interface,
        on_delete=models.CASCADE,
        related_name="peers",
        verbose_name="Interface included with this peer"
    )
    peer_key = models.ForeignKey(
        Key,
        on_delete=models.CASCADE,
        related_name='peerkey',
        verbose_name="Connected to"
    )
    persistent_keepalive = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )


    def __str__(self):
        return f"{self.interface.name} → {self.peer_key}"


class PeerAllowedIP(models.Model):
    peer = models.ForeignKey(
        Peer,
        on_delete=models.CASCADE,
        related_name="allowed_ips"
    )
    cidr = models.CharField(
        max_length=64
    )


    def __str__(self):
        return f"{self.peer} → {self.cidr}"


class PeerSnapshot(models.Model):
    peer = models.ForeignKey(
        Peer,
        on_delete=models.CASCADE,
        related_name="snapshots"
    )
    endpoint = models.CharField(
        max_length=64,
        null=True,
        blank=True
    )
    latest_handshake = models.DateTimeField(
        null=True,
        blank=True
    )
    rx_bytes = models.BigIntegerField()
    tx_bytes = models.BigIntegerField()
    collected_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )


    def __str__(self):
        return f"{self.peer} @ {self.collected_at}"




class PeerEvent(models.Model):
    EVENT_TYPES = [
        ("handshake", "Handshake"),
        ("handshake_failed", "Handshake Failed"),
        ("interface_up", "Interface Up"),
        ("interface_down", "Interface Down"),
        ("unknown", "Unknown"),
    ]

    peer = models.ForeignKey(
        Peer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="events"
    )
    interface = models.ForeignKey(
        Interface,
        on_delete=models.CASCADE,
        related_name="events"
    )
    event_type = models.CharField(
        max_length=32,
        choices=EVENT_TYPES
    )
    message = models.TextField()
    event_time = models.DateTimeField(
        db_index=True
    )

    def __str__(self):
        return f"{self.event_type} @ {self.event_time}"
    
