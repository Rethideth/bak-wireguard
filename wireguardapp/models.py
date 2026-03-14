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
        verbose_name="Jméno klíče",
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
        verbose_name="Systémové jméno serveru",
        max_length=100,
        unique=True,
        db_index=True
    )
    interface_key = models.ForeignKey(
        Key,
        verbose_name="Klíč rozhraní",
        on_delete=models.CASCADE,
    )
    listen_port = models.PositiveIntegerField(
        verbose_name="Port endpoitu k naslouchání",
        null=True,
        blank=True
    )
    ip_network = models.CharField(
        verbose_name="Adresa sítě rozhraní",
        max_length=32,
        null=True
    )
    ip_network_mask = models.PositiveIntegerField(
        verbose_name="Maska sítě",
        null=False,
    )
    
    ip_address = models.CharField(
        verbose_name="Přidělena ip adresa rozraní",
        max_length=32,
        null=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    interface_type = models.CharField(
        verbose_name="Typ rozhraní",
        max_length=32,
        choices=TYPE_CONNECTION,
    )
    server_endpoint = models.CharField(
        verbose_name="Dosažitelná adresa rozhraní serveru (Endpoint)",
        max_length=32,
        null=True
    )
    session_number = models.PositiveIntegerField(default=1)

    current_internet_interface = models.CharField(
        verbose_name="Aktuální rozhraní pro přesměrování do internetu",
        max_length=64)
    
    client_to_client = models.BooleanField(
        verbose_name="Povolit klientům se připojit mezi sebou?",
        default=False
    )

    def __str__(self):
        conn = 'Ne'
        if self.client_to_client:
            conn ='Ano'
        return f"{self.interface_key.name} (client-to-client:{conn})"


class Peer(models.Model):
    interface = models.ForeignKey(
        Interface,
        on_delete=models.CASCADE,
        related_name="owned_interface",
        verbose_name="Rozhraní spojené s tímto peer"
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



