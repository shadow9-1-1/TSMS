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
from app.models.planning import Plan, Task, PlanStatus, TaskStatus

teacher_bp = Blueprint('teacher', __name__, template_folder='templates')


def teacher_required(f):
    """Decorator to require teacher role or higher (admin/supervisor can also access)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        # Allow admin, supervisor, or users with teacher profile
        if not (current_user.is_admin() or current_user.is_supervisor() or current_user.teacher_profile):
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
        # Get students assigned to this teacher
        assigned_students = Student.query.filter_by(assigned_teacher_id=teacher.id).all()
        student_ids = [s.id for s in assigned_students]
    else:
        # Supervisor viewing teacher section
        courses = []
        student_count = 0
        student_ids = []
    
    # Planning stats for teacher
    if student_ids:
        plans_query = Plan.query.filter(Plan.student_id.in_(student_ids))
        active_plans = plans_query.filter(Plan.status == PlanStatus.ACTIVE).count()
        total_plans = plans_query.count()
        
        # Get tasks for these plans
        plan_ids = [p.id for p in plans_query.all()]
        if plan_ids:
            pending_tasks = Task.query.filter(
                Task.plan_id.in_(plan_ids),
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
            ).count()
            overdue_tasks = Task.query.filter(
                Task.plan_id.in_(plan_ids),
                Task.status == TaskStatus.OVERDUE
            ).count()
        else:
            pending_tasks = 0
            overdue_tasks = 0
    else:
        active_plans = 0
        total_plans = 0
        pending_tasks = 0
        overdue_tasks = 0
    
    planning_stats = {
        'active_plans': active_plans,
        'total_plans': total_plans,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks
    }
    
    return render_template('teacher/index.html', 
                         teacher=teacher,
                         courses=courses,
                         student_count=student_count,
                         planning_stats=planning_stats)


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


@teacher_bp.route('/planning')
@login_required
@teacher_required
def planning():
    """Teacher planning dashboard - view and manage student plans."""
    teacher = current_user.teacher_profile
    
    if teacher:
        # Get students assigned to this teacher
        students = Student.query.filter_by(assigned_teacher_id=teacher.id).all()
        student_ids = [s.id for s in students]
    else:
        # Admin/supervisor viewing - show all students
        students = Student.query.all()
        student_ids = [s.id for s in students]
    
    # Get plans for these students
    if student_ids:
        plans = Plan.query.filter(
            Plan.student_id.in_(student_ids)
        ).order_by(Plan.created_at.desc()).all()
    else:
        plans = []
    
    # Calculate student progress data
    students_with_progress = []
    for student in students:
        student_plans = [p for p in plans if p.student_id == student.id]
        active_plan = next((p for p in student_plans if p.status == PlanStatus.ACTIVE), None)
        
        # Calculate overall progress
        if student_plans:
            total_progress = sum(p.progress_percentage or 0 for p in student_plans)
            overall_progress = total_progress // len(student_plans)
        else:
            overall_progress = 0
        
        # Count tasks
        total_tasks = 0
        completed_tasks = 0
        for plan in student_plans:
            tasks = plan.tasks.all()
            total_tasks += len(tasks)
            completed_tasks += sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        
        students_with_progress.append({
            'student': student,
            'active_plan': active_plan,
            'total_plans': len(student_plans),
            'overall_progress': overall_progress,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks
        })
    
    # Stats
    stats = {
        'total_students': len(students),
        'total_plans': len(plans),
        'active_plans': sum(1 for p in plans if p.status == PlanStatus.ACTIVE),
        'completed_plans': sum(1 for p in plans if p.status == PlanStatus.COMPLETED)
    }
    
    return render_template('teacher/planning.html',
                         students_with_progress=students_with_progress,
                         plans=plans,
                         stats=stats)


@teacher_bp.route('/student-progress')
@login_required
@teacher_required
def student_progress():
    """View all students with their progress bars."""
    teacher = current_user.teacher_profile
    
    if teacher:
        students = Student.query.filter_by(assigned_teacher_id=teacher.id).all()
    else:
        students = Student.query.all()
    
    # Calculate progress for each student
    students_data = []
    for student in students:
        plans = Plan.query.filter_by(student_id=student.id).all()
        active_plan = next((p for p in plans if p.status == PlanStatus.ACTIVE), None)
        
        total_tasks = 0
        completed_tasks = 0
        pending_tasks = 0
        overdue_tasks = 0
        
        for plan in plans:
            for task in plan.tasks.all():
                total_tasks += 1
                if task.status == TaskStatus.COMPLETED:
                    completed_tasks += 1
                elif task.status == TaskStatus.OVERDUE:
                    overdue_tasks += 1
                elif task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                    pending_tasks += 1
        
        # Calculate overall progress percentage
        if total_tasks > 0:
            progress_percentage = int((completed_tasks / total_tasks) * 100)
        else:
            progress_percentage = 0
        
        students_data.append({
            'student': student,
            'active_plan': active_plan,
            'total_plans': len(plans),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'overdue_tasks': overdue_tasks,
            'progress_percentage': progress_percentage
        })
    
    return render_template('teacher/student_progress.html',
                         students_data=students_data)


# Import admin management routes (CRUD operations for teachers)
from app.blueprints.teacher import routes  # noqa: F401, E402
