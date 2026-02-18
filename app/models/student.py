"""
Student model for managing student records.

Students can be assigned to a teacher and enrolled in courses.
"""

from datetime import datetime
from enum import Enum
from app.extensions import db


class StudentStatus(Enum):
    """Enumeration for student status."""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    GRADUATED = 'graduated'
    TRANSFERRED = 'transferred'
    DROPPED = 'dropped'


class Student(db.Model):
    """
    Student model.
    
    Stores student information with optional teacher assignment.
    Students can be assigned to a teacher for supervision.
    
    Attributes:
        id: Primary key
        name: Full name of student
        email: Email address (unique)
        phone: Contact phone number
        status: Student status (active, inactive, etc.)
        assigned_teacher_id: Foreign key to Teacher (optional)
        created_at: Timestamp of record creation
    """
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, index=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    
    # Academic information
    grade_level = db.Column(db.String(20))
    enrollment_date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(
        db.Enum(StudentStatus), 
        nullable=False, 
        default=StudentStatus.ACTIVE,
        index=True
    )
    
    # Teacher assignment
    assigned_teacher_id = db.Column(
        db.Integer, 
        db.ForeignKey('teachers.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Supervisor assignment (for project/academic supervision)
    supervisor_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Guardian information
    guardian_name = db.Column(db.String(128))
    guardian_phone = db.Column(db.String(20))
    guardian_email = db.Column(db.String(120))
    guardian_relationship = db.Column(db.String(50))
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic',
                                  cascade='all, delete-orphan')
    supervisor = db.relationship('User', foreign_keys=[supervisor_id], backref='supervised_students')
    
    def __repr__(self):
        return f'<Student {self.name} ({self.status.value})>'
    
    # Status checking methods
    def is_active(self):
        """Check if student is active."""
        return self.status == StudentStatus.ACTIVE
    
    def activate(self):
        """Set student status to active."""
        self.status = StudentStatus.ACTIVE
    
    def deactivate(self):
        """Set student status to inactive."""
        self.status = StudentStatus.INACTIVE
    
    def mark_graduated(self):
        """Set student status to graduated."""
        self.status = StudentStatus.GRADUATED
    
    def mark_transferred(self):
        """Set student status to transferred."""
        self.status = StudentStatus.TRANSFERRED
    
    def mark_dropped(self):
        """Set student status to dropped."""
        self.status = StudentStatus.DROPPED
    
    # Teacher assignment
    def assign_teacher(self, teacher):
        """
        Assign a teacher to this student.
        
        Args:
            teacher: Teacher instance or teacher ID
        """
        from app.models.teacher import Teacher
        if isinstance(teacher, Teacher):
            self.assigned_teacher_id = teacher.id
        elif isinstance(teacher, int):
            self.assigned_teacher_id = teacher
        else:
            raise ValueError("Teacher must be a Teacher instance or integer ID")
    
    def unassign_teacher(self):
        """Remove teacher assignment."""
        self.assigned_teacher_id = None
    
    def get_teacher_name(self):
        """Get assigned teacher's name."""
        return self.assigned_teacher.name if self.assigned_teacher else None
    
    # Supervisor assignment
    def assign_supervisor(self, supervisor):
        """
        Assign a supervisor to this student.
        
        Args:
            supervisor: User instance or user ID (must be supervisor role)
        """
        from app.models.user import User
        if isinstance(supervisor, User):
            self.supervisor_id = supervisor.id
        elif isinstance(supervisor, int):
            self.supervisor_id = supervisor
        else:
            raise ValueError("Supervisor must be a User instance or integer ID")
    
    def unassign_supervisor(self):
        """Remove supervisor assignment."""
        self.supervisor_id = None
    
    def get_supervisor_name(self):
        """Get assigned supervisor's name."""
        return self.supervisor.name if self.supervisor else None
    
    def get_active_plan(self):
        """Get the currently active plan for this student."""
        from app.models.planning import PlanStatus
        return self.plans.filter_by(status=PlanStatus.ACTIVE).first()
    
    def get_all_plans(self):
        """Get all plans for this student."""
        return self.plans.order_by(db.desc('created_at')).all()
    
    def get_enrolled_courses(self):
        """Get all courses the student is enrolled in."""
        return [e.course for e in self.enrollments.filter_by(status='active').all()]
    
    def get_course_count(self):
        """Get number of active course enrollments."""
        return self.enrollments.filter_by(status='active').count()
    
    def to_dict(self):
        """Convert student to dictionary representation."""
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'status': self.status.value,
            'assigned_teacher_id': self.assigned_teacher_id,
            'assigned_teacher_name': self.get_teacher_name(),
            'supervisor_id': self.supervisor_id,
            'supervisor_name': self.get_supervisor_name(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def generate_student_id():
        """Generate a unique student ID."""
        import random
        import string
        year = datetime.utcnow().strftime('%Y')
        while True:
            sid = f'S{year}' + ''.join(random.choices(string.digits, k=4))
            if not Student.query.filter_by(student_id=sid).first():
                return sid
    
    @staticmethod
    def create_student(name, email, phone=None, teacher=None):
        """
        Factory method to create a new student.
        
        Args:
            name: Student's full name
            email: Email address
            phone: Contact phone (optional)
            teacher: Teacher instance or ID to assign (optional)
            
        Returns:
            Student: New student instance (committed to database)
        """
        student = Student(
            name=name,
            email=email.lower(),
            phone=phone,
            student_id=Student.generate_student_id(),
            status=StudentStatus.ACTIVE
        )
        
        if teacher:
            student.assign_teacher(teacher)
        
        db.session.add(student)
        db.session.commit()
        return student
