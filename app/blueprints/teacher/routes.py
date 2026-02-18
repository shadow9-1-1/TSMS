"""
Teacher management routes.

Handles CRUD operations for teachers including listing, creating,
editing, deleting and viewing teacher profiles.

Access:
    - Admin: Full access to all operations
    - Supervisor: Full access to all operations
    - Teacher: Can only view their own profile
"""

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, UserRole, UserStatus
from app.models.teacher import Teacher
from app.models.student import Student

from . import teacher_bp
from .forms import TeacherForm, CreateTeacherForm, TeacherSearchForm, AssignStudentForm


def admin_or_supervisor_required(f):
    """Decorator to require admin or supervisor role."""
    from functools import wraps
    
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


@teacher_bp.route('/manage')
@login_required
@admin_or_supervisor_required
def teacher_list():
    """List all teachers with search and filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get filter parameters
    search = request.args.get('search', '').strip()
    department = request.args.get('department', '').strip()
    status = request.args.get('status', '').strip()
    
    # Build query
    query = Teacher.query.join(User)
    
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            db.or_(
                User.name.ilike(search_filter),
                User.email.ilike(search_filter),
                Teacher.employee_id.ilike(search_filter),
                Teacher.specialization.ilike(search_filter)
            )
        )
    
    if department:
        query = query.filter(Teacher.department == department)
    
    if status:
        query = query.filter(Teacher.status == status)
    
    # Order by name
    query = query.order_by(User.name)
    
    # Paginate
    teachers = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template(
        'teacher/list.html',
        teachers=teachers,
        search=search,
        department=department,
        status=status
    )


@teacher_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_or_supervisor_required
def create():
    """Create a new teacher."""
    form = CreateTeacherForm()
    
    if form.validate_on_submit():
        # Create user account
        user = User(
            name=form.name.data,
            email=form.email.data.lower(),
            username=form.username.data.lower(),
            role=UserRole.TEACHER,
            status=UserStatus.ACTIVE
        )
        user.password = form.password.data
        
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create teacher profile
        teacher = Teacher(
            user_id=user.id,
            employee_id=Teacher.generate_employee_id(),
            department=form.department.data or None,
            specialization=form.specialization.data or None,
            phone=form.phone.data or None,
            qualification=form.qualification.data or None,
            experience_years=form.experience_years.data or 0,
            hire_date=form.hire_date.data,
            bio=form.bio.data or None,
            status=form.status.data
        )
        
        db.session.add(teacher)
        db.session.commit()
        
        flash(f'Teacher {user.name} has been created successfully.', 'success')
        return redirect(url_for('teacher.teacher_list'))
    
    return render_template('teacher/create.html', form=form)


@teacher_bp.route('/<int:id>')
@login_required
def detail(id):
    """View teacher profile details."""
    teacher = Teacher.query.get_or_404(id)
    
    # Check access: admin/supervisor can view all, teachers can view own
    if not (current_user.is_admin() or current_user.is_supervisor()):
        if not current_user.teacher_profile or current_user.teacher_profile.id != id:
            abort(403)
    
    # Get teacher's assigned students
    assigned_students = teacher.assigned_students.filter_by(status='active').all()
    
    # Get teacher's active courses
    active_courses = teacher.get_active_courses()
    
    return render_template(
        'teacher/detail.html',
        teacher=teacher,
        assigned_students=assigned_students,
        active_courses=active_courses
    )


@teacher_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_or_supervisor_required
def edit(id):
    """Edit an existing teacher."""
    teacher = Teacher.query.get_or_404(id)
    user = teacher.user
    
    form = TeacherForm(
        obj=teacher,
        original_email=user.email,
        original_username=user.username
    )
    
    if request.method == 'GET':
        # Pre-populate user fields
        form.name.data = user.name
        form.email.data = user.email
        form.username.data = user.username
    
    if form.validate_on_submit():
        # Update user account
        user.name = form.name.data
        user.email = form.email.data.lower()
        user.username = form.username.data.lower()
        
        # Update teacher profile
        teacher.department = form.department.data or None
        teacher.specialization = form.specialization.data or None
        teacher.phone = form.phone.data or None
        teacher.qualification = form.qualification.data or None
        teacher.experience_years = form.experience_years.data or 0
        teacher.hire_date = form.hire_date.data
        teacher.bio = form.bio.data or None
        teacher.status = form.status.data
        
        db.session.commit()
        
        flash(f'Teacher {user.name} has been updated successfully.', 'success')
        return redirect(url_for('teacher.detail', id=teacher.id))
    
    return render_template('teacher/edit.html', form=form, teacher=teacher)


@teacher_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@admin_or_supervisor_required
def delete(id):
    """Delete a teacher."""
    teacher = Teacher.query.get_or_404(id)
    user = teacher.user
    name = user.name
    
    # Check for assigned students
    if teacher.assigned_students.count() > 0:
        flash(f'Cannot delete {name}. They have students assigned. Please reassign students first.', 'error')
        return redirect(url_for('teacher.detail', id=id))
    
    # Check for active courses
    if teacher.courses.count() > 0:
        flash(f'Cannot delete {name}. They have courses assigned. Please reassign courses first.', 'error')
        return redirect(url_for('teacher.detail', id=id))
    
    # Delete teacher profile (user will be deleted via cascade)
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Teacher {name} has been deleted.', 'success')
    return redirect(url_for('teacher.teacher_list'))


@teacher_bp.route('/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_or_supervisor_required
def toggle_status(id):
    """Toggle teacher status between active and inactive."""
    teacher = Teacher.query.get_or_404(id)
    
    if teacher.status == 'active':
        teacher.status = 'inactive'
        teacher.user.status = UserStatus.INACTIVE
        flash(f'{teacher.name} has been deactivated.', 'success')
    else:
        teacher.status = 'active'
        teacher.user.status = UserStatus.ACTIVE
        flash(f'{teacher.name} has been activated.', 'success')
    
    db.session.commit()
    
    return redirect(url_for('teacher.detail', id=id))


@teacher_bp.route('/<int:id>/assign-student', methods=['GET', 'POST'])
@login_required
@admin_or_supervisor_required
def assign_student(id):
    """Assign a student to a teacher."""
    teacher = Teacher.query.get_or_404(id)
    
    # Get unassigned students
    unassigned_students = Student.query.filter(
        db.or_(
            Student.assigned_teacher_id.is_(None),
            Student.assigned_teacher_id != id
        )
    ).filter_by(status='active').order_by(Student.name).all()
    
    form = AssignStudentForm()
    form.student_id.choices = [(0, 'Select a student...')] + [
        (s.id, f'{s.name} ({s.student_id})') for s in unassigned_students
    ]
    
    if form.validate_on_submit():
        student = Student.query.get_or_404(form.student_id.data)
        student.assigned_teacher_id = teacher.id
        db.session.commit()
        
        flash(f'{student.name} has been assigned to {teacher.name}.', 'success')
        return redirect(url_for('teacher.detail', id=id))
    
    return render_template(
        'teacher/assign_student.html',
        form=form,
        teacher=teacher,
        unassigned_students=unassigned_students
    )


@teacher_bp.route('/<int:id>/unassign-student/<int:student_id>', methods=['POST'])
@login_required
@admin_or_supervisor_required
def unassign_student(id, student_id):
    """Remove a student assignment from a teacher."""
    teacher = Teacher.query.get_or_404(id)
    student = Student.query.get_or_404(student_id)
    
    if student.assigned_teacher_id != teacher.id:
        flash('This student is not assigned to this teacher.', 'error')
        return redirect(url_for('teacher.detail', id=id))
    
    student.assigned_teacher_id = None
    db.session.commit()
    
    flash(f'{student.name} has been unassigned from {teacher.name}.', 'success')
    return redirect(url_for('teacher.detail', id=id))
