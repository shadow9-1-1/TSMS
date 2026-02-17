"""
Admin blueprint.

Handles administrative functions including user management,
system configuration, and reporting.
"""

from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models.user import User, Role
from app.models.teacher import Teacher
from app.models.student import Student
from app.models.course import Course

admin_bp = Blueprint('admin', __name__, template_folder='templates')


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard."""
    stats = {
        'total_users': User.query.count(),
        'total_teachers': Teacher.query.count(),
        'total_students': Student.query.count(),
        'total_courses': Course.query.count(),
        'active_users': User.query.filter_by(is_active=True).count()
    }
    return render_template('admin/index.html', stats=stats)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """List all users."""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<int:id>')
@login_required
@admin_required
def user_detail(id):
    """View user details."""
    user = User.query.get_or_404(id)
    return render_template('admin/user_detail.html', user=user)


@admin_bp.route('/users/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(id):
    """Activate or deactivate a user."""
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/teachers')
@login_required
@admin_required
def teachers():
    """List all teachers."""
    page = request.args.get('page', 1, type=int)
    teachers = Teacher.query.order_by(Teacher.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/teachers.html', teachers=teachers)


@admin_bp.route('/students')
@login_required
@admin_required
def students():
    """List all students."""
    page = request.args.get('page', 1, type=int)
    students = Student.query.order_by(Student.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/students.html', students=students)


@admin_bp.route('/courses')
@login_required
@admin_required
def courses():
    """List all courses."""
    page = request.args.get('page', 1, type=int)
    courses = Course.query.order_by(Course.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/courses.html', courses=courses)


@admin_bp.route('/roles')
@login_required
@admin_required
def roles():
    """Manage user roles."""
    roles = Role.query.all()
    return render_template('admin/roles.html', roles=roles)


@admin_bp.route('/init-roles', methods=['POST'])
@login_required
@admin_required
def init_roles():
    """Initialize default roles."""
    Role.insert_roles()
    flash('Roles have been initialized.', 'success')
    return redirect(url_for('admin.roles'))
