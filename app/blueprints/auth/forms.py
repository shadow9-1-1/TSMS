"""
Authentication forms.

WTForms for login, registration, profile management, and password changes.
Includes validation for email uniqueness, password strength, and more.
"""

from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import (
    StringField, PasswordField, BooleanField, 
    SubmitField, TextAreaField
)
from wtforms.validators import (
    DataRequired, Email, Length, EqualTo, 
    ValidationError, Regexp, Optional
)
from flask_babel import lazy_gettext as _l

from app.models import User


class LoginForm(FlaskForm):
    """
    Login form with email/username and password.
    
    Fields:
        email: Email or username for login
        password: User password
        remember_me: Keep user logged in
    """
    
    email = StringField(_l('Email or Username'), validators=[
        DataRequired(message=_l('Email or username is required.'))
    ], render_kw={
        'placeholder': _l('you@example.com'),
        'autocomplete': 'email'
    })
    
    password = PasswordField(_l('Password'), validators=[
        DataRequired(message=_l('Password is required.'))
    ], render_kw={
        'placeholder': _l('Enter your password'),
        'autocomplete': 'current-password'
    })
    
    remember_me = BooleanField(_l('Remember me'))
    
    submit = SubmitField(_l('Sign In'))


class RegistrationForm(FlaskForm):
    """
    User registration form with validation.
    
    Fields:
        email: Unique email address
        username: Unique username
        first_name: User's first name
        last_name: User's last name
        password: Password (min 8 chars)
        password_confirm: Password confirmation
    """
    
    email = StringField(_l('Email'), validators=[
        DataRequired(message=_l('Email is required.')),
        Email(message=_l('Please enter a valid email address.')),
        Length(max=120, message=_l('Email must be less than 120 characters.'))
    ], render_kw={
        'placeholder': _l('you@example.com'),
        'autocomplete': 'email'
    })
    
    username = StringField(_l('Username'), validators=[
        DataRequired(message=_l('Username is required.')),
        Length(min=3, max=64, message=_l('Username must be between 3 and 64 characters.')),
        Regexp(
            '^[A-Za-z][A-Za-z0-9_.]*$', 0,
            message=_l('Username must start with a letter and contain only letters, numbers, dots, or underscores.')
        )
    ], render_kw={
        'placeholder': _l('johndoe'),
        'autocomplete': 'username'
    })
    
    first_name = StringField(_l('First Name'), validators=[
        DataRequired(message=_l('First name is required.')),
        Length(max=64, message=_l('First name must be less than 64 characters.'))
    ], render_kw={
        'placeholder': _l('John')
    })
    
    last_name = StringField(_l('Last Name'), validators=[
        DataRequired(message=_l('Last name is required.')),
        Length(max=64, message=_l('Last name must be less than 64 characters.'))
    ], render_kw={
        'placeholder': _l('Doe')
    })
    
    password = PasswordField(_l('Password'), validators=[
        DataRequired(message=_l('Password is required.')),
        Length(min=8, message=_l('Password must be at least 8 characters long.')),
        Regexp(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
            message=_l('Password must contain at least one uppercase letter, one lowercase letter, and one number.')
        )
    ], render_kw={
        'placeholder': _l('Minimum 8 characters'),
        'autocomplete': 'new-password'
    })
    
    password_confirm = PasswordField(_l('Confirm Password'), validators=[
        DataRequired(message=_l('Please confirm your password.')),
        EqualTo('password', message=_l('Passwords must match.'))
    ], render_kw={
        'placeholder': _l('Repeat your password'),
        'autocomplete': 'new-password'
    })
    
    submit = SubmitField(_l('Create Account'))
    
    def validate_email(self, field):
        """Check if email is already registered."""
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError(_l('This email is already registered.'))
    
    def validate_username(self, field):
        """Check if username is already taken."""
        if User.query.filter_by(username=field.data.lower()).first():
            raise ValidationError(_l('This username is already taken.'))


