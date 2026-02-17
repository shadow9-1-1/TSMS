"""
Student model for managing student records.

Students can enroll in courses and are tracked for academic progress.
"""

from datetime import datetime
from app.extensions import db


class Student(db.Model):
    """
    Student model.
    
    Stores student information and academic records.
    """
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    
    # Academic information
    grade_level = db.Column(db.String(20))
    enrollment_date = db.Column(db.Date, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, inactive, graduated, transferred
    
    # Guardian information
    guardian_name = db.Column(db.String(128))
    guardian_phone = db.Column(db.String(20))
    guardian_email = db.Column(db.String(120))
    guardian_relationship = db.Column(db.String(50))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic',
                                  cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.student_id}>'
    
    @property
    def full_name(self):
        """Return student's full name."""
        return f'{self.first_name} {self.last_name}'
    
    def get_enrolled_courses(self):
        """Get all courses the student is enrolled in."""
        from app.models.course import Enrollment
        return [e.course for e in self.enrollments.filter_by(status='active').all()]
    
    def get_course_count(self):
        """Get number of active course enrollments."""
        return self.enrollments.filter_by(status='active').count()
    
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
