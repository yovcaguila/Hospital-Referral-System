# SOFTWARE DESIGN - HOSPITAL REFERRAL SYSTEM DJANGO

This is the Django version of the Hospital Referral System for Phase 4. It follows the Phase 1-3 design more closely by using Python, Django, SQLite, Django ORM, and Django built-in authentication.

## Technology Stack

| Component | Technology |
|---|---|
| Backend Framework | Python / Django |
| Frontend | HTML, CSS, JavaScript |
| Database | SQLite |
| Database Access | Django ORM |
| Authentication | Django built-in authentication |
| Testing | Django TestCase / unittest |

## Folder Structure

```text
SOFTWARE DESIGN - HOSPITAL REFERRAL SYSTEM DJANGO/
├── manage.py
├── requirements.txt
├── README.md
├── db.sqlite3
├── hospital_referral/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── referrals/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
├── templates/
│   ├── login.html
│   └── dashboard.html
└── static/
    └── styles.css
```

## Implemented Phase 1-3 Design Items

- Use cases for login, signup, logout, patient registration, referral creation, referral status update, bed capacity update, and referral history.
- Python/Django backend framework.
- SQLite database through Django ORM.
- Django built-in authentication through `django.contrib.auth`.
- Component-style separation using `urls.py`, `views.py`, `models.py`, templates, and static files.
- Class diagram entities represented by Django models:
  - `User` through Django built-in auth
  - `UserProfile`
  - `Patient`
  - `Hospital`
  - `Referral`
  - `TriageRecord`
  - `MedicalDocument`

## How to Run in PyCharm

1. Open this folder in PyCharm:

```text
SOFTWARE DESIGN - HOSPITAL REFERRAL SYSTEM DJANGO
```

2. Open PyCharm Terminal.

3. Install Django:

```powershell
pip install -r requirements.txt
```

4. Create database tables:

```powershell
python manage.py makemigrations
python manage.py migrate
```

5. Run the server:

```powershell
python manage.py runserver
```

6. Open in browser:

```text
http://127.0.0.1:8000
```

## Default Accounts

Default accounts are automatically created when the login or dashboard page loads.

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Barangay Health Center | `barangay` | `barangay123` |
| District Hospital | `district` | `district123` |
| Batangas Medical Center | `batmc` | `batmc123` |

## How to Run Tests

```powershell
python manage.py test
```

## Important Note

This Django version keeps the same intended web app appearance and features, but the backend is now aligned with the Phase 1-3 technology stack: Django, SQLite, Django ORM, and Django built-in auth.
