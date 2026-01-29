from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Key(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    name = models.CharField(
        max_length=255,
        null=True
    )
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
    name = models.CharField(
        max_length=32,
        unique=True,
        db_index=True
    )
    public_key = models.ForeignKey(
        Key,
        on_delete=models.CASCADE,
        related_name='interfacekey'
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

    def __str__(self):
        return self.name


class Peer(models.Model):
    TYPE_CONNECTION = [('server', 'Server'), ('client', 'Client')]

    interface = models.ForeignKey(
        Interface,
        on_delete=models.CASCADE,
        related_name="peers"
    )
    public_key = models.ForeignKey(
        Key,
        on_delete=models.CASCADE,
        related_name='peerkey',
        verbose_name='interface connected to',
    )
    persistent_keepalive = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    peer_type = models.CharField(
        max_length=32,
        choices=TYPE_CONNECTION,
    )

    class Meta:
        unique_together = ("interface", "public_key")
        indexes = [
            models.Index(fields=["interface", "public_key"]),
        ]

    def __str__(self):
        return f"{self.interface.name} → {self.public_key}"


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
    
