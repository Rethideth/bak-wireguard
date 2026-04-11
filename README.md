# Unnamed WireGuard web interface

## Description
A web interface for VPN server using WireGuard.  
Allows the administrator to create WireGuard server interface and manage the server interface.
Allow to create/register and manage users that can create their own keys for WireGuard interfaces.
Also shows active connection state and their total and current sent/recieved bytes.

## Features
Uses Apache2 server to host the website. The site is deployed by django and connected to apache2 using mod_wsgi.

MariaDB for database service.

Uses scripts owned by root and permitted sudo for www-data to execute wireguard commands.

Private key are encrypted by Fernet symmetric encryption cryptography.fernet.Fernet. The fernet key is stored in a enviroment file .env, and read when a private key need to be decrypted. 

Provides password reset by email for accounts.

Web interface actions are logged in `/var/log/wgweb/wg.log`. These include:
- Creating or deleting a server interface
- Creating or removing a client key
- Turning On/Off the server interface
- Altering server interface information
- WireGuard peer state saving
- Disconnecting or connecting of WireGuard peers to the server interface

## Project Structure
Uses one django app `wireguardapp` for everything. Every function added by this work is documented by docstrings.

The structure of the directory of the wireguard app is:
### Database
Database access layer for the MariaDB database. 
- repository.py - Static classes and methods for CRUD operations. Every model has a repository and special repositories for client and server operation.

### Management
Has commands that are accessible from outside of the django project using virtual enviroment. 
 - commands
  - my_command.py - Dev testing managment command
  - wgdump.py - Managment command for saving and aggregating current state of WireGuard server interfaces. Used for cron job.

### Static
Has images for web interface.

### Templates
Has html files for web interface. 

### Service
Business layer for the view functions.
 - clientservice.py - Has a one static class with methods intended mainly for client usage.
 - serverservice.py - Has a one static class with methods intended mainly for server usage.
 - modelfactory.py - Has a one static class with methods for correctly creating instances of models.
 - wireguardcmd.py - Has functions which uses functions related to WireGuard configuration and commands, such as `wg show all dump`.
 - crypto.py - Has two functions for encryption and decryption of private keys. 

### Base
 - ajax.py - All json web requests from ajax requests.
 - contextprocessors.py - Has a single function that returns all server interfaces. Is used for getting a list of servers for dropdown of "Server Dashboardy".
 - forms.py - All forms that django app uses.
 - middleware.py - Has middleware for django project. Has a one function that check if database is up and redirects if it is down.
 - models.py - Has models of django app.
 - tests.py - Dev testing functions.
 - urls.py - List of urls that are mapped to views or ajax functions.
 - views.py - All http web requests.

## Sources
 - https://studygyaan.com/django/how-to-setup-django-applications-with-apache-and-mod-wsgi-on-ubuntu
 - https://docs.djangoproject.com/en/6.0/topics/auth/default/
 - https://docs.djangoproject.com/en/6.0/topics/class-based-views/mixins/
 - https://documentation.ubuntu.com/server/how-to/wireguard-vpn/vpn-as-the-default-gateway/#using-the-vpn-as-the-default-gateway
 - https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
 - https://www.w3schools.com/django/
 - https://www.scaleway.com/en/docs/tutorials/install-wireguard/
 - https://sendlayer.com/blog/how-to-implement-password-reset-in-django/

