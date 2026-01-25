# Postup

sudo tail -f /var/log/apache2/wg_web-error.log

## create project
cd /var/www/
sudo mkdir wg_web
sudo chown $USER:$USER wg_web
cd wg_web
python3 -m venv venv
source venv/bin/activate
pip install django
django-admin startproject wg_web .
python manage.py runserver
python manage.py createsuperuser

## create mariadb connection
sudo apt-get install libmariadb-dev
sudo apt-get install pkg-config python3-dev default-libmysqlclient-dev build-essential
pip install mysqlclient

sudo mysql
	CREATE DATABASE wg_web;
	CREATE USER ‘django’@’localhost’ IDENTIFIED BY ‘django'; 
	GRANT ALL PRIVILEGES ON 'wg_web'.* TO ‘django’@’localhost';
	FLUSH PRIVILEGES;
### ve wg_web/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mydb',
        'USER': 'django',
        'PASSWORD': 'password123',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {}
    }
}

python manage.py migrate

wg_web/settings.py
	STATIC_ROOT = '/var/www/bakproject/static'
	ALLOWED_HOSTS = ['127.0.0.1', 'wgweb.localhost']

python manage.py collectstatic

python manage.py runserver

## secure connection

apache conf


;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

python manage.py collectstatic



## ve apache server config
```
<VirtualHost *:443>
	SSLEngine on
	SSLCertificateFile /etc/apache2/ssl/apache.crt
	SSLCertificateKeyFile /etc/apache2/ssl/apache.key

	ServerAdmin admin@wgweb.localhost
	ServerName wgweb.localhost
	ServerAlias www.wgweb.localhost
	DocumentRoot /var/www/bakproject
	ErrorLog ${APACHE_LOG_DIR}/error.log
	CustomLog ${APACHE_LOG_DIR}/access.log combined

	Alias /static /var/www/bakproject/static
	<Directory /var/www/bakproject/static>
		Require all granted
	</Directory>

	Alias /static /var/www/bakproject/media
	<Directory /var/www/bakproject/media>
		Require all granted
	</Directory>

	<Directory /var/www/bakproject/wg_web>
		<Files wsgi.py>
			Require all granted
		</Files>
	</Directory>

	WSGIDaemonProcess wg_web python-path=/var/www/bakproject python-home=/var/www/bakproject/venv
	WSGIProcessGroup wg_web
	WSGIScriptAlias / /var/www/bakproject/wg_web/wsgi.py

</VirtualHost>


<VirtualHost *:80>
	ServerAdmin admin@wgweb.localhost
	ServerName wgweb.localhost
	ServerAlias www.wgweb.localhost
	DocumentRoot /var/www/bakproject
	ErrorLog ${APACHE_LOG_DIR}/error.log
	CustomLog ${APACHE_LOG_DIR}/access.log combined

	Alias /static /var/www/bakproject/static
	<Directory /var/www/bakproject/static>
		Require all granted
	</Directory>

	Alias /static /var/www/bakproject/media
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
### apache temporary certification
sudo a2enmod ssl
sudo mkdir -p /etc/apache2/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048  -keyout /etc/apache2/ssl/apache.key  -out /etc/apache2/ssl/apache.crt
sudo a2ensite default-ssl
sudo systemctl restart apache2


python manage.py startapp wireguardapp


## sources


https://studygyaan.com/django/how-to-setup-django-applications-with-apache-and-mod-wsgi-on-ubuntu

https://docs.djangoproject.com/en/6.0/topics/auth/default/
