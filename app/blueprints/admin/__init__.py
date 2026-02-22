"""
Admin blueprint.

Handles administrative functions including user management,
system configuration, and reporting.
"""

from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, UserRole, UserStatus
from app.models.teacher import Teacher
from app.models.student import Student
from .forms import CreateUserForm, EditUserForm, ChangePasswordForm, UserSearchForm

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
        'active_users': User.query.filter_by(status=UserStatus.ACTIVE).count()
    }
    
    # Get recent users for dashboard
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/index.html', stats=stats, recent_users=recent_users)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """List all users with search and filtering."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    role_filter = request.args.get('role', '', type=str)
    status_filter = request.args.get('status', '', type=str)
    
    # Build query
    query = User.query
    
    # Apply search filter
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            db.or_(
                User.name.ilike(search_pattern),
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern)
            )
        )
    
    # Apply role filter
    if role_filter:
        try:
            role_enum = UserRole(role_filter)
            query = query.filter(User.role == role_enum)
        except ValueError:
            pass
    
    # Apply status filter
    if status_filter:
        try:
            status_enum = UserStatus(status_filter)
            query = query.filter(User.status == status_enum)
        except ValueError:
            pass
    
    # Paginate results
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Create search form with current values
    form = UserSearchForm()
    form.search.data = search
    form.role.data = role_filter
    form.status.data = status_filter
    
    return render_template('admin/users.html', users=users, form=form)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    """Create a new user."""
    form = CreateUserForm()
    
    if form.validate_on_submit():
        user = User(
            name=form.name.data,
            username=form.username.data,
            email=form.email.data,
            role=UserRole(form.role.data),
            status=UserStatus(form.status.data)
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'User {user.username} has been created successfully.', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', form=form, user=None)


@admin_bp.route('/users/<int:id>')
@login_required
@admin_required
def user_detail(id):
    """View user details."""
    user = User.query.get_or_404(id)
    return render_template('admin/user_detail.html', user=user)


@admin_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    """Edit an existing user."""
    user = User.query.get_or_404(id)
    form = EditUserForm(
        original_username=user.username,
        original_email=user.email,
        obj=user
    )
    
    # Set initial values for role and status
    if request.method == 'GET':
        form.role.data = user.role.value
        form.status.data = user.status.value
    
    if form.validate_on_submit():
        user.name = form.name.data
        user.username = form.username.data
        user.email = form.email.data
        user.role = UserRole(form.role.data)
        user.status = UserStatus(form.status.data)
        
        db.session.commit()
        
        flash(f'User {user.username} has been updated successfully.', 'success')
        return redirect(url_for('admin.user_detail', id=user.id))
    
    return render_template('admin/user_form.html', form=form, user=user)


@admin_bp.route('/users/<int:id>/change-password', methods=['GET', 'POST'])
@login_required
@admin_required
def change_password(id):
    """Change a user's password."""
    user = User.query.get_or_404(id)
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        
        flash(f'Password for {user.username} has been changed.', 'success')
        return redirect(url_for('admin.user_detail', id=user.id))
    
    return render_template('admin/change_password.html', form=form, user=user)


@admin_bp.route('/users/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(id):
    """Activate or deactivate a user."""
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('admin.users'))
    
    # Toggle between active and inactive
    if user.status == UserStatus.ACTIVE:
        user.status = UserStatus.INACTIVE
        status_text = 'deactivated'
    else:
        user.status = UserStatus.ACTIVE
        status_text = 'activated'
    
    db.session.commit()
    
    flash(f'User {user.username} has been {status_text}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    """Delete a user."""
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin.users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} has been deleted.', 'success')
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
    return render_template('teacher/list.html', teachers=teachers)


@admin_bp.route('/students')
@login_required
@admin_required
def students():
    """List all students."""
    page = request.args.get('page', 1, type=int)
    students = Student.query.order_by(Student.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('student/list.html', students=students)
