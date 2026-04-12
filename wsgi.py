"""Production entry point for WSGI servers (gunicorn)."""

import os

from app import create_app
from app.extensions import db


def _is_truthy(value):
    return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}


config_name = os.getenv('FLASK_CONFIG')
if not config_name:
    config_name = 'production' if os.getenv('RENDER') else 'development'

app = create_app(config_name)


def _bootstrap_demo_state():
    """Create tables and optional demo admin for quick live demos."""
    if not _is_truthy(os.getenv('AUTO_CREATE_DB', '1')):
        return

    with app.app_context():
        db.create_all()

        demo_email = (os.getenv('DEMO_ADMIN_EMAIL') or '').strip().lower()
        demo_username = (os.getenv('DEMO_ADMIN_USERNAME') or '').strip().lower()
        demo_password = (os.getenv('DEMO_ADMIN_PASSWORD') or '').strip()
        demo_name = (os.getenv('DEMO_ADMIN_NAME') or 'Demo Admin').strip()

        if not (demo_email and demo_username and demo_password):
            return

        from app.models import User

        existing = User.query.filter(
            (User.email == demo_email) | (User.username == demo_username)
        ).first()
        if existing is None:
            User.create_admin(
                name=demo_name,
                username=demo_username,
                email=demo_email,
                password=demo_password,
            )


_bootstrap_demo_state()
