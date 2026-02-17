"""
Application entry point.

This script creates and runs the Flask application.
It handles loading environment variables and provides
CLI commands for database management.

Usage:
    Development: python run.py
    Production:  gunicorn -w 4 -b 0.0.0.0:8000 "run:app"
"""

import os
import click
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app import create_app
from app.extensions import db
from app.models import User, UserRole, UserStatus
from app.models.teacher import Teacher
from app.models.student import Student, StudentStatus
from app.models.course import Course, Enrollment

# Create application instance
app = create_app(os.getenv('FLASK_CONFIG', 'development'))


@app.cli.command('init-db')
def init_db():
    """Initialize the database with tables."""
    click.echo('Creating database tables...')
    db.create_all()
    click.echo('Tables created.')
    click.echo('Database initialization complete!')


@app.cli.command('create-admin')
@click.option('--email', prompt=True, help='Admin email address')
@click.option('--username', prompt=True, help='Admin username')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Admin password')
@click.option('--name', prompt='Full name', help='Admin full name')
def create_admin(email, username, password, name):
    """Create an admin user."""
    # Check if user already exists
    if User.query.filter_by(email=email.lower()).first():
        click.echo(f'Error: User with email {email} already exists.')
        return
    
    if User.query.filter_by(username=username.lower()).first():
        click.echo(f'Error: User with username {username} already exists.')
        return
    
    # Create admin user
    user = User.create_admin(
        name=name,
        username=username.lower(),
        email=email.lower(),
        password=password
    )
    
    click.echo(f'Admin user "{username}" created successfully!')


@app.cli.command('seed-demo')
def seed_demo():
    """Seed the database with demo data for development."""
    click.echo('Seeding demo data...')
    
    # Create demo admin if not exists
    if not User.query.filter_by(email='admin@tsms.com').first():
        User.create_admin(
            name='System Administrator',
            username='admin',
            email='admin@tsms.com',
            password='Admin123!'
        )
        click.echo('Demo admin created: admin@tsms.com / Admin123!')
    
    # Create demo teacher
    if not User.query.filter_by(email='teacher@tsms.com').first():
        teacher_user = User(
            name='John Smith',
            email='teacher@tsms.com',
            username='teacher',
            role=UserRole.TEACHER,
            status=UserStatus.ACTIVE
        )
        teacher_user.password = 'Teacher123!'
        db.session.add(teacher_user)
        db.session.commit()
        
        teacher = Teacher(
            employee_id=Teacher.generate_employee_id(),
            user_id=teacher_user.id,
            department='Mathematics',
            specialization='Algebra',
            phone='555-0101'
        )
        db.session.add(teacher)
        db.session.commit()
        click.echo('Demo teacher created: teacher@tsms.com / Teacher123!')
    
    # Create demo students
    teacher = Teacher.query.first()
    for i in range(1, 6):
        if not Student.query.filter_by(email=f'student{i}@tsms.com').first():
            student = Student(
                student_id=Student.generate_student_id(),
                name=f'Student Demo{i}',
                email=f'student{i}@tsms.com',
                phone=f'555-010{i}',
                status=StudentStatus.ACTIVE,
                assigned_teacher_id=teacher.id if teacher else None
            )
            db.session.add(student)
    
    db.session.commit()
    click.echo('Demo students created.')
    
    # Create demo course
    teacher = Teacher.query.first()
    if teacher and not Course.query.filter_by(code='MATH101').first():
        course = Course(
            code='MATH101',
            name='Introduction to Mathematics',
            description='A foundational mathematics course covering basic algebra and geometry.',
            credits=3,
            teacher_id=teacher.id,
            schedule='Mon, Wed, Fri 9:00-10:30',
            room='Room 101',
            semester='Fall',
            academic_year='2025-2026'
        )
        db.session.add(course)
        db.session.commit()
        click.echo('Demo course created.')
    
    click.echo('Demo data seeding complete!')


@app.cli.command('drop-all')
@click.confirmation_option(prompt='Are you sure you want to drop all tables?')
def drop_all():
    """Drop all database tables."""
    db.drop_all()
    click.echo('All tables dropped.')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
