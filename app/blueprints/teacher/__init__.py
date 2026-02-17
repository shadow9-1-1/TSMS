"""
Teacher blueprint.

Handles teacher-specific functions including course management
and student tracking.
"""

from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models.teacher import Teacher
from app.models.student import Student
from app.models.course import Course, Enrollment

teacher_bp = Blueprint('teacher', __name__, template_folder='templates')


def teacher_required(f):
    """Decorator to require teacher role or higher."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not current_user.teacher_profile and not current_user.is_supervisor():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@teacher_bp.route('/')
@login_required
@teacher_required
def index():
    """Teacher dashboard."""
    teacher = current_user.teacher_profile
    
    if teacher:
        courses = teacher.courses.all()
        student_count = teacher.get_student_count()
    else:
        # Supervisor viewing teacher section
        courses = []
        student_count = 0
    
    return render_template('teacher/index.html', 
                         teacher=teacher,
                         courses=courses,
                         student_count=student_count)


@teacher_bp.route('/courses')
@login_required
@teacher_required
def courses():
    """List teacher's courses."""
    teacher = current_user.teacher_profile
    
    if teacher:
        courses = teacher.courses.order_by(Course.created_at.desc()).all()
    else:
        courses = Course.query.order_by(Course.created_at.desc()).all()
    
    return render_template('teacher/courses.html', courses=courses)


@teacher_bp.route('/courses/<int:id>')
@login_required
@teacher_required
def course_detail(id):
    """View course details and enrolled students."""
    course = Course.query.get_or_404(id)
    
    # Check access permission
    teacher = current_user.teacher_profile
    if teacher and course.teacher_id != teacher.id and not current_user.is_supervisor():
        abort(403)
    
    enrollments = course.enrollments.order_by(Enrollment.enrollment_date.desc()).all()
    return render_template('teacher/course_detail.html', 
                         course=course, 
                         enrollments=enrollments)


@teacher_bp.route('/students')
@login_required
@teacher_required
def students():
    """List students in teacher's courses."""
    teacher = current_user.teacher_profile
    
    if teacher:
        # Get unique students from all teacher's courses
        student_ids = set()
        for course in teacher.courses:
            for enrollment in course.enrollments.filter_by(status='active'):
                student_ids.add(enrollment.student_id)
        students = Student.query.filter(Student.id.in_(student_ids)).all() if student_ids else []
    else:
        students = Student.query.all()
    
    return render_template('teacher/students.html', students=students)


@teacher_bp.route('/students/<int:id>')
@login_required
@teacher_required
def student_detail(id):
    """View student details."""
    student = Student.query.get_or_404(id)
    return render_template('teacher/student_detail.html', student=student)


@teacher_bp.route('/attendance/<int:course_id>')
@login_required
@teacher_required
def attendance(course_id):
    """Manage course attendance."""
    course = Course.query.get_or_404(course_id)
    
    # Check access permission
    teacher = current_user.teacher_profile
    if teacher and course.teacher_id != teacher.id and not current_user.is_supervisor():
        abort(403)
    
    enrollments = course.enrollments.filter_by(status='active').all()
    return render_template('teacher/attendance.html', 
                         course=course, 
                         enrollments=enrollments)


@teacher_bp.route('/grades/<int:course_id>')
@login_required
@teacher_required
def grades(course_id):
    """Manage course grades."""
    course = Course.query.get_or_404(course_id)
    
    # Check access permission
    teacher = current_user.teacher_profile
    if teacher and course.teacher_id != teacher.id and not current_user.is_supervisor():
        abort(403)
    
    enrollments = course.enrollments.all()
    return render_template('teacher/grades.html', 
                         course=course, 
                         enrollments=enrollments)