class ProfileForm(FlaskForm):
    """
    User profile edit form.
    
    Fields:
        first_name: User's first name
        last_name: User's last name
        email: Email address (must be unique)
    """
    
    first_name = StringField(_l('First Name'), validators=[
        DataRequired(message=_l('First name is required.')),
        Length(max=64)
    ])
    
    last_name = StringField(_l('Last Name'), validators=[
        DataRequired(message=_l('Last name is required.')),
        Length(max=64)
    ])
    
    email = StringField(_l('Email'), validators=[
        DataRequired(message=_l('Email is required.')),
        Email(message=_l('Please enter a valid email address.')),
        Length(max=120)
    ])
    
    submit = SubmitField(_l('Update Profile'))
    
    def validate_email(self, field):
        """Check if email is already registered by another user."""
        user = User.query.filter_by(email=field.data.lower()).first()
        if user and user.id != current_user.id:
            raise ValidationError(_l('This email is already registered.'))


class ChangePasswordForm(FlaskForm):
    """
    Password change form.
    
    Requires current password for verification and new password with confirmation.
    
    Fields:
        current_password: User's current password
        new_password: New password (min 8 chars)
        confirm_password: New password confirmation
    """
    
    current_password = PasswordField(_l('Current Password'), validators=[
        DataRequired(message=_l('Current password is required.'))
    ], render_kw={
        'placeholder': _l('Enter current password'),
        'autocomplete': 'current-password'
    })
    
    new_password = PasswordField(_l('New Password'), validators=[
        DataRequired(message=_l('New password is required.')),
        Length(min=8, message=_l('Password must be at least 8 characters long.')),
        Regexp(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
            message=_l('Password must contain at least one uppercase letter, one lowercase letter, and one number.')
        )
    ], render_kw={
        'placeholder': _l('Minimum 8 characters'),
        'autocomplete': 'new-password'
    })
    
    confirm_password = PasswordField(_l('Confirm New Password'), validators=[
        DataRequired(message=_l('Please confirm your new password.')),
        EqualTo('new_password', message=_l('Passwords must match.'))
    ], render_kw={
        'placeholder': _l('Repeat new password'),
        'autocomplete': 'new-password'
    })
    
    submit = SubmitField(_l('Change Password'))
    
    def validate_new_password(self, field):
        """Ensure new password is different from current."""
        if field.data == self.current_password.data:
            raise ValidationError(_l('New password must be different from current password.'))


class ForgotPasswordForm(FlaskForm):
    """
    Forgot password form.
    
    Fields:
        email: User's email for password reset
    """
    
    email = StringField(_l('Email'), validators=[
        DataRequired(message=_l('Email is required.')),
        Email(message=_l('Please enter a valid email address.'))
    ], render_kw={
        'placeholder': _l('you@example.com'),
        'autocomplete': 'email'
    })
    
    submit = SubmitField(_l('Send Reset Link'))


class ResetPasswordForm(FlaskForm):
    """
    Password reset form.
    
    Fields:
        password: New password
        password_confirm: Password confirmation
    """
    
    password = PasswordField(_l('New Password'), validators=[
        DataRequired(message=_l('Password is required.')),
        Length(min=8, message=_l('Password must be at least 8 characters long.')),
        Regexp(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
            message=_l('Password must contain at least one uppercase letter, one lowercase letter, and one number.')
        )
    ], render_kw={
        'placeholder': _l('Minimum 8 characters'),
        'autocomplete': 'new-password'
    })
    
    password_confirm = PasswordField(_l('Confirm Password'), validators=[
        DataRequired(message=_l('Please confirm your password.')),
        EqualTo('password', message=_l('Passwords must match.'))
    ], render_kw={
        'placeholder': _l('Repeat your password'),
        'autocomplete': 'new-password'
    })
    
    submit = SubmitField(_l('Reset Password'))
