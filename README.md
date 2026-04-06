# Hangarin Task & To-Do Manager

Django project implementing the requirements from the Hangarin PDF:
- Base model timestamps
- Task, SubTask, Note, Priority, Category models
- Admin customizations (display/filter/search)
- Choice-based status fields
- Plural name refactor (`Categories`, `Priorities`)
- Data population via management commands (fixed + Faker)

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

If your environment blocks `pip` download, use an existing Python environment with Django and Faker already installed.

## Social Login Setup

This project supports social login with Google and GitHub through `django-allauth`.

Create a local `.env` file in the project root from `.env.example`, then add your provider keys there.

Example:

```powershell
Copy-Item .env.example .env
```

```env
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

Restart Django after changing `.env`.

For Google login, create an OAuth client and use this redirect URI:

- `http://127.0.0.1:8000/accounts/google/login/callback/`

For GitHub login, create an OAuth App in GitHub and use this callback URL:

- `http://127.0.0.1:8000/accounts/github/login/callback/`

If you deploy the app, create a second GitHub OAuth App or update the callback URL to match your live domain, for example:

- `https://your-domain.com/accounts/github/login/callback/`

## Seed Data

```powershell
python manage.py seed_reference_data
python manage.py seed_fake_data --tasks 20 --max-subtasks 4 --max-notes 3
```

## Admin Coverage

- `TaskAdmin`: title, status, deadline, priority, category + filters + search
- `SubTaskAdmin`: title, status, `parent_task_name` + status filter + title search
- `CategoryAdmin` and `PriorityAdmin`: name display + searchable
- `NoteAdmin`: task, content, created_at + created_at filter + content search

## PythonAnywhere Deployment (Checklist)

1. Create a PythonAnywhere account and open a Bash console.
2. Clone this repository:
   - `git clone <your-repo-url>`
3. Create and activate virtualenv:
   - `mkvirtualenv --python=/usr/bin/python3.12 hangarin-env`
4. Install dependencies:
   - `pip install -r requirements.txt`
5. Create/update database:
   - `python manage.py migrate`
6. In PythonAnywhere Web tab:
   - Set working directory to project root.
   - Set WSGI file to point to `config.wsgi`.
   - Add project path and virtualenv path.
7. Set `ALLOWED_HOSTS` in `config/settings.py` to include your PythonAnywhere domain.
8. Reload the web app.
