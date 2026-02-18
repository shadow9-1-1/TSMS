"""
Models package initializer.

Imports all models for easy access and ensures they are registered
with SQLAlchemy for migrations.

Exports:
- User, UserRole, UserStatus (authentication & roles)
- Teacher (teacher profiles)
- Supervisor (supervisor profiles)
- Student, StudentStatus (student records)
- Course, Enrollment (course management)
"""

from app.models.user import User, UserRole, UserStatus
from app.models.teacher import Teacher
from app.models.supervisor import Supervisor
from app.models.student import Student, StudentStatus
from app.models.course import Course, Enrollment
from app.models.planning import Plan, Task, PlanStatus, PlanType, TaskStatus, TaskPriority

__all__ = [
    'User', 
    'UserRole', 
    'UserStatus',
    'Teacher', 
    'Supervisor',
    'Student', 
    'StudentStatus',
    'Course', 
    'Enrollment',
    'Plan',
    'Task',
    'PlanStatus',
    'PlanType',
    'TaskStatus',
    'TaskPriority'
]
