"""
Planning blueprint routes.

Handles plan and task CRUD operations.

Access:
    - Admin: Full access to all plans and tasks
    - Supervisor: Full access to plans for their students
    - Teacher: Can create and manage plans for their assigned students
"""

from datetime import date
from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from functools import wraps

from app.extensions import db
from app.models import User, UserRole, UserStatus, Student, StudentStatus
from app.models.planning import Plan, Task, PlanStatus, PlanType, TaskStatus, TaskPriority

from . import planning_bp
from .forms import PlanForm, TaskForm, PlanFilterForm


def can_manage_student(student):
    """Check if current user can manage a student's plans."""
    if current_user.is_admin():
        return True
    if current_user.is_supervisor() and student.supervisor_id == current_user.id:
        return True
    if current_user.teacher_profile and student.assigned_teacher_id == current_user.teacher_profile.id:
        return True
    return False


def planning_access_required(f):
    """Decorator to require planning access (admin, supervisor, or teacher)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        if not (current_user.is_admin() or current_user.is_supervisor() or current_user.teacher_profile):
            flash('You do not have permission to access this page.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# PLAN ROUTES
# =============================================================================

@planning_bp.route('/')
@login_required
@planning_access_required
def index():
    """Planning dashboard - list all accessible plans."""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '').strip()
    type_filter = request.args.get('type', '').strip()
    
    # Build query based on user role
    if current_user.is_admin():
        query = Plan.query
    elif current_user.is_supervisor():
        student_ids = [s.id for s in Student.query.filter_by(
            supervisor_id=current_user.id
        ).all()]
        query = Plan.query.filter(
            db.or_(
                Plan.student_id.in_(student_ids),
                Plan.supervisor_id == current_user.id,
                Plan.created_by_id == current_user.id
            )
        ) if student_ids else Plan.query.filter(
            db.or_(
                Plan.supervisor_id == current_user.id,
                Plan.created_by_id == current_user.id
            )
        )
    else:
        # Teacher - show plans for their students
        teacher = current_user.teacher_profile
        if teacher:
            student_ids = [s.id for s in Student.query.filter_by(
                assigned_teacher_id=teacher.id
            ).all()]
            query = Plan.query.filter(
                db.or_(
                    Plan.student_id.in_(student_ids),
                    Plan.created_by_id == current_user.id
                )
            ) if student_ids else Plan.query.filter_by(created_by_id=current_user.id)
        else:
            query = Plan.query.filter_by(created_by_id=current_user.id)
    
    # Apply filters
    if status_filter:
        try:
            query = query.filter(Plan.status == PlanStatus(status_filter))
        except ValueError:
            pass
    
    if type_filter:
        try:
            query = query.filter(Plan.plan_type == PlanType(type_filter))
        except ValueError:
            pass
    
    plans = query.order_by(Plan.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    form = PlanFilterForm()
    form.status.data = status_filter
    form.plan_type.data = type_filter
    
    # Statistics
    stats = {
        'total': query.count(),
        'active': query.filter(Plan.status == PlanStatus.ACTIVE).count(),
        'draft': query.filter(Plan.status == PlanStatus.DRAFT).count(),
        'completed': query.filter(Plan.status == PlanStatus.COMPLETED).count()
    }
    
    return render_template('planning/index.html',
                         plans=plans,
                         form=form,
                         stats=stats)


@planning_bp.route('/create', methods=['GET', 'POST'])
@planning_bp.route('/create/<int:student_id>', methods=['GET', 'POST'])
@login_required
@planning_access_required
def create_plan(student_id=None):
    """Create a new plan for a student."""
    form = PlanForm()
    
    # Get students the user can manage
    if current_user.is_admin():
        students = Student.query.filter_by(status=StudentStatus.ACTIVE).order_by(Student.name).all()
    elif current_user.is_supervisor():
        students = Student.query.filter_by(
            supervisor_id=current_user.id,
            status=StudentStatus.ACTIVE
        ).order_by(Student.name).all()
    else:
        teacher = current_user.teacher_profile
        if teacher:
            students = Student.query.filter_by(
                assigned_teacher_id=teacher.id,
                status=StudentStatus.ACTIVE
            ).order_by(Student.name).all()
        else:
            students = []
    
    form.student_id.choices = [('', 'Select Student')] + [
        (str(s.id), f'{s.name} ({s.student_id})') for s in students
    ]
    
    # Get supervisors for assignment
    supervisors = User.query.filter(
        db.or_(
            User.role == UserRole.SUPERVISOR,
            User.role == UserRole.ADMIN
        ),
        User.status == UserStatus.ACTIVE
    ).order_by(User.name).all()
    form.supervisor_id.choices = [('', 'No Supervisor')] + [
        (str(s.id), s.name) for s in supervisors
    ]
    
    if form.validate_on_submit():
        # Verify user can manage this student
        student = Student.query.get(int(form.student_id.data))
        if not student:
            flash('Invalid student selected.', 'error')
            return render_template('planning/plan_form.html',
                                 form=form,
                                 plan=None,
                                 title='Create Plan')
        
        if not current_user.is_admin() and not can_manage_student(student):
            flash('You do not have permission to create plans for this student.', 'error')
            return render_template('planning/plan_form.html',
                                 form=form,
                                 plan=None,
                                 title='Create Plan')
        
        plan = Plan(
            title=form.title.data,
            description=form.description.data,
            student_id=int(form.student_id.data),
            created_by_id=current_user.id,
            supervisor_id=int(form.supervisor_id.data) if form.supervisor_id.data else None,
            plan_type=PlanType(form.plan_type.data),
            status=PlanStatus(form.status.data),
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            objectives=form.objectives.data,
            notes=form.notes.data
        )
        
        db.session.add(plan)
        db.session.commit()
        
        flash(f'Plan "{plan.title}" created successfully.', 'success')
        return redirect(url_for('planning.plan_detail', id=plan.id))
    
    # Pre-fill student if provided (from URL path or query param)
    if student_id:
        form.student_id.data = str(student_id)
    elif request.args.get('student_id'):
        form.student_id.data = request.args.get('student_id')
    
    return render_template('planning/plan_form.html',
                         form=form,
                         plan=None,
                         title='Create Plan')


@planning_bp.route('/<int:id>')
@login_required
@planning_access_required
def plan_detail(id):
    """View plan details with tasks."""
    plan = Plan.query.get_or_404(id)
    
    # Check access
    if not current_user.is_admin():
        if not can_manage_student(plan.student):
            flash('You do not have permission to view this plan.', 'error')
            abort(403)
    
    tasks = plan.tasks.order_by(Task.order, Task.due_date).all()
    
    # Calculate stats
    stats = {
        'total_tasks': len(tasks),
        'completed': sum(1 for t in tasks if t.status == TaskStatus.COMPLETED),
        'in_progress': sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS),
        'overdue': sum(1 for t in tasks if t.is_overdue)
    }
    
    return render_template('planning/plan_detail.html',
                         plan=plan,
                         tasks=tasks,
                         stats=stats)


@planning_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@planning_access_required
def edit_plan(id):
    """Edit an existing plan."""
    plan = Plan.query.get_or_404(id)
    
    # Check access
    if not current_user.is_admin() and not can_manage_student(plan.student):
        flash('You do not have permission to edit this plan.', 'error')
        abort(403)
    
    form = PlanForm(obj=plan)
    
    # Set choices
    if current_user.is_admin():
        students = Student.query.filter_by(status=StudentStatus.ACTIVE).order_by(Student.name).all()
    else:
        students = [plan.student]
    
    form.student_id.choices = [(str(s.id), f'{s.name} ({s.student_id})') for s in students]
    
    supervisors = User.query.filter(
        db.or_(
            User.role == UserRole.SUPERVISOR,
            User.role == UserRole.ADMIN
        )
    ).order_by(User.name).all()
    form.supervisor_id.choices = [('', 'No Supervisor')] + [
        (str(s.id), s.name) for s in supervisors
    ]
    
    if request.method == 'GET':
        form.student_id.data = str(plan.student_id)
        form.supervisor_id.data = str(plan.supervisor_id) if plan.supervisor_id else ''
        form.plan_type.data = plan.plan_type.value
        form.status.data = plan.status.value
    
    if form.validate_on_submit():
        plan.title = form.title.data
        plan.description = form.description.data
        plan.student_id = int(form.student_id.data)
        plan.supervisor_id = int(form.supervisor_id.data) if form.supervisor_id.data else None
        plan.plan_type = PlanType(form.plan_type.data)
        plan.status = PlanStatus(form.status.data)
        plan.start_date = form.start_date.data
        plan.end_date = form.end_date.data
        plan.objectives = form.objectives.data
        plan.notes = form.notes.data
        
        db.session.commit()
        
        flash(f'Plan "{plan.title}" updated successfully.', 'success')
        return redirect(url_for('planning.plan_detail', id=plan.id))
    
    return render_template('planning/plan_form.html',
                         form=form,
                         plan=plan,
                         title='Edit Plan')


@planning_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@planning_access_required
def delete_plan(id):
    """Delete a plan."""
    plan = Plan.query.get_or_404(id)
    
    # Check access
    if not current_user.is_admin() and plan.created_by_id != current_user.id:
        flash('You do not have permission to delete this plan.', 'error')
        abort(403)
    
    title = plan.title
    db.session.delete(plan)
    db.session.commit()
    
    flash(f'Plan "{title}" deleted successfully.', 'success')
    return redirect(url_for('planning.index'))


@planning_bp.route('/<int:id>/activate', methods=['POST'])
@login_required
@planning_access_required
def activate_plan(id):
    """Activate a plan."""
    plan = Plan.query.get_or_404(id)
    
    if not current_user.is_admin() and not can_manage_student(plan.student):
        abort(403)
    
    plan.status = PlanStatus.ACTIVE
    db.session.commit()
    
    flash(f'Plan "{plan.title}" is now active.', 'success')
    return redirect(url_for('planning.plan_detail', id=plan.id))


@planning_bp.route('/<int:id>/complete', methods=['POST'])
@login_required
@planning_access_required
def complete_plan(id):
    """Mark a plan as completed."""
    plan = Plan.query.get_or_404(id)
    
    if not current_user.is_admin() and not can_manage_student(plan.student):
        abort(403)
    
    plan.complete()
    
    flash(f'Plan "{plan.title}" marked as completed.', 'success')
    return redirect(url_for('planning.plan_detail', id=plan.id))


# =============================================================================
# TASK ROUTES
# =============================================================================

@planning_bp.route('/<int:plan_id>/tasks/create', methods=['GET', 'POST'])
@login_required
@planning_access_required
def create_task(plan_id):
    """Create a new task for a plan."""
    plan = Plan.query.get_or_404(plan_id)
    
    if not current_user.is_admin() and not can_manage_student(plan.student):
        flash('You do not have permission to add tasks to this plan.', 'error')
        abort(403)
    
    form = TaskForm()
    
    # Get users for assignment
    users = User.query.filter_by(status='active').order_by(User.name).all()
    form.assigned_to_id.choices = [('', 'Unassigned')] + [
        (str(u.id), u.name) for u in users
    ]
    
    if form.validate_on_submit():
        # Get max order
        max_order = db.session.query(db.func.max(Task.order)).filter_by(plan_id=plan_id).scalar() or 0
        
        task = Task(
            plan_id=plan_id,
            title=form.title.data,
            description=form.description.data,
            status=TaskStatus(form.status.data),
            priority=TaskPriority(form.priority.data),
            start_date=form.start_date.data,
            due_date=form.due_date.data,
            assigned_to_id=int(form.assigned_to_id.data) if form.assigned_to_id.data else None,
            notes=form.notes.data,
            order=max_order + 1
        )
        
        db.session.add(task)
        db.session.commit()
        
        # Update plan progress
        plan.update_progress()
        
        flash(f'Task "{task.title}" created successfully.', 'success')
        return redirect(url_for('planning.plan_detail', id=plan_id))
    
    return render_template('planning/task_form.html',
                         form=form,
                         plan=plan,
                         task=None,
                         title='Create Task')


@planning_bp.route('/tasks/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@planning_access_required
def edit_task(id):
    """Edit an existing task."""
    task = Task.query.get_or_404(id)
    plan = task.plan
    
    if not current_user.is_admin() and not can_manage_student(plan.student):
        flash('You do not have permission to edit this task.', 'error')
        abort(403)
    
    form = TaskForm(obj=task)
    
    users = User.query.filter_by(status='active').order_by(User.name).all()
    form.assigned_to_id.choices = [('', 'Unassigned')] + [
        (str(u.id), u.name) for u in users
    ]
    
    if request.method == 'GET':
        form.status.data = task.status.value
        form.priority.data = task.priority.value
        form.assigned_to_id.data = str(task.assigned_to_id) if task.assigned_to_id else ''
    
    if form.validate_on_submit():
        task.title = form.title.data
        task.description = form.description.data
        task.status = TaskStatus(form.status.data)
        task.priority = TaskPriority(form.priority.data)
        task.start_date = form.start_date.data
        task.due_date = form.due_date.data
        task.assigned_to_id = int(form.assigned_to_id.data) if form.assigned_to_id.data else None
        task.notes = form.notes.data
        
        db.session.commit()
        
        # Update plan progress
        plan.update_progress()
        
        flash(f'Task "{task.title}" updated successfully.', 'success')
        return redirect(url_for('planning.plan_detail', id=plan.id))
    
    return render_template('planning/task_form.html',
                         form=form,
                         plan=plan,
                         task=task,
                         title='Edit Task')


@planning_bp.route('/tasks/<int:id>/delete', methods=['POST'])
@login_required
@planning_access_required
def delete_task(id):
    """Delete a task."""
    task = Task.query.get_or_404(id)
    plan = task.plan
    
    if not current_user.is_admin() and not can_manage_student(plan.student):
        flash('You do not have permission to delete this task.', 'error')
        abort(403)
    
    title = task.title
    db.session.delete(task)
    db.session.commit()
    
    # Update plan progress
    plan.update_progress()
    
    flash(f'Task "{title}" deleted successfully.', 'success')
    return redirect(url_for('planning.plan_detail', id=plan.id))


@planning_bp.route('/tasks/<int:id>/complete', methods=['POST'])
@login_required
@planning_access_required
def complete_task(id):
    """Mark a task as completed."""
    task = Task.query.get_or_404(id)
    
    if not current_user.is_admin() and not can_manage_student(task.plan.student):
        abort(403)
    
    task.complete()
    
    flash(f'Task "{task.title}" marked as completed.', 'success')
    
    # Check if request is AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'plan_progress': task.plan.progress_percentage
        })
    
    return redirect(url_for('planning.plan_detail', id=task.plan_id))


@planning_bp.route('/tasks/<int:id>/start', methods=['POST'])
@login_required
@planning_access_required
def start_task(id):
    """Start a task (mark as in progress)."""
    task = Task.query.get_or_404(id)
    
    if not current_user.is_admin() and not can_manage_student(task.plan.student):
        abort(403)
    
    task.start()
    
    flash(f'Task "{task.title}" started.', 'success')
    return redirect(url_for('planning.plan_detail', id=task.plan_id))


# =============================================================================
# STUDENT PLANS VIEW
# =============================================================================

@planning_bp.route('/student/<int:student_id>')
@login_required
@planning_access_required
def student_plans(student_id):
    """View all plans for a specific student."""
    student = Student.query.get_or_404(student_id)
    
    if not current_user.is_admin() and not can_manage_student(student):
        flash('You do not have permission to view this student\'s plans.', 'error')
        abort(403)
    
    plans = student.plans.order_by(Plan.created_at.desc()).all()
    active_plan = student.get_active_plan()
    
    return render_template('planning/student_plans.html',
                         student=student,
                         plans=plans,
                         active_plan=active_plan)
