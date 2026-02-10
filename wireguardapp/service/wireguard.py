import subprocess
from wireguardapp.models import Interface, Peer, PeerAllowedIP, PeerSnapshot, Key
import logging
from django.conf import settings

logger = logging.getLogger('wg')


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



    