import subprocess
from wireguardapp.models import Interface, Peer, PeerAllowedIP, PeerSnapshot, Key
import logging

logger = logging.getLogger('wg')

ENDPOINT = "127.0.0.1:51820"

KEY_DIR_PATH = "/var/www/bakproject/savedkeys"

def generateClientConfText(clientInterface : Interface, serverPeer : Peer):
    conf = f"""
[Interface]
PrivateKey = {clientInterface.interface_key.private_key}
Address = {clientInterface.ip_address}

[Peer]
PublicKey = {serverPeer.peer_key.public_key}
Endpoint = {ENDPOINT}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = {serverPeer.persistent_keepalive}
""".strip()
    
    return conf
    

def generateClientConf(key : Key):
    clientInterface = Interface.objects.get(interface_key = key)
    serverPeer = Peer.objects.get(interface = clientInterface)

    if (clientInterface.interface_type == Interface.SERVER):
        return "Pro server nemůže být vrácená konfigurace."

    return generateClientConfText(clientInterface, serverPeer)

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
            "/var/www/bakproject/scripts/enablepeer.sh", 
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

    logger.info("WireGuard peer added successfully")
    logger.debug("STDOUT: %s", result.stdout)
    return True


def reconfigureServerConf():
    
    pass

def genAndSaveClientConf(clientInterface : Interface, serverPeer : Peer):
    conf = generateClientConfText(clientInterface, serverPeer)
    name = 'wg-' + clientInterface.name + ".conf"
    with open('/var/www/bakproject/tempconf/' + name, 'w') as file:
        file.write(conf)

    return 
    