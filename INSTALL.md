# Installation
on ubuntu.

## 1. Install dependencies.
```
sudo apt install python3-pip
sudo apt install python3-venv
sudo apt-get install python3-pip apache2 libapache2-mod-wsgi-py3
sudo apt-get install libmariadb-devUpdate
sudo apt-get install pkg-config python3-dev default-libmysqlclient-dev build-essential
sudo apt install mariadb-server
sudo apt install git
sudo apt install wireguard
```
Go to a directory where do you want to install the project (here it is in `/var/www/wireguardweb`)


## 2. Clone and install the project into a directory where do you want it.
Here the project directory is `/var/www/wireguardweb`. It can somewhere else, but it must be reachable by apache system user `www-data` and all folder must have permissions for it.

```
mkdir /var/www/wireguardweb
sudo chmod 775 /var/www/wireguardweb
sudo chown $USER:www-data /var/www/wireguardweb
```
Inside of your directory clone the repo straight in the directory.
Do not forget the dot at the end of the git clone command.
```
cd /var/www/wireguardweb
git clone https://github.com/Rethideth/bak-wireguard .
```
If not working, try:
`export GNUTLS_CPUID_OVERRIDE=0x1`

### 2.1 Virtual env
Create a virtual python enviroment in the project directory:
```
python3 -m venv /var/www/wireguardweb/venv
```
Activate the virtual enviroment using `source venv/bin/activate`.

Deactivate using `deactivate`.

### 2.2 requirements
Requirement for project. Execute the commands below inside virtual enviroment.
```
pip install django
pip install mysqlclient
pip install cryptography
pip install python-dotenv
pip install psutil
```
### 2.3 encryption and enviroment values
Encryption for private key.
Create an enviromental file for the project
```
touch .env
sudo chmod 660 .env
sudo chown :www-data .env
```
Run this command and copy its output:
```python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"```
Then write the generated key into the `.env` file. 
`FERNET_KEY=<the generated key>` 

Generate a secret key for django.
```python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"```
Write output into `.env` file
`SECRET_KEY=<the generated key>`

Also add a row to store a password for MariaDB django user. Use this password in MariaDB user creation. 
`DJANGO_PASSWORD=<plain-text-password>` 

### 2.4 Logging 
You must have correct permission or manage.py runserver wont work correctly. 
The user who will run the `python manage.py runserver` will throw error if it doesnt have read and write on the log files.
```
sudo mkdir /var/log/wgweb
sudo chown www-data:$USER /var/log/wgweb
sudo touch /var/log/wgweb/wg.log /var/log/wgweb/web.log
sudo chown www-data:$USER /var/log/wgweb/wg.log /var/log/wgweb/web.log
sudo chmod 660 /var/log/wgweb/wg.log /var/log/wgweb/web.log
```
### 2.5 visudo script permission
Enable the www-data user to execute wireguard commands that need sudo.
```
sudo visudo /etc/sudoers.d/wireguard
```
Write this into the visudo to enable executing these scripts with wireguard commands.
Scripts files are in `/path/to/project/scripts/`, here it is `/var/www/wireguardweb/scripts/`.
```
www-data ALL=(root) NOPASSWD: \
	/var/www/wireguardweb/scripts/wg-peer-add.bash, \
	/var/www/wireguardweb/scripts/wg-peer-remove.bash, \
	/var/www/wireguardweb/scripts/wg-start.bash, \
	/var/www/wireguardweb/scripts/wg-stop.bash, \
	/var/www/wireguardweb/scripts/wg-check.bash, \
	/var/www/wireguardweb/scripts/wg-inf-dump.bash
```
Give the scripts execution privilege and change ownership to root.
```
sudo chown root:root wg-peer-add.bash wg-peer-remove.bash wg-start.bash wg-stop.bash wg-check.bash wg-inf-dump.bash 
sudo chmod 744 wg-peer-add.bash wg-peer-remove.bash wg-start.bash wg-stop.bash wg-check.bash wg-inf-dump.bash
```
### 2.6 mysql
In mariadb database, create an user and a database for django server. Use the same password in enviroment file (here it is `django`).
Enter the database:
`sudo mysql`
Execute these commands:
```
CREATE DATABASE IF NOT EXISTS wg_web;
CREATE USER IF NOT EXISTS 'django'@'localhost' IDENTIFIED BY 'django';
GRANT ALL PRIVILEGES ON wg_web.* TO 'django'@'localhost';
FLUSH PRIVILEGES;
```


