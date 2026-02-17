"""
Authentication decorators for role-based access control.

Provides decorators for restricting access to routes based on user roles.
Uses the UserRole enum from models for type-safe role checking.

Usage:
    @login_required
    @role_required(UserRole.ADMIN)
    def admin_only_route():
        pass
    
    @login_required
    @roles_required(UserRole.ADMIN, UserRole.SUPERVISOR)
    def admin_or_supervisor_route():
        pass
"""

from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user

from app.models import UserRole


def role_required(*roles):
    """
    Decorator to restrict access to users with specific roles.
    
    Can accept single role or multiple roles. User must have at least
    one of the specified roles to access the route.
    
    Args:
        *roles: One or more UserRole enum values
        
    Returns:
        Decorated function that checks role before execution
        
    Example:
        @role_required(UserRole.ADMIN)
        def admin_dashboard():
            pass
            
        @role_required(UserRole.ADMIN, UserRole.SUPERVISOR)
        def management_page():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # Check if user has any of the required roles
            user_role = current_user.role
            
            # Handle both enum and string role values
            allowed = False
            for role in roles:
                if isinstance(role, UserRole):
                    if user_role == role:
                        allowed = True
                        break
                elif isinstance(role, str):
                    if user_role.value == role.lower():
                        allowed = True
                        break
            
            if not allowed:
                flash('You do not have permission to access this page.', 'error')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorator to restrict access to admin users only.
    
    Shorthand for @role_required(UserRole.ADMIN)
    
    Example:
        @admin_required
        def admin_settings():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_admin():
            flash('Administrator access required.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def supervisor_required(f):
    """
    Decorator to restrict access to supervisor users only.
    
    Shorthand for @role_required(UserRole.SUPERVISOR)
    
    Example:
        @supervisor_required
        def supervisor_dashboard():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_supervisor():
            flash('Supervisor access required.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def teacher_required(f):
    """
    Decorator to restrict access to teacher users only.
    
    Shorthand for @role_required(UserRole.TEACHER)
    
    Example:
        @teacher_required
        def teacher_classes():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_teacher():
            flash('Teacher access required.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def admin_or_supervisor_required(f):
    """
    Decorator to restrict access to admin or supervisor users.
    
    Shorthand for @role_required(UserRole.ADMIN, UserRole.SUPERVISOR)
    
    Example:
        @admin_or_supervisor_required
        def management_page():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.can_manage_teachers():
            flash('Management access required.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def active_user_required(f):
    """
    Decorator to ensure user account is active.
    
    Checks that user is authenticated and has active status.
    
    Example:
        @active_user_required
        def active_users_only():
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_active_account():
            flash('Your account is not active. Please contact support.', 'error')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function
