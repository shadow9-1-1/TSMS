"""
Models package initializer.

Imports all models for easy access and ensures they are registered
with SQLAlchemy for migrations.
"""

from app.models.user import User, Role
from app.models.teacher import Teacher
from app.models.student import Student
from app.models.course import Course, Enrollment

__all__ = ['User', 'Role', 'Teacher', 'Student', 'Course', 'Enrollment']
