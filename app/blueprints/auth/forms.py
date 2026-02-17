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

from app.models import User


class LoginForm(FlaskForm):
    """
    Login form with email/username and password.
    
    Fields:
        email: Email or username for login
        password: User password
        remember_me: Keep user logged in
    """
    
    email = StringField('Email or Username', validators=[
        DataRequired(message='Email or username is required.')
    ], render_kw={
        'placeholder': 'you@example.com',
        'autocomplete': 'email'
    })
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.')
    ], render_kw={
        'placeholder': 'Enter your password',
        'autocomplete': 'current-password'
    })
    
    remember_me = BooleanField('Remember me')
    
    submit = SubmitField('Sign In')


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
    
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.'),
        Length(max=120, message='Email must be less than 120 characters.')
    ], render_kw={
        'placeholder': 'you@example.com',
        'autocomplete': 'email'
    })
    
    username = StringField('Username', validators=[
        DataRequired(message='Username is required.'),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters.'),
        Regexp(
            '^[A-Za-z][A-Za-z0-9_.]*$', 0,
            message='Username must start with a letter and contain only '
                    'letters, numbers, dots, or underscores.'
        )
    ], render_kw={
        'placeholder': 'johndoe',
        'autocomplete': 'username'
    })
    
    first_name = StringField('First Name', validators=[
        DataRequired(message='First name is required.'),
        Length(max=64, message='First name must be less than 64 characters.')
    ], render_kw={
        'placeholder': 'John'
    })
    
    last_name = StringField('Last Name', validators=[
        DataRequired(message='Last name is required.'),
        Length(max=64, message='Last name must be less than 64 characters.')
    ], render_kw={
        'placeholder': 'Doe'
    })
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=8, message='Password must be at least 8 characters long.'),
        Regexp(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
            message='Password must contain at least one uppercase letter, '
                    'one lowercase letter, and one number.'
        )
    ], render_kw={
        'placeholder': 'Minimum 8 characters',
        'autocomplete': 'new-password'
    })
    
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords must match.')
    ], render_kw={
        'placeholder': 'Repeat your password',
        'autocomplete': 'new-password'
    })
    
    submit = SubmitField('Create Account')
    
    def validate_email(self, field):
        """Check if email is already registered."""
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('This email is already registered.')
    
    def validate_username(self, field):
        """Check if username is already taken."""
        if User.query.filter_by(username=field.data.lower()).first():
            raise ValidationError('This username is already taken.')


class ProfileForm(FlaskForm):
    """
    User profile edit form.
    
    Fields:
        first_name: User's first name
        last_name: User's last name
        email: Email address (must be unique)
    """
    
    first_name = StringField('First Name', validators=[
        DataRequired(message='First name is required.'),
        Length(max=64)
    ])
    
    last_name = StringField('Last Name', validators=[
        DataRequired(message='Last name is required.'),
        Length(max=64)
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.'),
        Length(max=120)
    ])
    
    submit = SubmitField('Update Profile')
    
    def validate_email(self, field):
        """Check if email is already registered by another user."""
        user = User.query.filter_by(email=field.data.lower()).first()
        if user and user.id != current_user.id:
            raise ValidationError('This email is already registered.')


class ChangePasswordForm(FlaskForm):
    """
    Password change form.
    
    Requires current password for verification and new password with confirmation.
    
    Fields:
        current_password: User's current password
        new_password: New password (min 8 chars)
        confirm_password: New password confirmation
    """
    
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Current password is required.')
    ], render_kw={
        'placeholder': 'Enter current password',
        'autocomplete': 'current-password'
    })
    
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='New password is required.'),
        Length(min=8, message='Password must be at least 8 characters long.'),
        Regexp(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
            message='Password must contain at least one uppercase letter, '
                    'one lowercase letter, and one number.'
        )
    ], render_kw={
        'placeholder': 'Minimum 8 characters',
        'autocomplete': 'new-password'
    })
    
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password.'),
        EqualTo('new_password', message='Passwords must match.')
    ], render_kw={
        'placeholder': 'Repeat new password',
        'autocomplete': 'new-password'
    })
    
    submit = SubmitField('Change Password')
    
    def validate_new_password(self, field):
        """Ensure new password is different from current."""
        if field.data == self.current_password.data:
            raise ValidationError('New password must be different from current password.')


class ForgotPasswordForm(FlaskForm):
    """
    Forgot password form.
    
    Fields:
        email: User's email for password reset
    """
    
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.')
    ], render_kw={
        'placeholder': 'you@example.com',
        'autocomplete': 'email'
    })
    
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    """
    Password reset form.
    
    Fields:
        password: New password
        password_confirm: Password confirmation
    """
    
    password = PasswordField('New Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=8, message='Password must be at least 8 characters long.'),
        Regexp(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
            message='Password must contain at least one uppercase letter, '
                    'one lowercase letter, and one number.'
        )
    ], render_kw={
        'placeholder': 'Minimum 8 characters',
        'autocomplete': 'new-password'
    })
    
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords must match.')
    ], render_kw={
        'placeholder': 'Repeat your password',
        'autocomplete': 'new-password'
    })
    
    submit = SubmitField('Reset Password')
