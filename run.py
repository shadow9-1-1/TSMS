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
from app.models.user import User, Role
from app.models.teacher import Teacher
from app.models.student import Student
from app.models.course import Course, Enrollment

# Create application instance
app = create_app(os.getenv('FLASK_CONFIG', 'development'))


@app.cli.command('init-db')
def init_db():
    """Initialize the database with tables and default roles."""
    click.echo('Creating database tables...')
    db.create_all()
    click.echo('Tables created.')
    
    click.echo('Inserting default roles...')
    Role.insert_roles()
    click.echo('Roles inserted.')
    
    click.echo('Database initialization complete!')


@app.cli.command('create-admin')
@click.option('--email', prompt=True, help='Admin email address')
@click.option('--username', prompt=True, help='Admin username')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Admin password')
@click.option('--first-name', prompt='First name', help='Admin first name')
@click.option('--last-name', prompt='Last name', help='Admin last name')
def create_admin(email, username, password, first_name, last_name):
    """Create an admin user."""
    # Check if user already exists
    if User.query.filter_by(email=email.lower()).first():
        click.echo(f'Error: User with email {email} already exists.')
        return
    
    if User.query.filter_by(username=username.lower()).first():
        click.echo(f'Error: User with username {username} already exists.')
        return
    
    # Ensure roles exist
    if not Role.query.first():
        Role.insert_roles()
    
    # Create admin user
    user = User.create_admin(
        email=email.lower(),
        username=username.lower(),
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    
    click.echo(f'Admin user "{username}" created successfully!')


@app.cli.command('seed-demo')
def seed_demo():
    """Seed the database with demo data for development."""
    click.echo('Seeding demo data...')
    
    # Ensure roles exist
    if not Role.query.first():
        Role.insert_roles()
    
    # Create demo admin if not exists
    if not User.query.filter_by(email='admin@tsms.local').first():
        User.create_admin(
            email='admin@tsms.local',
            username='admin',
            password='Admin123!',
            first_name='System',
            last_name='Administrator'
        )
        click.echo('Demo admin created: admin@tsms.local / Admin123!')
    
    # Create demo teacher
    teacher_role = Role.query.filter_by(name='Teacher').first()
    if not User.query.filter_by(email='teacher@tsms.local').first():
        teacher_user = User(
            email='teacher@tsms.local',
            username='teacher',
            first_name='John',
            last_name='Smith',
            role=teacher_role,
            is_verified=True
        )
        teacher_user.password = 'Teacher123!'
        db.session.add(teacher_user)
        db.session.commit()
        
        teacher = Teacher(
            employee_id=Teacher.generate_employee_id(),
            user_id=teacher_user.id,
            department='Mathematics',
            specialization='Algebra',
            qualification='M.Sc Mathematics',
            experience_years=5
        )
        db.session.add(teacher)
        db.session.commit()
        click.echo('Demo teacher created: teacher@tsms.local / Teacher123!')
    
    # Create demo students
    for i in range(1, 6):
        if not Student.query.filter_by(email=f'student{i}@tsms.local').first():
            student = Student(
                student_id=Student.generate_student_id(),
                first_name=f'Student',
                last_name=f'Demo{i}',
                email=f'student{i}@tsms.local',
                grade_level='Grade 10'
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
