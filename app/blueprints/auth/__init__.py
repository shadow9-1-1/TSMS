"""
Authentication blueprint.

Handles user authentication including login, logout, registration,
and password management.

Exports:
- auth_bp: Blueprint instance
- Decorators: role_required, admin_required, supervisor_required, teacher_required
"""

from app.blueprints.auth.routes import auth_bp
from app.blueprints.auth.decorators import (
    role_required,
    admin_required,
    supervisor_required,
    teacher_required,
    admin_or_supervisor_required,
    active_user_required
)

__all__ = [
    'auth_bp',
    'role_required',
    'admin_required',
    'supervisor_required', 
    'teacher_required',
    'admin_or_supervisor_required',
    'active_user_required'
]
