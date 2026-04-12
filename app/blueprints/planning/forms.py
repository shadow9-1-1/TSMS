"""
Planning blueprint forms.

Forms for plan and task management.
"""

from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, DateField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Optional, Length, ValidationError
from flask_babel import lazy_gettext as _l

from app.models.planning import PlanStatus, PlanType, TaskStatus, TaskPriority


class PlanForm(FlaskForm):
    """Form for creating and editing plans."""
    
    title = StringField(_l('Plan Title'), validators=[
        DataRequired(message=_l('Title is required.')),
        Length(min=3, max=200, message=_l('Title must be between 3 and 200 characters.'))
    ])
    
    description = TextAreaField(_l('Description'), validators=[Optional()])
    
    # Changed to SelectMultipleField for multi-student support
    student_ids = SelectMultipleField(_l('Students'), validators=[
        DataRequired(message=_l('Please select at least one student.'))
    ])
    
    supervisor_id = SelectField(_l('Supervisor'), validators=[Optional()])
    
    plan_type = SelectField(_l('Plan Type'), validators=[DataRequired()],
        choices=[(t.value, t.value.replace('_', ' ').title()) for t in PlanType],
        default=PlanType.ACADEMIC.value
    )
    
    status = SelectField(_l('Status'), validators=[DataRequired()],
        choices=[(s.value, s.value.replace('_', ' ').title()) for s in PlanStatus],
        default=PlanStatus.DRAFT.value
    )
    
    start_date = DateField(_l('Start Date'), validators=[DataRequired()], default=date.today)
    
    end_date = DateField(_l('End Date'), validators=[Optional()])
    
    objectives = TextAreaField(_l('Objectives'), validators=[Optional()])
    
    notes = TextAreaField(_l('Notes'), validators=[Optional()])
    
    submit = SubmitField(_l('Save Plan'))
    
    def validate_end_date(self, field):
        """Validate end date is after start date."""
        if field.data and self.start_date.data:
            if field.data < self.start_date.data:
                raise ValidationError(_l('End date must be after start date.'))


class TaskForm(FlaskForm):
    """Form for creating and editing tasks."""
    
    title = StringField(_l('Task Title'), validators=[
        DataRequired(message=_l('Title is required.')),
        Length(min=3, max=200, message=_l('Title must be between 3 and 200 characters.'))
    ])
    
    description = TextAreaField(_l('Description'), validators=[Optional()])
    
    status = SelectField(_l('Status'), validators=[DataRequired()],
        choices=[(s.value, s.value.replace('_', ' ').title()) for s in TaskStatus],
        default=TaskStatus.PENDING.value
    )
    
    priority = SelectField(_l('Priority'), validators=[DataRequired()],
        choices=[(p.value, p.value.title()) for p in TaskPriority],
        default=TaskPriority.MEDIUM.value
    )
    
    start_date = DateField(_l('Start Date'), validators=[Optional()], default=date.today)
    
    due_date = DateField(_l('Due Date'), validators=[Optional()])
    
    assigned_to_id = SelectField(_l('Assigned To'), validators=[Optional()])
    
    notes = TextAreaField(_l('Notes'), validators=[Optional()])
    
    order = IntegerField(_l('Order'), validators=[Optional()], default=0)
    
    submit = SubmitField(_l('Save Task'))
    
    def validate_due_date(self, field):
        """Validate due date is after start date."""
        if field.data and self.start_date.data:
            if field.data < self.start_date.data:
                raise ValidationError(_l('Due date must be after start date.'))


class PlanFilterForm(FlaskForm):
    """Form for filtering plans."""
    
    status = SelectField(_l('Status'), validators=[Optional()],
        choices=[('', _l('All Statuses'))] + [(s.value, s.value.replace('_', ' ').title()) for s in PlanStatus]
    )
    
    plan_type = SelectField(_l('Type'), validators=[Optional()],
        choices=[('', _l('All Types'))] + [(t.value, t.value.replace('_', ' ').title()) for t in PlanType]
    )
