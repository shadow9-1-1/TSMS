"""
Authentication routes.

Handles user authentication including login, logout, registration,
password management, and session handling.

Routes:
- /login: User login with email/password
- /logout: User logout and session cleanup
- /register: New user registration (if enabled)
- /profile: User profile view and edit
"""

from datetime import datetime
from flask import (
    Blueprint, render_template, redirect, url_for, 
    flash, request, current_app, session
)
from flask_login import (
    login_user, logout_user, login_required, 
    current_user, fresh_login_required
)
from urllib.parse import urlparse, urljoin

from app.extensions import db
from app.models import User, UserRole, UserStatus, Teacher, Supervisor
from app.blueprints.auth.forms import (
    LoginForm, RegistrationForm, ProfileForm, ChangePasswordForm
)


# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


# ============================================================================
# Helper Functions
# ============================================================================

def is_safe_url(target):
    """
    Check if URL is safe for redirect (prevents open redirect attacks).
    
    Args:
        target: URL to validate
        
    Returns:
        bool: True if URL is safe for redirect
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def get_redirect_target():
    """
    Get safe redirect target from request args or referrer.
    
    Returns:
        str: Safe redirect URL or None
    """
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target
    return None


# ============================================================================
# Authentication Routes
# ============================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.
    
    GET: Display login form
    POST: Validate credentials and create session
    
    Returns:
        Redirect to dashboard on success, login page on failure
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Find user by email or username
        login_identifier = form.email.data.lower().strip()
        
        # Try email first, then username
        user = User.query.filter(
            (User.email == login_identifier) | 
            (User.username == login_identifier)
        ).first()
        
        # Validate credentials
        if user is None or not user.verify_password(form.password.data):
            flash('Invalid email/username or password.', 'error')
            return render_template('auth/login.html', form=form)
        
        # Check account status
        if user.status == UserStatus.INACTIVE:
            flash('Your account has been deactivated. Please contact support.', 'error')
            return render_template('auth/login.html', form=form)
        
        if user.status == UserStatus.SUSPENDED:
            flash('Your account has been suspended. Please contact support.', 'error')
            return render_template('auth/login.html', form=form)
        
        if user.status == UserStatus.PENDING:
            flash('Your account is pending approval. Please wait for activation.', 'warning')
            return render_template('auth/login.html', form=form)
        
        # Login user
        login_user(user, remember=form.remember_me.data)
        
        # Update last login timestamp
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        
        # Set session data
        session['user_role'] = user.role.value
        session['user_name'] = user.name
        session.permanent = form.remember_me.data
        
        # Flash success message
        flash(f'Welcome back, {user.name}!', 'success')
        
        # Redirect to next page or dashboard
        next_page = get_redirect_target()
        if next_page and is_safe_url(next_page):
            return redirect(next_page)
        
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """
    Handle user logout.
    
    Clears session and logs out user.
    
    Returns:
        Redirect to home page
    """
    # Clear session data
    session.pop('user_role', None)
    session.pop('user_name', None)
    
    # Logout user
    logout_user()
    
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle user registration.
    
    GET: Display registration form
    POST: Create new user account
    
    Note: Registration may be disabled in production via config.
    
    Returns:
        Redirect to login on success, registration page on failure
    """
    # Check if registration is enabled
    if not current_app.config.get('REGISTRATION_ENABLED', True):
        flash('Registration is currently disabled.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Create new user
        user = User(
            name=f"{form.first_name.data} {form.last_name.data}",
            username=form.username.data.lower().strip(),
            email=form.email.data.lower().strip(),
            role=UserRole.TEACHER,  # Default role for self-registration
            status=UserStatus.PENDING  # Require admin approval
        )
        user.password = form.password.data
        
        try:
            db.session.add(user)
            db.session.commit()
            
            flash(
                'Registration successful! Your account is pending approval. '
                'You will be notified once activated.',
                'success'
            )
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Registration error: {e}')
            flash('An error occurred during registration. Please try again.', 'error')
    
    return render_template('auth/register.html', form=form)


# ============================================================================
# Profile Routes
# ============================================================================

@auth_bp.route('/profile')
@login_required
def profile():
    """
    Display user profile.
    
    Returns:
        Profile page template
    """
    return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    Edit user profile.
    
    GET: Display profile edit form
    POST: Update profile information
    
    Returns:
        Redirect to profile on success, edit page on failure
    """
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.name = f"{form.first_name.data} {form.last_name.data}"
        current_user.email = form.email.data.lower().strip()
        
        try:
            db.session.commit()
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Profile update error: {e}')
            flash('An error occurred while updating your profile.', 'error')
    
    # Pre-populate form with split name
    if request.method == 'GET':
        name_parts = current_user.name.split(' ', 1)
        form.first_name.data = name_parts[0]
        form.last_name.data = name_parts[1] if len(name_parts) > 1 else ''
        form.email.data = current_user.email
    
    return render_template('auth/edit_profile.html', form=form)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@fresh_login_required
def change_password():
    """
    Change user password.
    
    Requires fresh login for security.
    
    GET: Display password change form
    POST: Update password
    
    Returns:
        Redirect to profile on success, form page on failure
    """
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Verify current password
        if not current_user.verify_password(form.current_password.data):
            flash('Current password is incorrect.', 'error')
            return render_template('auth/change_password.html', form=form)
        
        # Update password
        current_user.password = form.new_password.data
        
        try:
            db.session.commit()
            flash('Password changed successfully.', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Password change error: {e}')
            flash('An error occurred while changing your password.', 'error')
    
    return render_template('auth/change_password.html', form=form)


# ============================================================================
# Session Management
# ============================================================================

@auth_bp.before_app_request
def before_request():
    """
    Execute before each request.
    
    Updates session and checks user status.
    """
    if current_user.is_authenticated:
        # Check if user account is still active
        if current_user.status != UserStatus.ACTIVE:
            logout_user()
            flash('Your account is no longer active.', 'warning')
            return redirect(url_for('auth.login'))


@auth_bp.after_app_request
def after_request(response):
    """
    Execute after each request.
    
    Sets security headers for responses.
    """
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
