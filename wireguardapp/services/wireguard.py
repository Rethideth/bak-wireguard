import subprocess
from wireguardapp.models import Interface, Peer, PeerAllowedIP, PeerSnapshot, Key
from .selector import getServerInterface
import subprocess
import tempfile
from django.conf import settings
import logging


logger = logging.getLogger('wg')


def generateClientConfText(clientInterface : Interface, serverPeer : Peer,endpoint:str, listenPort:str):
    if clientInterface.interface_type != Interface.CLIENT:
        raise TypeError
    
    conf = f"""
[Interface]
PrivateKey = {clientInterface.interface_key.private_key}
Address = {clientInterface.ip_address}

[Peer]
PublicKey = {serverPeer.peer_key.public_key}
Endpoint = {endpoint}:{listenPort}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = {serverPeer.persistent_keepalive}
""".strip()
    
    return conf
    

def generateServerConfText(serverInterface : Interface):
    if serverInterface.interface_type != Interface.SERVER:
        raise TypeError
    serverPeers = Peer.objects.filter(peer_key = serverInterface.interface_key)

    conf = f"""
[Interface]
PrivateKey = {serverInterface.interface_key.private_key}
ListenPort = {serverInterface.listen_port}
Address = {serverInterface.ip_address}
SaveConfig = true
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
    cmd = [
            "sudo",
            settings.BASE_DIR / "scripts/wg-peer-add.sh", 
            serverInterfaceName, 
            peerKey,
            ipAddress
        ]
    logger.debug("ARGS: %s,%s,%s", serverInterfaceName,peerKey,ipAddress)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error("wg set command failed")
        logger.error("STDOUT: %s", result.stdout)
        logger.error("STDERR: %s", result.stderr)
        raise RuntimeError(result.stderr.strip())

    logger.info(f"WireGuard peer {peerKey} added successfully")
    logger.debug("STDOUT: %s", result.stdout)
    return True

def removeWGPeer(serverInterfaceName :str, peerKey : str):

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
        logger.error("wg set command failed")
        logger.error("STDOUT: %s", result.stdout)
        logger.error("STDERR: %s", result.stderr)
        raise RuntimeError(result.stderr.strip())

    logger.info(f"WireGuard peer {peerKey} removed successfully")
    logger.debug("STDOUT: %s", result.stdout)
    return True



def startWGserver():
    conf, servername = generateServerConfText(getServerInterface())

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
        print('error: %s',  e.stderr)
        return e.stderr

    return 

def stopWGserver():
    serverInterface = getServerInterface()

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
        print('error: %s', e.stderr)
        return e.stderr

    return 


def isWGserverUp():
    serverInterface = getServerInterface()
    try:
        result = subprocess.run(
            ["wg", "show", serverInterface.name],
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False