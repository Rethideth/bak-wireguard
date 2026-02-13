from cryptography.fernet import Fernet
from django.conf import settings

fernet = Fernet(settings.FERNET_KEY.encode())

def encrypt_value(value: str) -> str:
    """
    Encrypts a string value based on a fernet key.
    Fernet key in in a enviroment privileged file.
    
    :param value: String value for encryption.
    :type value: str


    :return: Encrypted value based on a fernet key.
    :rtype: str
    """
    return fernet.encrypt(value.encode()).decode()

def decrypt_value(value: str) -> str:
    """
    Decrypts a string value based on a fernet key.
    Fernet key in in a enviroment privileged file.
    
    :param value: Encrypted string value.
    :type value: str

    
    :return: Decrypted string value based on a fernet key.
    :rtype: str
    """
    return fernet.decrypt(value.encode()).decode()