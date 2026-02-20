"""
Planning models for student academic and project planning.

Provides Plan and Task models for individualized student planning
with supervisor oversight.
"""

from datetime import datetime, date
from enum import Enum
from app.extensions import db


class PlanStatus(Enum):
    """Enumeration for plan status."""
    DRAFT = 'draft'
    ACTIVE = 'active'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    ON_HOLD = 'on_hold'


class PlanType(Enum):
    """Enumeration for plan types."""
    ACADEMIC = 'academic'
    PROJECT = 'project'
    RESEARCH = 'research'
    INTERNSHIP = 'internship'
    OTHER = 'other'


class TaskStatus(Enum):
    """Enumeration for task status."""
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    OVERDUE = 'overdue'
    CANCELLED = 'cancelled'


class TaskPriority(Enum):
    """Enumeration for task priority."""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'


class ObjectiveStatus(Enum):
    """Enumeration for objective status."""
    PENDING = 'pending'
    COMPLETED = 'completed'


class Plan(db.Model):
    """
    Academic or Project Plan for a student.
    
    Plans are created by teachers/supervisors for individual students
    to track academic progress, project milestones, or research goals.
    
    Attributes:
        id: Primary key
        title: Plan title
        description: Detailed description
        student_id: Student this plan belongs to
        created_by_id: User who created the plan
        supervisor_id: Assigned supervisor for oversight
        plan_type: Type of plan (academic, project, etc.)
        status: Current plan status
        start_date: Plan start date
        end_date: Expected completion date
        objectives: Plan objectives/goals
        notes: Additional notes
    """
    __tablename__ = 'plans'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    student_id = db.Column(
        db.Integer,
        db.ForeignKey('students.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    created_by_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    supervisor_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Plan details
    plan_type = db.Column(
        db.Enum(PlanType),
        nullable=False,
        default=PlanType.ACADEMIC
    )
    status = db.Column(
        db.Enum(PlanStatus),
        nullable=False,
        default=PlanStatus.DRAFT,
        index=True
    )
    
    # Timeline
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    end_date = db.Column(db.Date)
    
    # Content
    objectives = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    # Progress tracking
    progress_percentage = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref=db.backref('plans', lazy='dynamic'))
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_plans')
    supervisor = db.relationship('User', foreign_keys=[supervisor_id], backref='supervised_plans')
    tasks = db.relationship('Task', backref='plan', lazy='dynamic', cascade='all, delete-orphan')
    plan_objectives = db.relationship('Objective', backref='plan', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Plan {self.title} for Student {self.student_id}>'
    
    @property
    def is_active(self):
        """Check if plan is active."""
        return self.status == PlanStatus.ACTIVE
    
    @property
    def is_overdue(self):
        """Check if plan is overdue."""
        if self.end_date and self.status not in (PlanStatus.COMPLETED, PlanStatus.CANCELLED):
            return date.today() > self.end_date
        return False
    
    @property
    def days_remaining(self):
        """Get days remaining until end date."""
        if self.end_date:
            delta = self.end_date - date.today()
            return delta.days
        return None
    
    @property
    def task_count(self):
        """Get total number of tasks."""
        return self.tasks.count()
    
    @property
    def completed_task_count(self):
        """Get number of completed tasks."""
        return self.tasks.filter_by(status=TaskStatus.COMPLETED).count()
    
    @property
    def objective_count(self):
        """Get total number of objectives."""
        return self.plan_objectives.count()
    
    @property
    def completed_objective_count(self):
        """Get number of completed objectives."""
        return self.plan_objectives.filter_by(status=ObjectiveStatus.COMPLETED).count()
    
    def calculate_progress(self):
        """Calculate progress based on completed objectives."""
        total = self.objective_count
        if total == 0:
            return 0
        completed = self.completed_objective_count
        return int((completed / total) * 100)
    
    def update_progress(self):
        """Update progress percentage based on objectives."""
        self.progress_percentage = self.calculate_progress()
        if self.progress_percentage == 100 and self.status == PlanStatus.ACTIVE:
            self.status = PlanStatus.COMPLETED
        db.session.commit()
    
    def activate(self):
        """Activate the plan."""
        self.status = PlanStatus.ACTIVE
        db.session.commit()
    
    def complete(self):
        """Mark plan as completed."""
        self.status = PlanStatus.COMPLETED
        self.progress_percentage = 100
        db.session.commit()
    
    def cancel(self):
        """Cancel the plan."""
        self.status = PlanStatus.CANCELLED
        db.session.commit()
    
    def to_dict(self):
        """Convert plan to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'student_id': self.student_id,
            'plan_type': self.plan_type.value,
            'status': self.status.value,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'progress_percentage': self.progress_percentage,
            'task_count': self.task_count,
            'completed_task_count': self.completed_task_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Task(db.Model):
    """
    Task within a student plan.
    
    Tasks have specific start and end dates, priorities, and can be
    tracked for progress within a plan.
    
    Attributes:
        id: Primary key
        plan_id: Parent plan
        title: Task title
        description: Task description
        status: Task status
        priority: Task priority level
        start_date: Task start date
        due_date: Task due date
        completed_at: When task was completed
        assigned_to_id: User assigned to oversee task
    """
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(
        db.Integer,
        db.ForeignKey('plans.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Task details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Status and priority
    status = db.Column(
        db.Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.PENDING,
        index=True
    )
    priority = db.Column(
        db.Enum(TaskPriority),
        nullable=False,
        default=TaskPriority.MEDIUM
    )
    
    # Timeline
    start_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date)
    completed_at = db.Column(db.DateTime)
    
    # Assignment
    assigned_to_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    
    # Additional fields
    notes = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)  # For ordering tasks
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assigned_to = db.relationship('User', backref='assigned_tasks')
    
    def __repr__(self):
        return f'<Task {self.title} ({self.status.value})>'
    
    @property
    def is_overdue(self):
        """Check if task is overdue."""
        if self.due_date and self.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            return date.today() > self.due_date
        return False
    
    @property
    def days_until_due(self):
        """Get days until due date."""
        if self.due_date:
            delta = self.due_date - date.today()
            return delta.days
        return None
    
    def start(self):
        """Start the task."""
        self.status = TaskStatus.IN_PROGRESS
        if not self.start_date:
            self.start_date = date.today()
        db.session.commit()
    
    def complete(self):
        """Complete the task."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        db.session.commit()
        # Update parent plan progress
        if self.plan:
            self.plan.update_progress()
    
    def cancel(self):
        """Cancel the task."""
        self.status = TaskStatus.CANCELLED
        db.session.commit()
        if self.plan:
            self.plan.update_progress()
    
    def check_overdue(self):
        """Check and update overdue status."""
        if self.is_overdue and self.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.OVERDUE):
            self.status = TaskStatus.OVERDUE
            db.session.commit()
    
    def to_dict(self):
        """Convert task to dictionary."""
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'priority': self.priority.value,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'is_overdue': self.is_overdue,
            'days_until_due': self.days_until_due,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Objective(db.Model):
    """
    Individual objective within a student plan.
    
    Objectives are trackable items that can be marked as complete.
    Plan progress is calculated based on completed objectives.
    
    Attributes:
        id: Primary key
        plan_id: Parent plan
        text: Objective description
        status: Objective status (pending/completed)
        order: Display order
        completed_at: When objective was completed
    """
    __tablename__ = 'objectives'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(
        db.Integer,
        db.ForeignKey('plans.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Objective details
    text = db.Column(db.String(500), nullable=False)
    status = db.Column(
        db.Enum(ObjectiveStatus),
        nullable=False,
        default=ObjectiveStatus.PENDING
    )
    order = db.Column(db.Integer, default=0)
    
    # Timestamps
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Objective {self.id}: {self.text[:30]}...>'
    
    @property
    def is_completed(self):
        """Check if objective is completed."""
        return self.status == ObjectiveStatus.COMPLETED
    
    def toggle(self):
        """Toggle objective completion status."""
        if self.status == ObjectiveStatus.COMPLETED:
            self.status = ObjectiveStatus.PENDING
            self.completed_at = None
        else:
            self.status = ObjectiveStatus.COMPLETED
            self.completed_at = datetime.utcnow()
        db.session.commit()
        # Update parent plan progress
        if self.plan:
            self.plan.update_progress()
    
    def complete(self):
        """Mark objective as completed."""
        self.status = ObjectiveStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        db.session.commit()
        if self.plan:
            self.plan.update_progress()
    
    def uncomplete(self):
        """Mark objective as pending."""
        self.status = ObjectiveStatus.PENDING
        self.completed_at = None
        db.session.commit()
        if self.plan:
            self.plan.update_progress()
    
    def to_dict(self):
        """Convert objective to dictionary."""
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'text': self.text,
            'status': self.status.value,
            'is_completed': self.is_completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
