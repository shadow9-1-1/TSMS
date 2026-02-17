"""
Blueprints package initializer.

Central location for importing all blueprints.
"""

from app.blueprints.main import main_bp
from app.blueprints.auth import auth_bp
from app.blueprints.admin import admin_bp
from app.blueprints.teacher import teacher_bp
from app.blueprints.student import student_bp

__all__ = ['main_bp', 'auth_bp', 'admin_bp', 'teacher_bp', 'student_bp']
