"""
Student blueprint.

Handles student management including CRUD operations
and enrollment management.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from app.extensions import db
from app.models import User, UserRole
from app.models.student import Student
from app.models.course import Course, Enrollment
from app.blueprints.student.forms import StudentForm, EnrollmentForm

student_bp = Blueprint('student', __name__, template_folder='templates')


def can_manage_students():
    """Check if current user can manage students."""
    return current_user.is_authenticated and (
        current_user.is_admin() or 
        current_user.is_supervisor() or 
        current_user.teacher_profile
    )


@student_bp.route('/')
@login_required
def index():
    """List all students with pagination and search."""
    if not can_manage_students():
        abort(403)
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status = request.args.get('status', 'all')
    
    query = Student.query
    
    # Apply search filter
    if search:
        query = query.filter(
            db.or_(
                Student.name.ilike(f'%{search}%'),
                Student.student_id.ilike(f'%{search}%'),
                Student.email.ilike(f'%{search}%')
            )
        )
    
    # Apply status filter
    if status != 'all':
        query = query.filter_by(status=status)
    
    students = query.order_by(Student.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('student/index.html', 
                         students=students,
                         search=search,
                         status=status)


@student_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new student."""
    if not can_manage_students():
        abort(403)
    
    form = StudentForm()
    
    if form.validate_on_submit():
        student = Student(
            student_id=Student.generate_student_id(),
            name=form.name.data,
            email=form.email.data.lower(),
            phone=form.phone.data,
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            address=form.address.data,
            grade_level=form.grade_level.data,
            guardian_name=form.guardian_name.data,
            guardian_phone=form.guardian_phone.data,
            guardian_email=form.guardian_email.data,
            guardian_relationship=form.guardian_relationship.data
        )
        
        db.session.add(student)
        db.session.commit()
        
        flash(f'Student {student.name} has been created.', 'success')
        return redirect(url_for('student.detail', id=student.id))
    
    return render_template('student/create.html', form=form)


@student_bp.route('/<int:id>')
@login_required
def detail(id):
    """View student details."""
    if not can_manage_students():
        abort(403)
    
    student = Student.query.get_or_404(id)
    enrollments = student.enrollments.order_by(Enrollment.enrollment_date.desc()).all()
    
    return render_template('student/detail.html', 
                         student=student,
                         enrollments=enrollments)


@student_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit student details."""
    if not can_manage_students():
        abort(403)
    
    student = Student.query.get_or_404(id)
    form = StudentForm(obj=student)
    
    if form.validate_on_submit():
        form.populate_obj(student)
        student.email = form.email.data.lower()
        db.session.commit()
        
        flash(f'Student {student.name} has been updated.', 'success')
        return redirect(url_for('student.detail', id=student.id))
    
    return render_template('student/edit.html', form=form, student=student)


@student_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a student."""
    if not current_user.is_admin():
        abort(403)
    
    student = Student.query.get_or_404(id)
    name = student.name
    
    db.session.delete(student)
    db.session.commit()
    
    flash(f'Student {name} has been deleted.', 'success')
    return redirect(url_for('student.index'))


@student_bp.route('/<int:id>/enroll', methods=['GET', 'POST'])
@login_required
def enroll(id):
    """Enroll student in a course."""
    if not can_manage_students():
        abort(403)
    
    student = Student.query.get_or_404(id)
    form = EnrollmentForm()
    
    # Get available courses
    enrolled_course_ids = [e.course_id for e in student.enrollments.filter_by(status='active')]
    available_courses = Course.query.filter(
        Course.status == 'active',
        ~Course.id.in_(enrolled_course_ids) if enrolled_course_ids else True
    ).all()
    
    form.course_id.choices = [(c.id, f'{c.code} - {c.name}') for c in available_courses]
    
    if form.validate_on_submit():
        course = Course.query.get(form.course_id.data)
        
        if course.is_full():
            flash('This course is full.', 'error')
            return redirect(url_for('student.enroll', id=student.id))
        
        enrollment = Enrollment(
            student_id=student.id,
            course_id=course.id
        )
        
        db.session.add(enrollment)
        db.session.commit()
        
        flash(f'{student.name} has been enrolled in {course.name}.', 'success')
        return redirect(url_for('student.detail', id=student.id))
    
    return render_template('student/enroll.html', 
                         form=form, 
                         student=student,
                         available_courses=available_courses)
