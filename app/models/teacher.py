"""
Teacher model for managing teacher profiles and assignments.

Teachers are linked to User accounts and can manage students.
"""

from datetime import datetime
from app.extensions import db
from app.models.user import UserRole


class Teacher(db.Model):
    """
    Teacher profile model.
    
    Stores teacher-specific information linked to a User account.
    Teachers can have students assigned to them directly.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User
        specialization: Teaching specialization/subject area
        phone: Contact phone number
    """
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, index=True)
    department = db.Column(db.String(100))
    specialization = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    qualification = db.Column(db.String(200))
    experience_years = db.Column(db.Integer, default=0)
    bio = db.Column(db.Text)
    hire_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active, inactive, on_leave
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False, 
        unique=True,
        index=True
    )
    
    # Relationships
    assigned_students = db.relationship(
        'Student', 
        backref='assigned_teacher', 
        lazy='dynamic',
        foreign_keys='Student.assigned_teacher_id'
    )
    
    def __repr__(self):
        return f'<Teacher {self.employee_id or self.id}>'
    
    @property
    def name(self):
        """Get teacher's name from user profile."""
        return self.user.name if self.user else None
    
    @property
    def email(self):
        """Get teacher's email from user profile."""
        return self.user.email if self.user else None
    
    def get_student_count(self):
        """Get total number of students assigned to this teacher."""
        return self.assigned_students.filter_by(status='active').count()
    
    def get_active_students(self):
        """Get all active students assigned to this teacher."""
        return self.assigned_students.filter_by(status='active').all()
    
    def to_dict(self):
        """Convert teacher to dictionary representation."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'employee_id': self.employee_id,
            'name': self.name,
            'email': self.email,
            'specialization': self.specialization,
            'phone': self.phone,
            'department': self.department,
            'student_count': self.get_student_count(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def generate_employee_id():
        """Generate a unique employee ID."""
        import random
        import string
        while True:
            emp_id = 'T' + ''.join(random.choices(string.digits, k=6))
            if not Teacher.query.filter_by(employee_id=emp_id).first():
                return emp_id
    
    @staticmethod
    def create_teacher(user, specialization=None, phone=None, department=None):
        """
        Create a teacher profile for a user.
        
        Args:
            user: User instance (must have Teacher role)
            specialization: Teaching specialization
            phone: Contact phone
            department: Department name
            
        Returns:
            Teacher: New teacher instance
        """
        if user.role != UserRole.TEACHER:
            raise ValueError("User must have Teacher role")
        
        teacher = Teacher(
            user_id=user.id,
            employee_id=Teacher.generate_employee_id(),
            specialization=specialization,
            phone=phone,
            department=department
        )
        db.session.add(teacher)
        db.session.commit()
        return teacher
