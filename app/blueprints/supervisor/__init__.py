"""
Supervisor blueprint.

Handles supervisor-specific functions including:
- Supervisor dashboard
- Viewing assigned students
- Plan oversight
- Student supervision management
"""

from flask import Blueprint

supervisor_bp = Blueprint('supervisor', __name__, template_folder='templates')

from . import routes  # noqa: F401, E402