### 2.7 finish django
Add static directory into the project directory
```
mkdir /var/www/wireguardweb/static
```
Change group to www-data for all project files
```
sudo chown  $USER:www-data /var/www/wireguardweb/* -R
```

Run these commands 
```
python manage.py makemigrations
python manage.py migrate


python manage.py collectstatic
python manage.py createsuperuser
python manage.py runserver
```
If runserver is ok, everything on the side of django is completed.


## 3. Apache 
Create a configuration file
```
sudo nano /etc/apache2/sites-available/wgweb.conf
```
Write into the config file the code under. You may need to change the project directory (`/var/www/wireguardweb`), ServerName and other if you need.
```
<VirtualHost *:443>
        SSLEngine on
        SSLCertificateFile /etc/apache2/ssl/apache.crt
        SSLCertificateKeyFile /etc/apache2/ssl/apache.key

        ServerAdmin admin@wgweb.localhost
        # ServerName wgweb.localhost
        # ServerAlias www.wgweb.localhost
        DocumentRoot /var/www/wireguardweb

        # Error logging
        ErrorLog ${APACHE_LOG_DIR}/error.log
        CustomLog ${APACHE_LOG_DIR}/access.log combined

        Alias /static /var/www/wireguardweb/static
        <Directory /var/www/wireguardweb/static>
                Require all granted
        </Directory>

        Alias /media /var/www/wireguardweb/media
        <Directory /var/www/wireguardweb/media>
                Require all granted
        </Directory>

        <Directory /var/www/wireguardweb/wg_web>
                <Files wsgi.py>
                        Require all granted
                </Files>
        </Directory>

        # Python wsgi config
        WSGIDaemonProcess wg_web python-path=/var/www/wireguardweb python-home=/var/www/wireguardweb/venv
        WSGIProcessGroup wg_web
        WSGIScriptAlias / /var/www/wireguardweb/wg_web/wsgi.py
        WSGIApplicationGroup %{GLOBAL}

</VirtualHost>

<VirtualHost *:80>
        ServerAdmin admin@wgweb.localhost
        ServerName wgweb.localhost
        ServerAlias www.wgweb.localhost
        DocumentRoot /var/www/wireguardweb

        # Error logging
        ErrorLog ${APACHE_LOG_DIR}/error.log
        CustomLog ${APACHE_LOG_DIR}/access.log combined

        # Redirect HTTP to HTTPS
        Redirect / https://wgweb       


        Alias /static /var/www/wireguardweb/static
        <Directory /var/www/wireguardweb/static>
                Require all granted
        </Directory>

        Alias /media /var/www/wireguardweb/media
        <Directory /var/www/wireguardweb/media>
                Require all granted
        </Directory>

        <Directory /var/www/wireguardweb/wg_web>
                <Files wsgi.py>
                        Require all granted
                </Files>
        </Directory>

</VirtualHost>
```
### apache config
Configure self signed certificate and enable the site.
```
sudo a2enmod ssl
sudo mkdir -p /etc/apache2/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/apache2/ssl/apache.key -out /etc/apache2/ssl/apache.crt
```
Enable the site.
```
sudo a2dissite 000-default.conf
sudo a2dissite default-ssl.conf
sudo a2ensite wgweb.conf
sudo a2enmod wsgi
```
Check if apache config has any errors
```
apachectl configtest
```

Restart apache
`sudo systemctl restart apache2`

## 4. Errors
Apache errors are in `/var/log/apache2/error.log`

## 5. Network
Ports and firewall.
In project directory in `wg_web/settings.py`, to the list `ALLOWED_HOSTS`, add an ip address or a domain that this server will run on. 

Allow ports in your firewall (`ufw` in this case) for wireguard. Only allow those ports, that you be using.
Before you enable your firewall, enable your ports first, especially `ssh` port if you are configuring a remote server.
```
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
```
Allow ports that will be using wireguard. Usually it is `51820`, but you can allow more ports for more wireguard interfaces
```
sudo ufw allow 51820
```
Enable firewall
```
sudo ufw enable
```
## 6. Automatic logging
Enable a cron job for executing django managment command for logging peer data.
Edit cron jobs for the user `www-data`
```
sudo crontab -u www-data -e
```
Add a row:
```
0 * * * * cd /var/www/wireguardweb && /var/www/wireguardweb/venv/bin/python manage.py wgdump >> /var/log/wgweb/wg.log 2>&1
```
