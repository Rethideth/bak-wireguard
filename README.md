## Apache config

```
<VirtualHost *:443>
	SSLEngine on
	SSLCertificateFile /etc/apache2/ssl/apache.crt
	SSLCertificateKeyFile /etc/apache2/ssl/apache.key

	ServerAdmin admin@wgweb.localhost
	ServerName wgweb.localhost
	# ServerName 192.168.0.161
	ServerAlias www.wgweb.localhost
	DocumentRoot /var/www/bakproject
	
	# Error logging
	ErrorLog ${APACHE_LOG_DIR}/error.log
	CustomLog ${APACHE_LOG_DIR}/access.log combined

	Alias /static /var/www/bakproject/static
	<Directory /var/www/bakproject/static>
		Require all granted
	</Directory>

	Alias /media /var/www/bakproject/media
	<Directory /var/www/bakproject/media>
		Require all granted
	</Directory>

	<Directory /var/www/bakproject/wg_web>
		<Files wsgi.py>
			Require all granted
		</Files>
	</Directory>

	# Python wsgi config
	WSGIDaemonProcess wg_web python-path=/var/www/bakproject python-home=/var/www/bakproject/venv
	WSGIProcessGroup wg_web
	WSGIScriptAlias / /var/www/bakproject/wg_web/wsgi.py
	WSGIApplicationGroup %{GLOBAL}
	
</VirtualHost>


<VirtualHost *:80>
	ServerAdmin admin@wgweb.localhost
	ServerName wgweb.localhost
	ServerAlias www.wgweb.localhost
	DocumentRoot /var/www/bakproject
	
	# Error logging
	ErrorLog ${APACHE_LOG_DIR}/error.log
	CustomLog ${APACHE_LOG_DIR}/access.log combined
	
	# Redirect HTTP to HTTPS
	RewriteEngine On
	RewriteCond %{HTTPS} off
	RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI}	

	Alias /static /var/www/bakproject/static
	<Directory /var/www/bakproject/static>
		Require all granted
	</Directory>

	Alias /media /var/www/bakproject/media
	<Directory /var/www/bakproject/media>
		Require all granted
	</Directory>

	<Directory /var/www/bakproject/wg_web>
		<Files wsgi.py>
			Require all granted
		</Files>
	</Directory>

</VirtualHost>
```

## Visudo config
Use `sudo visudo /etc/sudoers.d/wireguard` to write the following code

```
www-data ALL=(root) NOPASSWD: \
	/var/www/bakproject/scripts/wg-peer-add.sh, \
	/var/www/bakproject/scripts/wg-peer-remove.sh, \
	/var/www/bakproject/scripts/wg-start.sh, \
	/var/www/bakproject/scripts/wg-stop.sh

```

Modify permissions in scripts directory

```
sudo chown root:root wg-peer-add.sh wg-peer-remove.sh wg-start.sh wg-stop.sh
sudo chmod 744 wg-peer-add.sh wg-peer-remove.sh wg-start.sh wg-stop.sh
```

## Routing
Allow wireguard port
`sudo ufw allow 51820/udp`
Following port forwarding, NAT and masking is in the wireguard server config
PostUp:
```
sysctl -w net.ipv4.ip_forward=1
iptables -t nat -A POSTROUTING -o {INTERNET_INTERFACE} -j MASQUERADE
iptables -A FORWARD -i wg-server -j ACCEPT; iptables -A FORWARD -o wg-server -j ACCEPT
PostDown = 
```
PostDown:
```
sysctl -w net.ipv4.ip_forward=0
iptables -t nat -D POSTROUTING -o {INTERNET_INTERFACE} -j MASQUERADE
iptables -D FORWARD -i wg-server -j ACCEPT
iptables -D FORWARD -o wg-server -j ACCEPT

```

## Database 

```
udo apt-get install libmariadb-dev
sudo apt-get install pkg-config python3-dev default-libmysqlclient-dev build-essential
pip install mysqlclient
```

in -> sudo mysql:
```
	CREATE DATABASE wg_web;
	CREATE USER ‘django’@’localhost’ IDENTIFIED BY ‘django'; 
	GRANT ALL PRIVILEGES ON 'wg_web'.* TO ‘django’@’localhost';
	FLUSH PRIVILEGES;
```

## Django

### Logs

```
sudo mkdir /var/log/wgweb
sudo chown www-data:www-data /var/log/wgweb
sudo touch /var/log/wgweb/wg.log /var/log/wgweb/test.log
sudo chown www-data:$USER /var/log/wgweb/wg.log /var/log/wgweb/test.log
sudo chmod 660 /var/log/wgweb/wg.log /var/log/wgweb/test.log
 
```

## Encryption

In shell copy the decoded (from binary) key and put in a .env file in project root directory. 
```
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```
In the .env file copy the key that was printed and paste it at `<key>`:
```FERNET_KEY=<key>```


## Downland
### Python
```
sudo apt install python3-pip
```

### Django
in virtual enviroment
```
  pip install django
  pip install mysqlclient
  pip install cryptography
  pip install python-dotenv
```
### Database
```
sudo apt-get install libmariadb-dev
sudo apt-get install pkg-config python3-dev default-libmysqlclient-dev build-essential

```


## Sources
 - https://studygyaan.com/django/how-to-setup-django-applications-with-apache-and-mod-wsgi-on-ubuntu
 - https://docs.djangoproject.com/en/6.0/topics/auth/default/
 - https://documentation.ubuntu.com/server/how-to/wireguard-vpn/vpn-as-the-default-gateway/#using-the-vpn-as-the-default-gateway



