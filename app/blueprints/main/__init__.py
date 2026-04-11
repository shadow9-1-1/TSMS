"""
Main blueprint.

Handles main application routes including landing page and dashboard.
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.models import User, UserRole
from app.models.student import Student
from app.models.teacher import Teacher

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
    if current_user.is_teacher():
        return redirect(url_for('teacher.index'))

    # Get dashboard statistics
    stats = {
        'total_students': Student.query.count(),
        'total_teachers': Teacher.query.count()
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
        return redirect(url_for('main.index'))


@main_bp.route('/about')
def about():
    """About page."""
    return render_template('main/about.html')
