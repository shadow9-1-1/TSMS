"""
Student blueprint.

Handles student management including CRUD operations,
teacher assignment, and role-based access control.
"""

from flask import Blueprint

student_bp = Blueprint('student', __name__, template_folder='templates')

# Import routes to register them with the blueprint
from app.blueprints.student import routes  # noqa: F401, E402
