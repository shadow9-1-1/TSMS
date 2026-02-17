"""
Flask extensions module.

Centralizes the initialization of all Flask extensions.
Extensions are initialized without the app instance (factory pattern),
then later bound to the app in the create_app() function.

This approach allows:
- Better testing with different app configurations
- Avoiding circular imports
- Clean separation of concerns
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Database ORM - handles all database operations
db = SQLAlchemy()

# Database migrations - tracks schema changes
migrate = Migrate()

# Authentication management - handles user sessions
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'

# CSRF protection for forms
csrf = CSRFProtect()
