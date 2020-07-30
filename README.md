Annotation web
====================================

Requirements
------------------------------------
* python 3
* django 2.1
* numpy
* pillow (PIL)
* +++ see requirements.txt

Setup
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

Channels
--------
Need to install redis > 5.0