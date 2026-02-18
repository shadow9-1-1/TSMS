"""
Admin blueprint forms.

Forms for user management in the admin panel.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError

from app.models import User, UserRole, UserStatus


class UserForm(FlaskForm):
    """Form for creating and editing users."""
    
    name = StringField('Full Name', validators=[
        DataRequired(message='Name is required.'),
        Length(min=2, max=128, message='Name must be between 2 and 128 characters.')
    ])
    
    username = StringField('Username', validators=[
        DataRequired(message='Username is required.'),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters.')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.'),
        Length(max=128)
    ])
    
    role = SelectField('Role', validators=[DataRequired()])
    
    status = SelectField('Status', validators=[DataRequired()])
    
    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
        
        # Set role choices
        self.role.choices = [(role.value, role.value.title()) for role in UserRole]
        
        # Set status choices
        self.status.choices = [(status.value, status.value.title()) for status in UserStatus]
    
    def validate_username(self, field):
        """Validate username uniqueness."""
        if field.data != self.original_username:
            user = User.query.filter_by(username=field.data).first()
            if user:
                raise ValidationError('This username is already taken.')
    
    def validate_email(self, field):
        """Validate email uniqueness."""
        if field.data != self.original_email:
            user = User.query.filter_by(email=field.data).first()
            if user:
                raise ValidationError('This email is already registered.')


class CreateUserForm(UserForm):
    """Form for creating new users with password."""
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=8, message='Password must be at least 8 characters.')
    ])
    
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm the password.'),
        EqualTo('password', message='Passwords must match.')
    ])
    
    submit = SubmitField('Create User')


class EditUserForm(UserForm):
    """Form for editing existing users (no password)."""
    
    submit = SubmitField('Update User')


class ChangePasswordForm(FlaskForm):
    """Form for changing user password."""
    
    password = PasswordField('New Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=8, message='Password must be at least 8 characters.')
    ])
    
    password2 = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm the password.'),
        EqualTo('password', message='Passwords must match.')
    ])
    
    submit = SubmitField('Change Password')


class UserSearchForm(FlaskForm):
    """Form for searching and filtering users."""
    
    search = StringField('Search', validators=[Optional()])
    
    role = SelectField('Role', validators=[Optional()])
    
    status = SelectField('Status', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # All option + role choices
        self.role.choices = [('', 'All Roles')] + [(role.value, role.value.title()) for role in UserRole]
        
        # All option + status choices
        self.status.choices = [('', 'All Statuses')] + [(status.value, status.value.title()) for status in UserStatus]
