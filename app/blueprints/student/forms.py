"""
Student management forms.

WTForms for student CRUD operations and enrollment.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError

from app.models.student import Student


class StudentForm(FlaskForm):
    """Student creation and editing form."""
    
    name = StringField('Full Name', validators=[
        DataRequired(message='Name is required.'),
        Length(max=128)
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please enter a valid email address.'),
        Length(max=120)
    ])
    phone = StringField('Phone', validators=[
        Optional(),
        Length(max=20)
    ])
    date_of_birth = DateField('Date of Birth', validators=[
        Optional()
    ])
    gender = SelectField('Gender', choices=[
        ('', 'Select Gender'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], validators=[Optional()])
    address = TextAreaField('Address', validators=[
        Optional(),
        Length(max=500)
    ])
    grade_level = StringField('Grade Level', validators=[
        Optional(),
        Length(max=20)
    ])
    
    # Guardian information
    guardian_name = StringField('Guardian Name', validators=[
        Optional(),
        Length(max=128)
    ])
    guardian_phone = StringField('Guardian Phone', validators=[
        Optional(),
        Length(max=20)
    ])
    guardian_email = StringField('Guardian Email', validators=[
        Optional(),
        Email(message='Please enter a valid email address.'),
        Length(max=120)
    ])
    guardian_relationship = SelectField('Relationship', choices=[
        ('', 'Select Relationship'),
        ('parent', 'Parent'),
        ('guardian', 'Guardian'),
        ('relative', 'Relative'),
        ('other', 'Other')
    ], validators=[Optional()])
    
    submit = SubmitField('Save Student')
    
    def __init__(self, *args, original_email=None, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        self.original_email = original_email
    
    def validate_email(self, field):
        """Check if email is already registered."""
        if field.data.lower() != self.original_email:
            if Student.query.filter_by(email=field.data.lower()).first():
                raise ValidationError('This email is already registered.')


class EnrollmentForm(FlaskForm):
    """Course enrollment form."""
    
    course_id = SelectField('Course', coerce=int, validators=[
        DataRequired(message='Please select a course.')
    ])
    submit = SubmitField('Enroll')
