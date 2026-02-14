import subprocess
from wireguardapp.models import Interface, Peer,  PeerSnapshot, Key
from .crypto import decrypt_value
import subprocess
import tempfile
from django.conf import settings
import logging
import time
import datetime

logger = logging.getLogger('wg')

INTERNET_INTERFACE = 'wlo1'


def generateClientConfText(
        clientInterface : Interface,
        serverPeer : Peer,
        endpoint:str, 
        listenPort:str,
        allowedIPs:str ='0.0.0.0/0'):
    """
    Creates the text for a clients configuration file based on the given parameters.
    
    :param clientInterface: The interface the configuration file is created for.
    :type clientInterface: Interface
    :param serverPeer: The peer with the client interface which connects to the server.
    :type serverPeer: Peer
    :param endpoint: The public address of the VPN server.
    :type endpoint: str
    :param listenPort: The port of the VPN server.
    :type listenPort: str
    :param allowedIPs: Network of addresses which will be forwarded to the VPN server.
    :type allowedIPs: str

    :return: Text of the configuration file for the client.
    :rtype: str

    Configuration Structure
    --------------
    The configuration text string will be in this format:

    .. code-block:: python

        [Interface]
        PrivateKey =                # Client decoded private key
        Address =                   # Client ip address with bit mask

        [Peer]
        PublicKey =                 # Server public key
        Endpoint =                  # Reachable address and port that can access the wireguard server interface. 
        AllowedIPs =                # Which ip addresses given by a network (e.g. 10.10.0.0/24) will be forwarded to this interface
        PersistentKeepalive =       # Time in seconds to periodicaly check if the connection is active.

    """
    if clientInterface.interface_type != Interface.CLIENT:
        raise TypeError
    
    conf = f"""
[Interface]
PrivateKey = {decrypt_value(clientInterface.interface_key.private_key)}
Address = {clientInterface.ip_address}

[Peer]
PublicKey = {serverPeer.peer_key.public_key}
Endpoint = {endpoint}:{listenPort}
AllowedIPs = {allowedIPs}
PersistentKeepalive = {serverPeer.persistent_keepalive}
""".strip()
    
    return conf
    

def generateServerConfText(serverInterface : Interface):
    """
    Creates the text for the server configuration file based on the interface given.
    Raises an exception if it is not given a server interface.
    
    :param serverInterface: The server interface to create the configuration file.
    :type serverInterface: 
    
    :return: Text of the configuration file for the server.
    :rtype: str

    :raises TypeError: If the parameter serverInterface does not have interface_type = Interface.SERVER.

    Configuration Structure
    --------------
    The configuration text string will be in this format:

    .. code-block:: python
        [Interface]
        PrivateKey =                # Decoded server private key.
        ListenPort =                # Server listening port (51820)
        Address =                   # Server ip interface. Has its own ip address and bit mask
        SaveConfig = true           # On Interface down, saves the state of the wireguard peers from `wg set` and writes it into the config
        PostUp =                                                                        # add network rules on interface starting
            sysctl -w net.ipv4.ip_forward=1;                                            # enable port forwarding
            iptables -t nat -A POSTROUTING -o <internet_interface> -j MASQUERADE;       # rewrites the incoming traffic origin address to the interface 
            iptables -A FORWARD -i <wireguard_interface> -j ACCEPT;                                 # enables forwarding of packets from and into wg-server
            iptables -A FORWARD -o wg-server -j ACCEPT; 
    PostDown =                                                                          # removes network rules in interface stopping
            sysctl -w net.ipv4.ip_forward=0; 
            iptables -t nat -D POSTROUTING -o {INTERNET_INTERFACE} -j MASQUERADE; 
            iptables -D FORWARD -i wg-server -j ACCEPT; 
            iptables -D FORWARD -o wg-server -j ACCEPT; 

        [Peer]
        PublicKey =                 # clients public key  
        AllowedIPs =                # clients ip addres with bit mask

    """

    if serverInterface.interface_type != Interface.SERVER:
        raise TypeError
    serverPeers = Peer.objects.filter(peer_key = serverInterface.interface_key)

    conf = f"""
[Interface]
PrivateKey = {decrypt_value(serverInterface.interface_key.private_key)}
ListenPort = {serverInterface.listen_port}
Address = {serverInterface.ip_address}
SaveConfig = true
PostUp = sysctl -w net.ipv4.ip_forward=1
PostUp = iptables -t nat -A POSTROUTING -o {INTERNET_INTERFACE} -j MASQUERADE
PostUp = iptables -A FORWARD -i {serverInterface.name} -j ACCEPT
PostUp = iptables -A FORWARD -o {serverInterface.name} -j ACCEPT
PostDown = sysctl -w net.ipv4.ip_forward=0; \\
PostDown = iptables -t nat -D POSTROUTING -o {INTERNET_INTERFACE} -j MASQUERADE; \\
PostDown = iptables -D FORWARD -i {serverInterface.name} -j ACCEPT; \\
PostDown = iptables -D FORWARD -o {serverInterface.name} -j ACCEPT \\
""".strip()
    
    for peer in serverPeers:
        conf = conf + '\n\n'
        conf = conf + f"""
[Peer]
PublicKey = {peer.interface.interface_key.public_key}
AllowedIPs = {peer.interface.ip_address}
""".strip()

    return conf, serverInterface.name


