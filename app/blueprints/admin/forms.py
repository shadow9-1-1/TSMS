"""
Admin blueprint forms.

Forms for user management in the admin panel.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, ValidationError
from flask_babel import lazy_gettext as _l

from app.models import User, UserRole, UserStatus


class UserForm(FlaskForm):
    """Form for creating and editing users."""
    
    name = StringField(_l('Full Name'), validators=[
        DataRequired(message=_l('Name is required.')),
        Length(min=2, max=128, message=_l('Name must be between 2 and 128 characters.'))
    ])
    
    username = StringField(_l('Username'), validators=[
        DataRequired(message=_l('Username is required.')),
        Length(min=3, max=64, message=_l('Username must be between 3 and 64 characters.'))
    ])
    
    email = StringField(_l('Email'), validators=[
        DataRequired(message=_l('Email is required.')),
        Email(message=_l('Please enter a valid email address.')),
        Length(max=128)
    ])
    
    role = SelectField(_l('Role'), validators=[DataRequired()])
    
    status = SelectField(_l('Status'), validators=[DataRequired()])
    
    def __init__(self, original_username=None, original_email=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email
        
        # Set role choices
        role_labels = {
            UserRole.ADMIN: _l('Admin'),
            UserRole.SUPERVISOR: _l('Supervisor'),
            UserRole.TEACHER: _l('Teacher'),
        }
        self.role.choices = [(role.value, role_labels.get(role, _l(role.value.title()))) for role in UserRole]
        
        # Set status choices
        status_labels = {
            UserStatus.ACTIVE: _l('Active'),
            UserStatus.INACTIVE: _l('Inactive'),
            UserStatus.SUSPENDED: _l('Suspended'),
            UserStatus.PENDING: _l('Pending'),
        }
        self.status.choices = [(status.value, status_labels.get(status, _l(status.value.title()))) for status in UserStatus]
    
    def validate_username(self, field):
        """Validate username uniqueness."""
        if field.data != self.original_username:
            user = User.query.filter_by(username=field.data).first()
            if user:
                raise ValidationError(_l('This username is already taken.'))
    
    def validate_email(self, field):
        """Validate email uniqueness."""
        if field.data != self.original_email:
            user = User.query.filter_by(email=field.data).first()
            if user:
                raise ValidationError(_l('This email is already registered.'))


class CreateUserForm(UserForm):
    """Form for creating new users with password."""
    
    password = PasswordField(_l('Password'), validators=[
        DataRequired(message=_l('Password is required.')),
        Length(min=8, message=_l('Password must be at least 8 characters.'))
    ])
    
    password2 = PasswordField(_l('Confirm Password'), validators=[
        DataRequired(message=_l('Please confirm the password.')),
        EqualTo('password', message=_l('Passwords must match.'))
    ])
    
    submit = SubmitField(_l('Create User'))


class EditUserForm(UserForm):
    """Form for editing existing users (no password)."""
    
    submit = SubmitField(_l('Update User'))


class ChangePasswordForm(FlaskForm):
    """Form for changing user password."""
    
    password = PasswordField(_l('New Password'), validators=[
        DataRequired(message=_l('Password is required.')),
        Length(min=8, message=_l('Password must be at least 8 characters.'))
    ])
    
    password2 = PasswordField(_l('Confirm New Password'), validators=[
        DataRequired(message=_l('Please confirm the password.')),
        EqualTo('password', message=_l('Passwords must match.'))
    ])
    
    submit = SubmitField(_l('Change Password'))


class UserSearchForm(FlaskForm):
    """Form for searching and filtering users."""
    
    search = StringField(_l('Search'), validators=[Optional()])
    
    role = SelectField(_l('Role'), validators=[Optional()])
    
    status = SelectField(_l('Status'), validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # All option + role choices
        role_labels = {
            UserRole.ADMIN: _l('Admin'),
            UserRole.SUPERVISOR: _l('Supervisor'),
            UserRole.TEACHER: _l('Teacher'),
        }
        self.role.choices = [('', _l('All Roles'))] + [(role.value, role_labels.get(role, _l(role.value.title()))) for role in UserRole]
        
        # All option + status choices
        status_labels = {
            UserStatus.ACTIVE: _l('Active'),
            UserStatus.INACTIVE: _l('Inactive'),
            UserStatus.SUSPENDED: _l('Suspended'),
            UserStatus.PENDING: _l('Pending'),
        }
        self.status.choices = [('', _l('All Statuses'))] + [(status.value, status_labels.get(status, _l(status.value.title()))) for status in UserStatus]
