"""
Planning blueprint.

Handles student planning and task management:
- Creating and managing student plans
- Task scheduling and tracking
- Plan oversight and progress monitoring
"""

from flask import Blueprint

planning_bp = Blueprint('planning', __name__, template_folder='templates')

from . import routes  # noqa: F401, E402