#private key, public_key
def generateKeyPair():
    """
    Generates unencrypted private key and its own public key.
    Keys generated using wg commands 'wg genkey' and 'wg pubkey <private_key>' 

    :return: Tuple of strings of unecrypted private key and public key
    :rtype: Tuple[str,str]
    """
    private_key = subprocess.run(['wg', 'genkey'], 
            capture_output=True,
            text=True,
            check=True,
    ).stdout

    public_key = subprocess.run(
        ['wg', 'pubkey'],
        input=private_key,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return private_key.strip(),public_key.strip()


def addWGPeer(serverInterfaceName : str,peerKey : str, ipAddress : str):
    """
    Executes a privileged bash script wg-peer-add.sh to temporarily add a peer to the server to connect a client.
    On stopping the server interface, the pper should be saved into config due to 'SaveConfig = True'.
    Result is logged into logs/wg.log.
    To execute the script properly, the script must be owned
    by root and www-data have sudo privileges on the script from visudo.
    If failed, try to look 'visudo /etc/sudoers.d/wireguard'
    
    :param serverInterfaceName: The name of the server interface to add the peer.
    :type serverInterfaceName: str
    :param peerKey: The clients public key.
    :type peerKey: str
    :param ipAddress: The ip address with its bit mask of the client (e.g. 10.10.0.15/32). 
        For wireguard it is the ip address which will Wireguard forwards the clients network traffic.
    :type ipAddress: str

    :raises RuntimeError: Raises an exception if executing the scripts fails.
    """
    cmd = [
            "sudo",
            settings.BASE_DIR / "scripts/wg-peer-add.sh", 
            serverInterfaceName, 
            peerKey,
            ipAddress
        ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error(f"({datetime.datetime.now()}): wg set command failed")
        logger.error("STDOUT: %s", result.stdout)
        logger.error("STDERR: %s", result.stderr)
        raise RuntimeError(result.stderr.strip())

    logger.info(f"({datetime.datetime.now()}): WireGuard peer {peerKey} added successfully")
    logger.debug("STDOUT: %s", result.stdout)
    return 

def removeWGPeer(serverInterfaceName :str, peerKey : str):
    """
    Executes a privileged bash script wg-peer-remove.sh to temporarily remove a peer to the server to disconnect a client.
    On stopping the server interface, the peer should be removed from config due to 'SaveConfig = True'.
    Result is logged into logs/wg.log.
    To execute the script properly, the script must be owned
    by root and www-data have sudo privileges on the script from visudo.
    If failed, try to look 'visudo /etc/sudoers.d/wireguard'
    
    :param serverInterfaceName: The name of the server interface to which peer to remove.
    :type serverInterfaceName: str
    :param peerKey: The clients public key.
    :type peerKey: str

    :raises RuntimeError: Raises an exception if executing the scripts fails.
    """

    cmd = [
            "sudo",
            settings.BASE_DIR / "scripts/wg-peer-remove.sh", 
            serverInterfaceName, 
            peerKey,
        ]
    logger.debug("ARGS: %s,%s,%s", serverInterfaceName,peerKey)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error(f"({datetime.datetime.now()}): wg set command failed")
        logger.error("STDOUT: %s", result.stdout)
        logger.error("STDERR: %s", result.stderr)
        raise RuntimeError(result.stderr.strip())

    logger.info(f"({datetime.datetime.now()}): WireGuard peer {peerKey} removed successfully")
    logger.debug("STDOUT: %s", result.stdout)
    return True



def startWGserver(serverInterface : Interface):
    """
    Starts the server interface using a privileged bash script wg-start.sh.
    The interface will have a generated config file based on the server interface and its own peers.
    This function will create a temporary file, then the script will install the config file into /etc/wireguard.
    In the end the script will try to start the server interface using 'wg-quick'.
    result is logged into logs/wg.log

    :param serverInterface: The server interface to start.
    :type serverInterface: Interface
    
    :raises CalledProcessError: If the script fail to execute fully
    :raises TypeError: If the provided `serverInterface` does not have a server type.
    """
    conf, servername = generateServerConfText(serverInterface=serverInterface)

    with tempfile.NamedTemporaryFile(
        mode='w',
        delete=False, 
        prefix='wg-',
        suffix='.conf') as temp:
        temp.write(conf)
        tmpPath = temp.name


    cmd = [
        "sudo",
        settings.BASE_DIR / "scripts/wg-start.sh", 
        tmpPath,
        servername
    ]

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"({datetime.datetime.now()}): wg-start.sh script has failed.")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return 
    
    logger.info(f"({datetime.datetime.now()}): Wireguard server has been started.")

    return 

def stopWGserver(serverInterface : Interface):
    """
    Stops the server interface using a privileged bash script wg-stop.sh.
    The script will try to stop the server interface using wg-quick.
    Result is logged into logs/wg.log

    :param serverInterface: The server interface to stop.
    :type serverInterface: Interface
    
    :raises CalledProcessError: If the script fail to execute fully
    """

    cmd = [
        "sudo",
        settings.BASE_DIR / "scripts/wg-stop.sh", 
        serverInterface.name
    ]

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"({datetime.datetime.now()}): wg-stop.sh script has failed.")
        logger.error(f"STDOUT: {e.stdout}")
        logger.error(f"STDERR: {e.stderr}")
        return 
    
    logger.info(f"({datetime.datetime.now()}): Wireguard server has been stopped.")

    return 


