Annotation web
====================================

Setup
------------------------------------

1. Clone repo
```bash
git clone https://github.com/smistad/annotationweb.git
```

2. Setup up virtual environment
```bash
cd annotationweb
virtualenv -ppython3 environment
source environment/bin/activate
```

3. Install requirements
```bash
pip install -r requirements.txt
```

4. Initialize database
```bash
./manage.py makemigrations
./manage.py migrate
```

5. Create super user
```bash
./manage.py createsuperuser
```

6. Run server and have fun
```bash
./manage.py runserver
```

Open browser at http://localhost:8000