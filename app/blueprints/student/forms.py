"""Student management forms."""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
from flask_babel import lazy_gettext as _l

from app.models.student import Student


class StudentForm(FlaskForm):
    """Student creation and editing form."""
    
    name = StringField(_l('Full Name'), validators=[
        DataRequired(message=_l('Name is required.')),
        Length(max=128)
    ])
    email = StringField(_l('Email'), validators=[
        DataRequired(message=_l('Email is required.')),
        Email(message=_l('Please enter a valid email address.')),
        Length(max=120)
    ])
    phone = StringField(_l('Phone'), validators=[
        Optional(),
        Length(max=20)
    ])
    date_of_birth = DateField(_l('Date of Birth'), validators=[
        Optional()
    ])
    gender = SelectField(_l('Gender'), choices=[
        ('', _l('Select Gender')),
        ('male', _l('Male')),
        ('female', _l('Female')),
        ('other', _l('Other'))
    ], validators=[Optional()])
    address = TextAreaField(_l('Address'), validators=[
        Optional(),
        Length(max=500)
    ])
    grade_level = StringField(_l('Grade Level'), validators=[
        Optional(),
        Length(max=20)
    ])
    status = SelectField(_l('Status'), choices=[
        ('active', _l('Active')),
        ('inactive', _l('Inactive')),
        ('graduated', _l('Graduated')),
        ('transferred', _l('Transferred')),
        ('dropped', _l('Dropped'))
    ], validators=[DataRequired()])
    
    # Guardian information
    guardian_name = StringField(_l('Guardian Name'), validators=[
        Optional(),
        Length(max=128)
    ])
    guardian_phone = StringField(_l('Guardian Phone'), validators=[
        Optional(),
        Length(max=20)
    ])
    guardian_email = StringField(_l('Guardian Email'), validators=[
        Optional(),
        Email(message=_l('Please enter a valid email address.')),
        Length(max=120)
    ])
    guardian_relationship = SelectField(_l('Relationship'), choices=[
        ('', _l('Select Relationship')),
        ('parent', _l('Parent')),
        ('guardian', _l('Guardian')),
        ('relative', _l('Relative')),
        ('other', _l('Other'))
    ], validators=[Optional()])
    
    notes = TextAreaField(_l('Notes'), validators=[
        Optional(),
        Length(max=1000)
    ])
    
    submit = SubmitField(_l('Save Student'))
    
    def __init__(self, *args, original_email=None, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        self.original_email = original_email
    
    def validate_email(self, field):
        """Check if email is already registered."""
        if field.data.lower() != self.original_email:
            if Student.query.filter_by(email=field.data.lower()).first():
                raise ValidationError(_l('This email is already registered.'))


class StudentSearchForm(FlaskForm):
    """Form for searching/filtering students."""
    
    search = StringField(_l('Search'), validators=[Optional()])
    status = SelectField(_l('Status'), choices=[
        ('', _l('All Status')),
        ('active', _l('Active')),
        ('inactive', _l('Inactive')),
        ('graduated', _l('Graduated')),
        ('transferred', _l('Transferred')),
        ('dropped', _l('Dropped'))
    ], validators=[Optional()])
    teacher_id = SelectField(_l('Assigned Teacher'), coerce=int, validators=[Optional()])
    grade_level = StringField(_l('Grade Level'), validators=[Optional()])


class AssignTeacherForm(FlaskForm):
    """Form for assigning a student to a teacher."""
    
    teacher_id = SelectField(_l('Teacher'), coerce=int, validators=[
        DataRequired(message=_l('Please select a teacher.'))
    ])
    submit = SubmitField(_l('Assign Teacher'))
