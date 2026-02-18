"""
Role-based access control decorators.

Provides decorators for protecting routes based on user roles.
Supports Admin, Supervisor, and Teacher roles.

Usage:
    @role_required("Admin")
    def admin_only_view():
        ...
    
    @role_required("Admin", "Supervisor")
    def admin_or_supervisor_view():
        ...
    
    @admin_required
    def admin_dashboard():
        ...
"""

from functools import wraps
from flask import redirect, url_for, flash, abort, render_template, request
from flask_login import current_user

from app.models.user import UserRole


def role_required(*roles):
    """
    Decorator to restrict access to users with specific roles.
    
    Can accept one or more role names as strings or UserRole enum values.
    If user is not authenticated, redirects to login page.
    If user is authenticated but lacks required role, shows 403 error.
    
    Args:
        *roles: One or more role names (str) or UserRole enum values.
                Role names are case-insensitive.
    
    Returns:
        Decorated function that checks role before execution.
    
    Examples:
        @role_required("Admin")
        def admin_only():
            ...
        
        @role_required("Admin", "Supervisor")
        def admin_or_supervisor():
            ...
        
        @role_required(UserRole.ADMIN, UserRole.SUPERVISOR)
        def using_enum():
            ...
    
    Raises:
        403: If authenticated user doesn't have required role.
        Redirects to login if user is not authenticated.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # Check if user account is active
            if hasattr(current_user, 'status'):
                from app.models.user import UserStatus
                if current_user.status != UserStatus.ACTIVE:
                    flash('Your account is not active. Please contact an administrator.', 'error')
                    return redirect(url_for('auth.login'))
            
            # Normalize roles to lowercase strings for comparison
            allowed_roles = set()
            for role in roles:
                if isinstance(role, UserRole):
                    allowed_roles.add(role.value.lower())
                elif isinstance(role, str):
                    allowed_roles.add(role.lower())
            
            # Check if user has any of the allowed roles
            user_role = current_user.role.value.lower() if hasattr(current_user.role, 'value') else str(current_user.role).lower()
            
            if user_role not in allowed_roles:
                # Log unauthorized access attempt (optional)
                # app.logger.warning(f'Unauthorized access attempt by {current_user.email} to {request.url}')
                
                flash('You do not have permission to access this page.', 'error')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorator to restrict access to admin users only.
    
    Shortcut for @role_required("Admin").
    
    Example:
        @admin_required
        def admin_dashboard():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_admin():
            flash('You do not have permission to access this page.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def supervisor_required(f):
    """
    Decorator to restrict access to supervisor users only.
    
    Shortcut for @role_required("Supervisor").
    
    Example:
        @supervisor_required
        def supervisor_dashboard():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_supervisor():
            flash('You do not have permission to access this page.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def teacher_required(f):
    """
    Decorator to restrict access to teacher users only.
    
    Shortcut for @role_required("Teacher").
    
    Example:
        @teacher_required
        def teacher_dashboard():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_teacher():
            flash('You do not have permission to access this page.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def admin_or_supervisor_required(f):
    """
    Decorator to restrict access to admin or supervisor users.
    
    Shortcut for @role_required("Admin", "Supervisor").
    
    Example:
        @admin_or_supervisor_required
        def management_view():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not (current_user.is_admin() or current_user.is_supervisor()):
            flash('You do not have permission to access this page.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def active_user_required(f):
    """
    Decorator to ensure the user account is active.
    
    Use this in addition to @login_required when you need
    to verify the account status.
    
    Example:
        @login_required
        @active_user_required
        def protected_view():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if hasattr(current_user, 'status'):
            from app.models.user import UserStatus
            if current_user.status != UserStatus.ACTIVE:
                flash('Your account is not active. Please contact an administrator.', 'error')
                return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function


def permission_required(permission):
    """
    Decorator to check for a specific permission.
    
    Allows for more granular access control beyond roles.
    
    Args:
        permission: The permission name to check.
    
    Example:
        @permission_required('manage_teachers')
        def teacher_management():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # Check for permission method on user model
            permission_method = f'can_{permission}'
            if hasattr(current_user, permission_method):
                if not getattr(current_user, permission_method)():
                    flash('You do not have permission to perform this action.', 'error')
                    abort(403)
            else:
                # If permission method doesn't exist, deny by default
                flash('You do not have permission to perform this action.', 'error')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Utility function for checking roles in templates
def user_has_role(user, *roles):
    """
    Check if a user has any of the specified roles.
    
    Useful in Jinja2 templates.
    
    Args:
        user: The user object to check.
        *roles: One or more role names to check against.
    
    Returns:
        True if user has any of the specified roles, False otherwise.
    
    Example (in template):
        {% if user_has_role(current_user, 'Admin', 'Supervisor') %}
            <a href="/admin">Admin Panel</a>
        {% endif %}
    """
    if not user or not user.is_authenticated:
        return False
    
    allowed_roles = set()
    for role in roles:
        if isinstance(role, UserRole):
            allowed_roles.add(role.value.lower())
        elif isinstance(role, str):
            allowed_roles.add(role.lower())
    
    user_role = user.role.value.lower() if hasattr(user.role, 'value') else str(user.role).lower()
    return user_role in allowed_roles
