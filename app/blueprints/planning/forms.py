"""
Planning blueprint forms.

Forms for plan and task management.
"""

from datetime import date
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, ValidationError

from app.models.planning import PlanStatus, PlanType, TaskStatus, TaskPriority


class PlanForm(FlaskForm):
    """Form for creating and editing plans."""
    
    title = StringField('Plan Title', validators=[
        DataRequired(message='Title is required.'),
        Length(min=3, max=200, message='Title must be between 3 and 200 characters.')
    ])
    
    description = TextAreaField('Description', validators=[Optional()])
    
    student_id = SelectField('Student', validators=[
        DataRequired(message='Please select a student.')
    ])
    
    supervisor_id = SelectField('Supervisor', validators=[Optional()])
    
    plan_type = SelectField('Plan Type', validators=[DataRequired()],
        choices=[(t.value, t.value.replace('_', ' ').title()) for t in PlanType],
        default=PlanType.ACADEMIC.value
    )
    
    status = SelectField('Status', validators=[DataRequired()],
        choices=[(s.value, s.value.replace('_', ' ').title()) for s in PlanStatus],
        default=PlanStatus.DRAFT.value
    )
    
    start_date = DateField('Start Date', validators=[DataRequired()], default=date.today)
    
    end_date = DateField('End Date', validators=[Optional()])
    
    objectives = TextAreaField('Objectives', validators=[Optional()])
    
    notes = TextAreaField('Notes', validators=[Optional()])
    
    submit = SubmitField('Save Plan')
    
    def validate_end_date(self, field):
        """Validate end date is after start date."""
        if field.data and self.start_date.data:
            if field.data < self.start_date.data:
                raise ValidationError('End date must be after start date.')


class TaskForm(FlaskForm):
    """Form for creating and editing tasks."""
    
    title = StringField('Task Title', validators=[
        DataRequired(message='Title is required.'),
        Length(min=3, max=200, message='Title must be between 3 and 200 characters.')
    ])
    
    description = TextAreaField('Description', validators=[Optional()])
    
    status = SelectField('Status', validators=[DataRequired()],
        choices=[(s.value, s.value.replace('_', ' ').title()) for s in TaskStatus],
        default=TaskStatus.PENDING.value
    )
    
    priority = SelectField('Priority', validators=[DataRequired()],
        choices=[(p.value, p.value.title()) for p in TaskPriority],
        default=TaskPriority.MEDIUM.value
    )
    
    start_date = DateField('Start Date', validators=[Optional()], default=date.today)
    
    due_date = DateField('Due Date', validators=[Optional()])
    
    assigned_to_id = SelectField('Assigned To', validators=[Optional()])
    
    notes = TextAreaField('Notes', validators=[Optional()])
    
    order = IntegerField('Order', validators=[Optional()], default=0)
    
    submit = SubmitField('Save Task')
    
    def validate_due_date(self, field):
        """Validate due date is after start date."""
        if field.data and self.start_date.data:
            if field.data < self.start_date.data:
                raise ValidationError('Due date must be after start date.')


class PlanFilterForm(FlaskForm):
    """Form for filtering plans."""
    
    status = SelectField('Status', validators=[Optional()],
        choices=[('', 'All Statuses')] + [(s.value, s.value.replace('_', ' ').title()) for s in PlanStatus]
    )
    
    plan_type = SelectField('Type', validators=[Optional()],
        choices=[('', 'All Types')] + [(t.value, t.value.replace('_', ' ').title()) for t in PlanType]
    )
