"""
Teacher model for managing teacher profiles and assignments.

Teachers are linked to User accounts and can manage courses and students.
"""

from datetime import datetime
from app.extensions import db


class Teacher(db.Model):
    """
    Teacher profile model.
    
    Stores teacher-specific information linked to a User account.
    """
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    department = db.Column(db.String(100))
    specialization = db.Column(db.String(200))
    qualification = db.Column(db.String(200))
    experience_years = db.Column(db.Integer, default=0)
    bio = db.Column(db.Text)
    hire_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active, inactive, on_leave
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    courses = db.relationship('Course', backref='teacher', lazy='dynamic',
                              cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Teacher {self.employee_id}>'
    
    @property
    def full_name(self):
        """Get teacher's full name from user profile."""
        return self.user.full_name if self.user else 'Unknown'
    
    @property
    def email(self):
        """Get teacher's email from user profile."""
        return self.user.email if self.user else None
    
    def get_active_courses(self):
        """Get all active courses for this teacher."""
        from app.models.course import Course
        return self.courses.filter_by(status='active').all()
    
    def get_student_count(self):
        """Get total number of students across all courses."""
        total = 0
        for course in self.courses:
            total += course.enrollments.count()
        return total
    
    @staticmethod
    def generate_employee_id():
        """Generate a unique employee ID."""
        import random
        import string
        while True:
            emp_id = 'T' + ''.join(random.choices(string.digits, k=6))
            if not Teacher.query.filter_by(employee_id=emp_id).first():
                return emp_id
