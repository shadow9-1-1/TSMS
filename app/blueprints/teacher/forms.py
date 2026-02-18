"""
Teacher management forms.

WTForms for teacher CRUD operations.
"""

from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, DateField, 
    IntegerField, PasswordField, SubmitField
)
from wtforms.validators import (
    DataRequired, Email, Length, Optional, ValidationError, 
    NumberRange, EqualTo
)

from app.models.teacher import Teacher
from app.models import User


class TeacherForm(FlaskForm):
    """Form for creating and editing teachers."""
    
    # User account fields
    name = StringField('Full Name', validators=[
        DataRequired(message='Name is required.'),
        Length(min=2, max=128, message='Name must be between 2 and 128 characters.')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.'),
        Length(max=120)
    ])
    username = StringField('Username', validators=[
        DataRequired(message='Username is required.'),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters.')
    ])
    
    # Teacher profile fields
    department = SelectField('Department', choices=[
        ('', 'Select Department'),
        ('Mathematics', 'Mathematics'),
        ('Science', 'Science'),
        ('English', 'English'),
        ('History', 'History'),
        ('Arts', 'Arts'),
        ('Physical Education', 'Physical Education'),
        ('Computer Science', 'Computer Science'),
        ('Languages', 'Languages'),
        ('Music', 'Music'),
        ('Other', 'Other')
    ], validators=[Optional()])
    
    specialization = StringField('Specialization', validators=[
        Optional(),
        Length(max=200, message='Specialization must be less than 200 characters.')
    ])
    
    phone = StringField('Phone Number', validators=[
        Optional(),
        Length(max=20, message='Phone number must be less than 20 characters.')
    ])
    
    qualification = StringField('Qualification', validators=[
        Optional(),
        Length(max=200, message='Qualification must be less than 200 characters.')
    ])
    
    experience_years = IntegerField('Years of Experience', validators=[
        Optional(),
        NumberRange(min=0, max=50, message='Experience must be between 0 and 50 years.')
    ])
    
    hire_date = DateField('Hire Date', validators=[Optional()])
    
    bio = TextAreaField('Bio', validators=[
        Optional(),
        Length(max=1000, message='Bio must be less than 1000 characters.')
    ])
    
    status = SelectField('Status', choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave')
    ], validators=[DataRequired()])
    
    submit = SubmitField('Save Teacher')
    
    def __init__(self, *args, original_email=None, original_username=None, **kwargs):
        super(TeacherForm, self).__init__(*args, **kwargs)
        self.original_email = original_email
        self.original_username = original_username
    
    def validate_email(self, field):
        """Check if email is already registered."""
        if self.original_email and field.data.lower() == self.original_email.lower():
            return
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('This email is already registered.')
    
    def validate_username(self, field):
        """Check if username is already taken."""
        if self.original_username and field.data.lower() == self.original_username.lower():
            return
        if User.query.filter_by(username=field.data.lower()).first():
            raise ValidationError('This username is already taken.')


class CreateTeacherForm(TeacherForm):
    """Form for creating a new teacher with password."""
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=8, message='Password must be at least 8 characters.')
    ])
    
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm the password.'),
        EqualTo('password', message='Passwords must match.')
    ])


class TeacherSearchForm(FlaskForm):
    """Form for searching and filtering teachers."""
    
    search = StringField('Search', validators=[Optional()])
    department = SelectField('Department', choices=[
        ('', 'All Departments'),
        ('Mathematics', 'Mathematics'),
        ('Science', 'Science'),
        ('English', 'English'),
        ('History', 'History'),
        ('Arts', 'Arts'),
        ('Physical Education', 'Physical Education'),
        ('Computer Science', 'Computer Science'),
        ('Languages', 'Languages'),
        ('Music', 'Music'),
        ('Other', 'Other')
    ], validators=[Optional()])
    
    status = SelectField('Status', choices=[
        ('', 'All Status'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('on_leave', 'On Leave')
    ], validators=[Optional()])


class AssignStudentForm(FlaskForm):
    """Form for assigning students to a teacher."""
    
    student_id = SelectField('Student', coerce=int, validators=[
        DataRequired(message='Please select a student.')
    ])
    submit = SubmitField('Assign Student')
