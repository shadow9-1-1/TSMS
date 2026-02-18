"""
Student management routes.

Handles CRUD operations for students with role-based access control.

Access:
    - Admin: Full access to all operations
    - Supervisor: Full access to all operations
    - Teacher: View only students assigned to them
"""

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models.student import Student, StudentStatus
from app.models.teacher import Teacher

from . import student_bp
from .forms import StudentForm, StudentSearchForm, AssignTeacherForm


def admin_or_supervisor_required(f):
    """Decorator to require admin or supervisor role."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        
        if not (current_user.is_admin() or current_user.is_supervisor()):
            flash('You do not have permission to access this page.', 'error')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def can_view_student(student):
    """Check if current user can view a specific student."""
    if current_user.is_admin() or current_user.is_supervisor():
        return True
    
    # Teachers can only view their assigned students
    if current_user.teacher_profile:
        return student.assigned_teacher_id == current_user.teacher_profile.id
    
    return False


@student_bp.route('/manage')
@login_required
def student_list():
    """List students with role-based filtering."""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get filter parameters
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    teacher_id = request.args.get('teacher_id', '', type=str)
    
    # Build base query
    query = Student.query
    
    # Role-based filtering
    if current_user.is_admin() or current_user.is_supervisor():
        # Admin/Supervisor see all students
        pass
    elif current_user.teacher_profile:
        # Teachers only see their assigned students
        query = query.filter(Student.assigned_teacher_id == current_user.teacher_profile.id)
    else:
        # No access
        abort(403)
    
    # Apply search filter
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            db.or_(
                Student.name.ilike(search_filter),
                Student.email.ilike(search_filter),
                Student.student_id.ilike(search_filter),
                Student.phone.ilike(search_filter)
            )
        )
    
    # Apply status filter
    if status:
        try:
            status_enum = StudentStatus(status)
            query = query.filter(Student.status == status_enum)
        except ValueError:
            pass
    
    # Apply teacher filter (admin/supervisor only)
    if teacher_id and (current_user.is_admin() or current_user.is_supervisor()):
        if teacher_id == 'unassigned':
            query = query.filter(Student.assigned_teacher_id.is_(None))
        else:
            try:
                query = query.filter(Student.assigned_teacher_id == int(teacher_id))
            except ValueError:
                pass
    
    # Order by name
    query = query.order_by(Student.name)
    
    # Paginate
    students = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Get teachers for filter dropdown (admin/supervisor only)
    teachers = []
    if current_user.is_admin() or current_user.is_supervisor():
        teachers = Teacher.query.join(Teacher.user).order_by(db.text('users.name')).all()
    
    return render_template(
        'student/list.html',
        students=students,
        search=search,
        status=status,
        teacher_id=teacher_id,
        teachers=teachers,
        can_manage=current_user.is_admin() or current_user.is_supervisor()
    )


@student_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_or_supervisor_required
def create_student():
    """Create a new student."""
    form = StudentForm()
    
    if form.validate_on_submit():
        # Create student
        student = Student(
            student_id=Student.generate_student_id(),
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            phone=form.phone.data.strip() if form.phone.data else None,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data if form.gender.data else None,
            address=form.address.data.strip() if form.address.data else None,
            grade_level=form.grade_level.data.strip() if form.grade_level.data else None,
            status=StudentStatus(form.status.data),
            guardian_name=form.guardian_name.data.strip() if form.guardian_name.data else None,
            guardian_phone=form.guardian_phone.data.strip() if form.guardian_phone.data else None,
            guardian_email=form.guardian_email.data.lower().strip() if form.guardian_email.data else None,
            guardian_relationship=form.guardian_relationship.data if form.guardian_relationship.data else None,
            notes=form.notes.data.strip() if form.notes.data else None
        )
        
        db.session.add(student)
        db.session.commit()
        
        flash(f'Student {student.name} has been created successfully.', 'success')
        return redirect(url_for('student.student_detail', id=student.id))
    
    return render_template('student/create.html', form=form)


@student_bp.route('/view/<int:id>')
@login_required
def student_detail(id):
    """View student profile details."""
    student = Student.query.get_or_404(id)
    
    # Check access permission
    if not can_view_student(student):
        flash('You do not have permission to view this student.', 'error')
        abort(403)
    
    # Get available teachers for assignment
    teachers = []
    if current_user.is_admin() or current_user.is_supervisor():
        teachers = Teacher.query.filter(Teacher.status == 'active').join(
            Teacher.user
        ).order_by(db.text('users.name')).all()
    
    return render_template(
        'student/detail.html',
        student=student,
        teachers=teachers,
        can_manage=current_user.is_admin() or current_user.is_supervisor()
    )


@student_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_or_supervisor_required
def edit_student(id):
    """Edit student details."""
    student = Student.query.get_or_404(id)
    form = StudentForm(obj=student, original_email=student.email)
    
    # Set status field
    if request.method == 'GET':
        form.status.data = student.status.value
    
    if form.validate_on_submit():
        student.name = form.name.data.strip()
        student.email = form.email.data.lower().strip()
        student.phone = form.phone.data.strip() if form.phone.data else None
        student.date_of_birth = form.date_of_birth.data
        student.gender = form.gender.data if form.gender.data else None
        student.address = form.address.data.strip() if form.address.data else None
        student.grade_level = form.grade_level.data.strip() if form.grade_level.data else None
        student.status = StudentStatus(form.status.data)
        student.guardian_name = form.guardian_name.data.strip() if form.guardian_name.data else None
        student.guardian_phone = form.guardian_phone.data.strip() if form.guardian_phone.data else None
        student.guardian_email = form.guardian_email.data.lower().strip() if form.guardian_email.data else None
        student.guardian_relationship = form.guardian_relationship.data if form.guardian_relationship.data else None
        student.notes = form.notes.data.strip() if form.notes.data else None
        
        db.session.commit()
        
        flash(f'Student {student.name} has been updated successfully.', 'success')
        return redirect(url_for('student.student_detail', id=student.id))
    
    return render_template('student/edit.html', form=form, student=student)


@student_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@admin_or_supervisor_required
def delete_student(id):
    """Delete a student."""
    student = Student.query.get_or_404(id)
    name = student.name
    
    # Check if student has active enrollments
    if student.enrollments.filter_by(status='active').count() > 0:
        flash(f'Cannot delete {name}. They have active course enrollments. Please unenroll first.', 'error')
        return redirect(url_for('student.student_detail', id=id))
    
    db.session.delete(student)
    db.session.commit()
    
    flash(f'Student {name} has been deleted.', 'success')
    return redirect(url_for('student.student_list'))


@student_bp.route('/<int:id>/assign-teacher', methods=['GET', 'POST'])
@login_required
@admin_or_supervisor_required
def assign_teacher(id):
    """Assign a student to a teacher."""
    student = Student.query.get_or_404(id)
    form = AssignTeacherForm()
    
    # Get active teachers
    teachers = Teacher.query.filter(Teacher.status == 'active').join(
        Teacher.user
    ).order_by(db.text('users.name')).all()
    
    form.teacher_id.choices = [(0, 'Select a teacher...')] + [
        (t.id, f'{t.name} - {t.department or "No Department"}') for t in teachers
    ]
    
    if form.validate_on_submit():
        teacher_id = form.teacher_id.data
        
        if teacher_id == 0:
            flash('Please select a teacher.', 'error')
        else:
            teacher = Teacher.query.get(teacher_id)
            if teacher:
                student.assigned_teacher_id = teacher.id
                db.session.commit()
                flash(f'{student.name} has been assigned to {teacher.name}.', 'success')
                return redirect(url_for('student.student_detail', id=student.id))
            else:
                flash('Teacher not found.', 'error')
    
    return render_template(
        'student/assign_teacher.html',
        form=form,
        student=student,
        teachers=teachers
    )


@student_bp.route('/<int:id>/unassign-teacher', methods=['POST'])
@login_required
@admin_or_supervisor_required
def unassign_teacher(id):
    """Remove teacher assignment from a student."""
    student = Student.query.get_or_404(id)
    
    if student.assigned_teacher_id:
        teacher_name = student.assigned_teacher.name if student.assigned_teacher else 'Unknown'
        student.assigned_teacher_id = None
        db.session.commit()
        flash(f'{student.name} has been unassigned from {teacher_name}.', 'success')
    else:
        flash('Student was not assigned to any teacher.', 'info')
    
    return redirect(url_for('student.student_detail', id=student.id))


@student_bp.route('/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_or_supervisor_required
def toggle_status(id):
    """Toggle student status between active and inactive."""
    student = Student.query.get_or_404(id)
    
    if student.status == StudentStatus.ACTIVE:
        student.status = StudentStatus.INACTIVE
        flash(f'{student.name} has been deactivated.', 'success')
    else:
        student.status = StudentStatus.ACTIVE
        flash(f'{student.name} has been activated.', 'success')
    
    db.session.commit()
    return redirect(url_for('student.student_detail', id=student.id))
