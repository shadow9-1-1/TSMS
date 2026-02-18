"""
Application factory module.

Implements the Flask application factory pattern for creating app instances.
This pattern allows:
- Multiple app instances with different configurations
- Better testing capabilities
- Lazy initialization of extensions
- Clean blueprint registration
"""

import os
from flask import Flask

from config import config


def create_app(config_name=None):
    """
    Application factory function.
    
    Args:
        config_name: Configuration to use ('development', 'testing', 'production')
                    Defaults to FLASK_CONFIG env variable or 'development'
    
    Returns:
        Flask application instance
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'development')
    
    # Create Flask application instance
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    _init_extensions(app)
    
    # Register blueprints
    _register_blueprints(app)
    
    # Register error handlers
    _register_error_handlers(app)
    
    # Register shell context
    _register_shell_context(app)
    
    # Register template context processors
    _register_context_processors(app)
    
    # Create upload folder if it doesn't exist
    if not os.path.exists(app.config.get('UPLOAD_FOLDER', 'uploads')):
        os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
    
    return app


def _init_extensions(app):
    """Initialize Flask extensions with the app instance."""
    from app.extensions import db, migrate, login_manager, csrf
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # User loader callback for Flask-Login
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login session management."""
        return User.query.get(int(user_id))


def _register_blueprints(app):
    """Register all application blueprints."""
    from app.blueprints.main import main_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.admin import admin_bp
    from app.blueprints.teacher import teacher_bp
    from app.blueprints.student import student_bp
    from app.blueprints.supervisor import supervisor_bp
    from app.blueprints.planning import planning_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)  # url_prefix already set in blueprint
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(teacher_bp, url_prefix='/teacher')
    app.register_blueprint(student_bp, url_prefix='/student')
    app.register_blueprint(supervisor_bp, url_prefix='/supervisor')
    app.register_blueprint(planning_bp, url_prefix='/planning')


def _register_error_handlers(app):
    """Register custom error handlers."""
    from flask import render_template
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        from app.extensions import db
        db.session.rollback()
        return render_template('errors/500.html'), 500


def _register_shell_context(app):
    """Register shell context for flask shell command."""
    from app.extensions import db
    from app.models import User, UserRole, Teacher, Student, Supervisor
    
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'User': User,
            'UserRole': UserRole,
            'Teacher': Teacher,
            'Student': Student,
            'Supervisor': Supervisor
        }


def _register_context_processors(app):
    """Register Jinja2 context processors."""
    from datetime import datetime
    
    @app.context_processor
    def inject_globals():
        return {
            'current_year': datetime.utcnow().year,
            'app_name': 'TSMS'
        }
