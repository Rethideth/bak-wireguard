# Overview
A web interface for Wireguard.  
Uses django users to create users for creating users keys.
Creates a one server interface and allows to create clients keys and their configuration for connection.
Also shows active connection state and their sent/recieved bytes.

Uses Apache2 server to host the website. The site is created by django and connected to the server using mod_wsgi.

Uses scripts owned by root and permitted sudo for www-data to execute wireguard commands.

Private key are encrypted by Fernet symmetric encryption cryptography.fernet.Fernet. The fernet key is stored in a enviroment file .env, and read when a private key need to be decrypted. 

Logic of the website is in wireguardapp/services.

On windows, add DNS=1.1.1.1 to the client interface config, if not working.

## Sources
 - https://studygyaan.com/django/how-to-setup-django-applications-with-apache-and-mod-wsgi-on-ubuntu
 - https://docs.djangoproject.com/en/6.0/topics/auth/default/
 - https://docs.djangoproject.com/en/6.0/topics/class-based-views/mixins/
 - https://documentation.ubuntu.com/server/how-to/wireguard-vpn/vpn-as-the-default-gateway/#using-the-vpn-as-the-default-gateway
 - https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
 - https://www.w3schools.com/django/


