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
from flask_babel import lazy_gettext as _l

from app.models.teacher import Teacher
from app.models import User


class TeacherForm(FlaskForm):
    """Form for creating and editing teachers."""
    
    # User account fields
    name = StringField(_l('Full Name'), validators=[
        DataRequired(message=_l('Name is required.')),
        Length(min=2, max=128, message=_l('Name must be between 2 and 128 characters.'))
    ])
    email = StringField(_l('Email'), validators=[
        DataRequired(message=_l('Email is required.')),
        Email(message=_l('Please enter a valid email address.')),
        Length(max=120)
    ])
    username = StringField(_l('Username'), validators=[
        DataRequired(message=_l('Username is required.')),
        Length(min=3, max=64, message=_l('Username must be between 3 and 64 characters.'))
    ])
    
    # Teacher profile fields
    department = SelectField(_l('Department'), choices=[
        ('', _l('Select Department')),
        ('Mathematics', _l('Mathematics')),
        ('Science', _l('Science')),
        ('English', _l('English')),
        ('History', _l('History')),
        ('Arts', _l('Arts')),
        ('Physical Education', _l('Physical Education')),
        ('Computer Science', _l('Computer Science')),
        ('Languages', _l('Languages')),
        ('Music', _l('Music')),
        ('Other', _l('Other'))
    ], validators=[Optional()])
    
    specialization = StringField(_l('Specialization'), validators=[
        Optional(),
        Length(max=200, message=_l('Specialization must be less than 200 characters.'))
    ])
    
    phone = StringField(_l('Phone Number'), validators=[
        Optional(),
        Length(max=20, message=_l('Phone number must be less than 20 characters.'))
    ])
    
    qualification = StringField(_l('Qualification'), validators=[
        Optional(),
        Length(max=200, message=_l('Qualification must be less than 200 characters.'))
    ])
    
    experience_years = IntegerField(_l('Years of Experience'), validators=[
        Optional(),
        NumberRange(min=0, max=50, message=_l('Experience must be between 0 and 50 years.'))
    ])
    
    hire_date = DateField(_l('Hire Date'), validators=[Optional()])
    
    bio = TextAreaField(_l('Bio'), validators=[
        Optional(),
        Length(max=1000, message=_l('Bio must be less than 1000 characters.'))
    ])
    
    status = SelectField(_l('Status'), choices=[
        ('active', _l('Active')),
        ('inactive', _l('Inactive')),
        ('on_leave', _l('On Leave'))
    ], validators=[DataRequired()])
    
    submit = SubmitField(_l('Save Teacher'))
    
    def __init__(self, *args, original_email=None, original_username=None, **kwargs):
        super(TeacherForm, self).__init__(*args, **kwargs)
        self.original_email = original_email
        self.original_username = original_username
    
    def validate_email(self, field):
        """Check if email is already registered."""
        if self.original_email and field.data.lower() == self.original_email.lower():
            return
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError(_l('This email is already registered.'))
    
    def validate_username(self, field):
        """Check if username is already taken."""
        if self.original_username and field.data.lower() == self.original_username.lower():
            return
        if User.query.filter_by(username=field.data.lower()).first():
            raise ValidationError(_l('This username is already taken.'))


class CreateTeacherForm(TeacherForm):
    """Form for creating a new teacher with password."""
    
    password = PasswordField(_l('Password'), validators=[
        DataRequired(message=_l('Password is required.')),
        Length(min=8, message=_l('Password must be at least 8 characters.'))
    ])
    
    confirm_password = PasswordField(_l('Confirm Password'), validators=[
        DataRequired(message=_l('Please confirm the password.')),
        EqualTo('password', message=_l('Passwords must match.'))
    ])


class TeacherSearchForm(FlaskForm):
    """Form for searching and filtering teachers."""
    
    search = StringField(_l('Search'), validators=[Optional()])
    department = SelectField(_l('Department'), choices=[
        ('', _l('All Departments')),
        ('Mathematics', _l('Mathematics')),
        ('Science', _l('Science')),
        ('English', _l('English')),
        ('History', _l('History')),
        ('Arts', _l('Arts')),
        ('Physical Education', _l('Physical Education')),
        ('Computer Science', _l('Computer Science')),
        ('Languages', _l('Languages')),
        ('Music', _l('Music')),
        ('Other', _l('Other'))
    ], validators=[Optional()])
    
    status = SelectField(_l('Status'), choices=[
        ('', _l('All Status')),
        ('active', _l('Active')),
        ('inactive', _l('Inactive')),
        ('on_leave', _l('On Leave'))
    ], validators=[Optional()])


class AssignStudentForm(FlaskForm):
    """Form for assigning students to a teacher."""
    
    student_id = SelectField(_l('Student'), coerce=int, validators=[
        DataRequired(message=_l('Please select a student.'))
    ])
    submit = SubmitField(_l('Assign Student'))
