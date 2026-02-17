"""
Main blueprint.

Handles main application routes including landing page and dashboard.
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.models import User, UserRole
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.course import Course

main_bp = Blueprint('main', __name__, template_folder='templates')


@main_bp.route('/')
def index():
    """Landing page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('main/index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - redirects based on user role."""
    # Get dashboard statistics
    stats = {
        'total_students': Student.query.count(),
        'total_teachers': Teacher.query.count(),
        'total_courses': Course.query.filter_by(status='active').count(),
        'active_enrollments': 0
    }
    
    # Role-specific dashboard data
    if current_user.is_admin():
        return render_template('main/dashboard.html', 
                             stats=stats, 
                             role='admin')
    elif current_user.is_supervisor():
        return render_template('main/dashboard.html', 
                             stats=stats, 
                             role='supervisor')
    else:
        # Teacher dashboard
        teacher = current_user.teacher_profile
        if teacher:
            stats['my_courses'] = teacher.courses.count()
            stats['my_students'] = teacher.get_student_count()
        return render_template('main/dashboard.html', 
                             stats=stats, 
                             role='teacher')


@main_bp.route('/about')
def about():
    """About page."""
    return render_template('main/about.html')
