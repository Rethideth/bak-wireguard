from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(
        to=User,
        on_delete=models.CASCADE
    )
    verified = models.BooleanField(default=False)
    key_limit = models.PositiveIntegerField(default=5)
    key_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user}"

class Key(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
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
    private_key = models.TextField()

    def __str__(self):
        return f"{self.user}:{self.name}"
    


class Interface(models.Model):
    SERVER = 'server'
    CLIENT = 'client'
    TYPE_CONNECTION = [(SERVER, 'Server'), (CLIENT, 'Client')]
    
    name = models.CharField(
        max_length=100,
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
    ip_network = models.CharField(
        max_length=32,
        null=True
    )
    ip_network_mask = models.PositiveIntegerField(
        null=False,
    )
    
    ip_address = models.CharField(
        max_length=32,
        null=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    interface_type = models.CharField(
        max_length=32,
        choices=TYPE_CONNECTION,
    )
    server_endpoint = models.CharField(
        max_length=32,
        null=True
    )
    session_number = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.name}-{self.interface_key.name}"


class Peer(models.Model):
    interface = models.ForeignKey(
        Interface,
        on_delete=models.CASCADE,
        related_name="owned_interface",
        verbose_name="Interface included with this peer"
    )
    peer_interface = models.ForeignKey(
        Interface,
        on_delete=models.CASCADE,
        related_name="peer",
        verbose_name="Connected to"
        
    )
    persistent_keepalive = models.PositiveIntegerField(
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    total_rx_bytes = models.BigIntegerField(default=0)
    total_tx_bytes = models.BigIntegerField(default=0)
    last_rx_bytes = models.BigIntegerField(default=0)
    last_tx_bytes = models.BigIntegerField(default=0)

    def __str__(self):
        return f"{self.interface.name} → {self.peer_interface.interface_key}"


class PeerSnapshot(models.Model):
    peer = models.ForeignKey(
        Peer,
        on_delete=models.CASCADE,
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
    session = models.PositiveIntegerField(
        null=True, blank=False)

    def __str__(self):
        return f"{self.peer} @ {self.collected_at}"



