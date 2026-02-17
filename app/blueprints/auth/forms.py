"""
Authentication forms.

WTForms for login, registration, and profile management.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp

from app.models.user import User


class LoginForm(FlaskForm):
    """Login form."""
    
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.')
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """User registration form."""
    
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.'),
        Length(max=120)
    ])
    username = StringField('Username', validators=[
        DataRequired(message='Username is required.'),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters.'),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               message='Username must start with a letter and contain only letters, numbers, dots, or underscores.')
    ])
    first_name = StringField('First Name', validators=[
        DataRequired(message='First name is required.'),
        Length(max=64)
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(message='Last name is required.'),
        Length(max=64)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=8, message='Password must be at least 8 characters long.')
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Register')
    
    def validate_email(self, field):
        """Check if email is already registered."""
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email is already registered.')
    
    def validate_username(self, field):
        """Check if username is already taken."""
        if User.query.filter_by(username=field.data.lower()).first():
            raise ValidationError('Username is already taken.')


class ProfileForm(FlaskForm):
    """User profile edit form."""
    
    first_name = StringField('First Name', validators=[
        DataRequired(),
        Length(max=64)
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(),
        Length(max=64)
    ])
    phone = StringField('Phone', validators=[
        Length(max=20)
    ])
    submit = SubmitField('Update Profile')


class ChangePasswordForm(FlaskForm):
    """Password change form."""
    
    current_password = PasswordField('Current Password', validators=[
        DataRequired()
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Change Password')
