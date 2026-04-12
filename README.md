# TSMS

TSMS is a Teachers and Students Management System built with Flask. It provides role-based dashboards and workflows for administrators, supervisors, teachers, and students.

## Features

- Role-based access control (Admin, Supervisor, Teacher)
- Teacher and student management
- Planning module for student plans, tasks, and progress tracking
- Authentication and profile management
- English and Arabic localization with RTL support

## Tech Stack

- Python 3.11+
- Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-WTF
- Flask-Babel for i18n
- Jinja2 templates
- SQLite (development default)

## Quick Start

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set `FLASK_APP` and run database migrations:

Windows PowerShell:

```powershell
$env:FLASK_APP = "run.py"
flask db upgrade
```

Linux/macOS:

```bash
export FLASK_APP=run.py
flask db upgrade
```

4. Start the app:

```bash
python run.py
```

The app runs on `http://127.0.0.1:5000` by default.

## Internationalization (i18n)

The project uses `Flask-Babel` with gettext catalogs in `app/translations`.

### Supported Languages

- English (`en`) - default
- Arabic (`ar`) - RTL

### Language Switching

Switch language using the `lang` query parameter:

- English: `?lang=en`
- Arabic: `?lang=ar`

Example:

- `http://127.0.0.1:5000/?lang=en`
- `http://127.0.0.1:5000/?lang=ar`

The selected language is persisted in session.

### Extract / Update / Compile Translations

From the project root:

1. Extract translatable messages:

```bash
python -m babel.messages.frontend extract -F babel.cfg -k _ -k lazy_gettext -o messages.pot .
```

2. Initialize a new language (run once per locale):

```bash
python -m babel.messages.frontend init -i messages.pot -d app/translations -l ar
```

3. Update existing catalogs after code/template changes:

```bash
python -m babel.messages.frontend update -i messages.pot -d app/translations
```

4. Compile catalogs (`.po` -> `.mo`):

```bash
python -m babel.messages.frontend compile -d app/translations
```

### Optional: Assistive PO Translation Script

A helper script is available at `tools/translate_po.py` to prefill untranslated Arabic entries.

Example:

```bash
python tools/translate_po.py app/translations/ar/LC_MESSAGES/messages.po
```

After running it, review translations manually, then compile catalogs again.

## Project Structure

- `app/blueprints/`: feature modules (auth, admin, student, teacher, supervisor, planning)
- `app/models/`: SQLAlchemy models
- `app/templates/`: Jinja templates
- `app/translations/`: gettext locale catalogs
- `migrations/`: Alembic migration files

## Notes

- Development uses SQLite by default (`data-dev.sqlite`).
- For production, configure environment variables and use a production WSGI server (for example, gunicorn).

## Deploy for Live Demo

Use this path when you want a public link a client can open directly in the browser.

### Files already prepared for deployment

- `wsgi.py` (production entry point for gunicorn)
- `Procfile` (web start process)
- `runtime.txt` (Python version pin)
- `render.yaml` (optional one-click Render blueprint config)
- `config.py` production fallback to SQLite demo DB when `DATABASE_URL` is not set

### Fastest Render setup (manual)

1. Push this project to GitHub.
2. In Render, click **New +** -> **Web Service**.
3. Connect your GitHub repo and select this project.
4. Set:
	- Build Command: `pip install -r requirements.txt`
	- Start Command: `gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 wsgi:app`
5. Add environment variables:
	- `FLASK_CONFIG=production`
	- `SECRET_KEY=<long-random-secret>`
	- `AUTO_CREATE_DB=1`
	- `DEMO_ADMIN_NAME=<your admin display name>`
	- `DEMO_ADMIN_EMAIL=<your admin email>`
	- `DEMO_ADMIN_USERNAME=<your admin username>`
	- `DEMO_ADMIN_PASSWORD=<your admin password>`
6. Click **Create Web Service** and wait for deploy.
7. Open the generated Render URL and log in with the demo admin credentials.

### Alternative setup with render.yaml

If you use Render Blueprint flow, Render can read `render.yaml` and prefill service config.
You still need to set the demo admin values (`DEMO_ADMIN_*`) before first successful login.

### Environment variables summary

You can copy values from `.env.example` when filling Render environment variables.

Required:

- `FLASK_CONFIG=production`
- `SECRET_KEY=<long-random-secret>`

Recommended for easy demo access:

- `AUTO_CREATE_DB=1`
- `DEMO_ADMIN_NAME`, `DEMO_ADMIN_EMAIL`, `DEMO_ADMIN_USERNAME`, `DEMO_ADMIN_PASSWORD`

Optional:

- `DATABASE_URL` (if you want Postgres instead of SQLite)

### Start command

`gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 wsgi:app`

### Known demo limitations

- If you use SQLite on free hosting, data can be reset on redeploy/restart.
- This setup is optimized for fast demo delivery, not long-term production scale.
- Self-registration currently creates pending accounts; use the demo admin login for immediate access.

### Final checklist before clicking deploy

1. Repo is pushed with the latest files.
2. Build command is `pip install -r requirements.txt`.
3. Start command points to `wsgi:app`.
4. `FLASK_CONFIG=production` is set.
5. `SECRET_KEY` is set.
6. `DEMO_ADMIN_*` values are set (so login works immediately).
7. Deploy logs show gunicorn started without import errors.
8. Open the public URL and verify login page, static assets, and dashboard after sign-in.
