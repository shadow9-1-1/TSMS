"""
Supervisor blueprint routes.

Handles supervisor dashboard, student oversight, and plan management.

Access:
    - Supervisor: Full access to supervised students and their plans
    - Admin: Full access to all students and plans
"""

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from functools import wraps

from app.extensions import db
from app.models import User, UserRole, UserStatus, Student, StudentStatus
from app.models.planning import Plan, Task, PlanStatus, TaskStatus

from . import supervisor_bp
from .forms import AssignSupervisorForm, StudentFilterForm


def supervisor_required(f):
    """Decorator to require supervisor or admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not (current_user.is_admin() or current_user.is_supervisor()):
            flash('You do not have permission to access this page.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


@supervisor_bp.route('/')
@login_required
@supervisor_required
def index():
    """Supervisor dashboard."""
    # Get supervised students
    if current_user.is_admin():
        # Admins see all students with supervisors
        supervised_students = Student.query.filter(
            Student.supervisor_id.isnot(None)
        ).order_by(Student.name).all()
        total_students = Student.query.count()
    else:
        # Supervisors see only their assigned students
        supervised_students = Student.query.filter_by(
            supervisor_id=current_user.id
        ).order_by(Student.name).all()
        total_students = len(supervised_students)
    
    # Get active plans for supervised students
    student_ids = [s.id for s in supervised_students]
    active_plans = Plan.query.filter(
        Plan.student_id.in_(student_ids),
        Plan.status == PlanStatus.ACTIVE
    ).all() if student_ids else []
    
    # Get overdue tasks
    overdue_tasks = Task.query.join(Plan).filter(
        Plan.student_id.in_(student_ids),
        Task.status == TaskStatus.OVERDUE
    ).all() if student_ids else []
    
    # Statistics
    stats = {
        'total_students': total_students,
        'active_plans': len(active_plans),
        'overdue_tasks': len(overdue_tasks),
        'pending_reviews': Plan.query.filter(
            Plan.student_id.in_(student_ids),
            Plan.status == PlanStatus.DRAFT
        ).count() if student_ids else 0
    }
    
    return render_template('supervisor/index.html',
                         supervised_students=supervised_students[:10],
                         active_plans=active_plans[:5],
                         overdue_tasks=overdue_tasks[:5],
                         stats=stats)


@supervisor_bp.route('/students')
@login_required
@supervisor_required
def student_list():
    """List all supervised students."""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    # Build query
    if current_user.is_admin():
        query = Student.query
    else:
        query = Student.query.filter_by(supervisor_id=current_user.id)
    
    # Apply search
    if search:
        search_pattern = f'%{search}%'
        query = query.filter(
            db.or_(
                Student.name.ilike(search_pattern),
                Student.student_id.ilike(search_pattern),
                Student.email.ilike(search_pattern)
            )
        )
    
    # Apply status filter
    if status_filter:
        try:
            status_enum = StudentStatus(status_filter)
            query = query.filter(Student.status == status_enum)
        except ValueError:
            pass
    
    # Paginate
    students = query.order_by(Student.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    form = StudentFilterForm()
    form.search.data = search
    form.status.data = status_filter
    
    return render_template('supervisor/students.html',
                         students=students,
                         form=form)


@supervisor_bp.route('/students/<int:id>')
@login_required
@supervisor_required
def student_detail(id):
    """View detailed student profile with plans."""
    student = Student.query.get_or_404(id)
    
    # Check access (admin can view all, supervisors only their students)
    if not current_user.is_admin() and student.supervisor_id != current_user.id:
        flash('You do not have permission to view this student.', 'error')
        abort(403)
    
    # Get student's plans
    plans = student.plans.order_by(Plan.created_at.desc()).all()
    active_plan = student.get_active_plan()
    
    return render_template('supervisor/student_detail.html',
                         student=student,
                         plans=plans,
                         active_plan=active_plan)


@supervisor_bp.route('/students/<int:id>/assign', methods=['GET', 'POST'])
@login_required
@supervisor_required
def assign_supervisor(id):
    """Assign a supervisor to a student."""
    student = Student.query.get_or_404(id)
    
    # Only admins and current supervisors can reassign
    if not current_user.is_admin():
        if student.supervisor_id and student.supervisor_id != current_user.id:
            flash('You cannot reassign this student.', 'error')
            abort(403)
    
    form = AssignSupervisorForm()
    
    # Get available supervisors
    supervisors = User.query.filter(
        db.or_(
            User.role == UserRole.SUPERVISOR,
            User.role == UserRole.ADMIN
        ),
        User.status == UserStatus.ACTIVE
    ).order_by(User.name).all()
    form.supervisor_id.choices = [('', 'Select Supervisor')] + [
        (str(s.id), s.name) for s in supervisors
    ]
    
    if form.validate_on_submit():
        if form.supervisor_id.data:
            student.supervisor_id = int(form.supervisor_id.data)
            flash(f'Supervisor assigned to {student.name}.', 'success')
        else:
            student.supervisor_id = None
            flash(f'Supervisor removed from {student.name}.', 'success')
        
        db.session.commit()
        return redirect(url_for('supervisor.student_detail', id=student.id))
    
    # Pre-fill current supervisor
    if student.supervisor_id:
        form.supervisor_id.data = str(student.supervisor_id)
    
    return render_template('supervisor/assign_supervisor.html',
                         student=student,
                         form=form)


@supervisor_bp.route('/students/<int:id>/unassign', methods=['POST'])
@login_required
@supervisor_required
def unassign_supervisor(id):
    """Remove supervisor assignment from a student."""
    student = Student.query.get_or_404(id)
    
    if not current_user.is_admin() and student.supervisor_id != current_user.id:
        flash('You cannot unassign this student.', 'error')
        abort(403)
    
    student.supervisor_id = None
    db.session.commit()
    
    flash(f'Supervisor removed from {student.name}.', 'success')
    return redirect(url_for('supervisor.student_list'))


@supervisor_bp.route('/plans')
@login_required
@supervisor_required
def plan_list():
    """List all plans for supervised students."""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '').strip()
    
    # Build query
    if current_user.is_admin():
        query = Plan.query
    else:
        # Get supervised student IDs
        student_ids = [s.id for s in Student.query.filter_by(
            supervisor_id=current_user.id
        ).all()]
        query = Plan.query.filter(Plan.student_id.in_(student_ids)) if student_ids else Plan.query.filter(False)
    
    # Apply status filter
    if status_filter:
        try:
            status_enum = PlanStatus(status_filter)
            query = query.filter(Plan.status == status_enum)
        except ValueError:
            pass
    
    # Paginate
    plans = query.order_by(Plan.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('supervisor/plans.html', plans=plans, status_filter=status_filter)


@supervisor_bp.route('/plans/<int:id>')
@login_required
@supervisor_required
def plan_detail(id):
    """View plan details."""
    plan = Plan.query.get_or_404(id)
    
    # Check access
    if not current_user.is_admin():
        if plan.student.supervisor_id != current_user.id:
            flash('You do not have permission to view this plan.', 'error')
            abort(403)
    
    tasks = plan.tasks.order_by(Task.order, Task.due_date).all()
    
    return render_template('supervisor/plan_detail.html',
                         plan=plan,
                         tasks=tasks)


@supervisor_bp.route('/unassigned')
@login_required
@supervisor_required
def unassigned_students():
    """List students without supervisors (admin only)."""
    if not current_user.is_admin():
        flash('Only administrators can access this page.', 'error')
        abort(403)
    
    page = request.args.get('page', 1, type=int)
    
    students = Student.query.filter(
        Student.supervisor_id.is_(None),
        Student.status == StudentStatus.ACTIVE
    ).order_by(Student.name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('supervisor/unassigned.html', students=students)
