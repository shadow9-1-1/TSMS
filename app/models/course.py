"""
Course and Enrollment models.

Manages courses and student enrollment relationships.
"""

from datetime import datetime
from app.extensions import db


class Course(db.Model):
    """
    Course model.
    
    Represents a course taught by a teacher.
    """
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    credits = db.Column(db.Integer, default=3)
    max_students = db.Column(db.Integer, default=30)
    
    # Schedule
    schedule = db.Column(db.String(200))  # e.g., "Mon, Wed, Fri 9:00-10:30"
    room = db.Column(db.String(50))
    
    # Status
    status = db.Column(db.String(20), default='active')  # active, inactive, completed
    semester = db.Column(db.String(50))
    academic_year = db.Column(db.String(20))
    
    # Timestamps
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic',
                                  cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Course {self.code}>'
    
    @property
    def enrolled_count(self):
        """Get number of enrolled students."""
        return self.enrollments.filter_by(status='active').count()
    
    @property
    def available_seats(self):
        """Get number of available seats."""
        return max(0, self.max_students - self.enrolled_count)
    
    def is_full(self):
        """Check if course is at capacity."""
        return self.enrolled_count >= self.max_students
    
    @staticmethod
    def generate_course_code(prefix='CRS'):
        """Generate a unique course code."""
        import random
        import string
        while True:
            code = prefix + ''.join(random.choices(string.digits, k=4))
            if not Course.query.filter_by(code=code).first():
                return code


class Enrollment(db.Model):
    """
    Enrollment model.
    
    Represents a student's enrollment in a course.
    """
    __tablename__ = 'enrollments'
    
    id = db.Column(db.Integer, primary_key=True)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, dropped, completed
    grade = db.Column(db.String(5))  # A, B, C, D, F, or percentage
    grade_points = db.Column(db.Float)
    attendance_percentage = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # Unique constraint to prevent duplicate enrollments
    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='unique_enrollment'),
    )
    
    def __repr__(self):
        return f'<Enrollment {self.student_id} in {self.course_id}>'
    
    def drop_course(self):
        """Mark enrollment as dropped."""
        self.status = 'dropped'
        self.updated_at = datetime.utcnow()
    
    def complete_course(self, grade=None):
        """Mark enrollment as completed."""
        self.status = 'completed'
        if grade:
            self.grade = grade
        self.updated_at = datetime.utcnow()
