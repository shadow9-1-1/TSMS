"""
Supervisor blueprint forms.

Forms for supervisor management operations.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import Optional

from app.models import StudentStatus


class AssignSupervisorForm(FlaskForm):
    """Form for assigning a supervisor to a student."""
    
    supervisor_id = SelectField('Supervisor', validators=[Optional()])
    submit = SubmitField('Assign Supervisor')


class StudentFilterForm(FlaskForm):
    """Form for filtering students."""
    
    search = StringField('Search', validators=[Optional()])
    status = SelectField('Status', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status.choices = [('', 'All Statuses')] + [
            (s.value, s.value.title()) for s in StudentStatus
        ]