def isWGserverUp(serverInterface : Interface) -> bool:
    """
    Check if the Wireguard server interface is currently running.
    Check by using 'wg show <interface_name>' command if it is running.
    If the command executes succesfully, it returns True.
    If the commnad fails to execute, it returns False

    :param serverInterface: The server interface to check if it is running.
    :type serverInterface: Interface

    :return: Return True if interface is running, False if it is stopped. 
    :rtype: bool
    """

    try:
        result = subprocess.run(
            ["wg", "show", serverInterface.name],
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False
    

def getWGPeersState(serverInterface :Interface):
    """
    Retrieve the current WireGuard peer state.

    Uses the command ``wg show <interface_name> dump`` to read the
    current state of all peers attached to the server interface.

    A peer is considered connected if:

    - ``latest_handshake > 0``
    - The last handshake occurred within the past 120 seconds.

    :param serverInterface: The server interface to get its own peers.
    :type serverInterface: Interface

    :return: A list of dictionaries, one per peer, with the structure or a empty list
        of command execution fails.
    :rtype: list[dict]

    List structure
    ------------------
    The list of values will be in this form:
    .. code-block:: python

        [
            {
                "peer": str,          # Peer string representation
                "endpoint": str,      # Peer endpoint (ip:port) or "—"
                "handshake": int,     # Unix timestamp (seconds)
                "rx": int,            # Received bytes
                "tx": int,            # Transmitted bytes
                "is_connected": bool  # True if handshake < 120 seconds ago
            },
        ]
    """
    now = int(time.time())

    try:
        result = subprocess.run(
            ["wg", "show", serverInterface.name, "dump"],
            capture_output=True,
            text=True,
            check=True
        )

        lines = result.stdout.strip().split("\n")

        peers = []

        # First line is interface info → skip it
        for line in lines[1:]:
            parts = line.split("\t")

            public_key = parts[0]
            endpoint = parts[2]
            latest_handshake = int(parts[4])
            transfer_rx = int(parts[5])
            transfer_tx = int(parts[6])
            is_connected = (
                latest_handshake > 0 and
                (now - latest_handshake) < 120
            )
            peer = Peer.objects.get(peer_key__public_key = public_key)

            peers.append({
                "peer": peer.__str__(),
                "endpoint": endpoint or "—",
                "handshake": latest_handshake,
                "rx": transfer_rx,
                "tx": transfer_tx,
                'is_connected':is_connected
            })

        return peers

    except Exception:
        return []