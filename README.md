Annotation web
====================================

Annotation web is a web-based annnotation system made primarily for easy annotation of 
image sequences such as ultrasound videos and camera recordings.
It uses mainly django/python for the backend and javascript/jQuery and HTML canvas for 
the interactive annotation frontend.

It was initially developed by Erik Smistad working at both SINTEF Medical Technology and NTNU.
But has been extended by several contributors at both SINTEF and NTNU. 

Warning: This is reasearch-ware and thus seriously lack documentation and tests.
You are welcome to contribute to this project, and feel free to direct
any questions to @smistad.


Requirements
------------------------------------
* python 3
* django 2.2
* numpy
* pillow (PIL)
* +++ see requirements.txt

Development setup
------------------------------------

**1. Clone repo**
```bash
git clone https://github.com/smistad/annotationweb.git
```

**2. Setup up virtual environment**
```bash
cd annotationweb
virtualenv -ppython3 environment
source environment/bin/activate
```

**3. Install requirements**
```bash
pip install --upgrade pip # Make sure pip is up to date first
pip install -r requirements.txt
```

**4. Initialize database**
```bash
./manage.py makemigrations
./manage.py migrate
```

**5. Create super user**
```bash
./manage.py createsuperuser
```

**6. Run server and have fun**
```bash
./manage.py runserver
```

Open browser at http://localhost:8000


Deployment
------------------------------------
This guide is for Ubuntu Linux.
To setup annotation web for deployment on a server use apache2 and mod_wsgi:

**1. First install packages**
```bash
sudo apt-get install python3-pip apache2 libapache2-mod-wsgi-py3
```

**2. Then clone the repo on the server**
```bash
git clone https://github.com/smistad/annotationweb.git
```

**3. Setup up virtual environment on the server**
```bash
cd annotationweb
virtualenv -ppython3 environment
source environment/bin/activate
```

**4. Install requirements**
```bash
pip install --upgrade pip # Make sure pip is up to date first
pip install -r requirements.txt
```

**5. Initialize database**
```bash
./manage.py makemigrations
./manage.py migrate
```

**6. Create super user**
```bash
./manage.py createsuperuser
```


**7. Collect static files**
```bash
./manage.py collectstatic
```

**8. Fix user permissions**
Apache needs write access to the database.
Apache runs on the user wwww-data thus give this user write 
access to the root folder and the database file db.sqlite3
```bash
cd ..
sudo chown :www-data annotationweb
sudo chmod g+w annotationweb
cd annotationweb
sudo chown www-data db.sqlite3
sudo chmod g+w db.sqlite3
```

**9. Create an apache config**
```bash
sudo nano /etc/apache2/sites-available/annotationweb.conf
```
The config should look something like this:
```
```
Or, if you need https/SSL encryption:
```
```

**10. Enable website and have fun**
```bash
sudo a2ensite annotationweb
sudo systemctl reload apache2
```

Updating
--------

**1. Back up your database**
Your database is stored entirely in the db.sqlite3 file. Copy this to a safe location.
You may also want to keep a copy of the code as well, so you can copy the entire project folder.

**2. Pull latest changes from git**
```bash
git pull
```

**3. Update database**
```bash
./manage.py migrate
```

**4. Run server and have fun**
```bash
./manage.py runserver
```

Open browser at http://localhost:8000
