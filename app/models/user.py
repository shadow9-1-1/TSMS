"""
User and Role models for authentication and authorization.

Implements role-based access control (RBAC) with three roles:
- Admin: Full system access
- Supervisor: Manage teachers and view reports
- Teacher: Manage own students and courses
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from app.extensions import db


class Role(db.Model):
    """
    Role model for RBAC.
    
    Defines system roles and their permissions.
    """
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.String(256))
    permissions = db.Column(db.Integer, default=0)
    is_default = db.Column(db.Boolean, default=False, index=True)
    
    # Relationships
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    # Permission constants
    PERMISSION_VIEW = 1
    PERMISSION_EDIT = 2
    PERMISSION_CREATE = 4
    PERMISSION_DELETE = 8
    PERMISSION_MANAGE_USERS = 16
    PERMISSION_ADMIN = 32
    
    def __repr__(self):
        return f'<Role {self.name}>'
    
    def has_permission(self, permission):
        """Check if role has a specific permission."""
        return self.permissions & permission == permission
    
    def add_permission(self, permission):
        """Add a permission to the role."""
        if not self.has_permission(permission):
            self.permissions += permission
    
    def remove_permission(self, permission):
        """Remove a permission from the role."""
        if self.has_permission(permission):
            self.permissions -= permission
    
    def reset_permissions(self):
        """Reset all permissions."""
        self.permissions = 0
    
    @staticmethod
    def insert_roles():
        """Insert default roles into the database."""
        roles = {
            'Teacher': [
                Role.PERMISSION_VIEW,
                Role.PERMISSION_EDIT,
                Role.PERMISSION_CREATE
            ],
            'Supervisor': [
                Role.PERMISSION_VIEW,
                Role.PERMISSION_EDIT,
                Role.PERMISSION_CREATE,
                Role.PERMISSION_DELETE,
                Role.PERMISSION_MANAGE_USERS
            ],
            'Admin': [
                Role.PERMISSION_VIEW,
                Role.PERMISSION_EDIT,
                Role.PERMISSION_CREATE,
                Role.PERMISSION_DELETE,
                Role.PERMISSION_MANAGE_USERS,
                Role.PERMISSION_ADMIN
            ]
        }
        
        default_role = 'Teacher'
        
        for role_name, permissions in roles.items():
            role = Role.query.filter_by(name=role_name).first()
            if role is None:
                role = Role(name=role_name)
            role.reset_permissions()
            for perm in permissions:
                role.add_permission(perm)
            role.is_default = (role_name == default_role)
            db.session.add(role)
        
        db.session.commit()


class User(UserMixin, db.Model):
    """
    User model for authentication.
    
    Extends UserMixin for Flask-Login integration.
    Handles password hashing and role-based permissions.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20))
    avatar_url = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    
    # Foreign keys
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    
    # Relationships
    teacher_profile = db.relationship('Teacher', backref='user', uselist=False, 
                                       cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        # Assign default role if none specified
        if self.role is None:
            self.role = Role.query.filter_by(is_default=True).first()
    
    @property
    def password(self):
        """Prevent password from being read."""
        raise AttributeError('Password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        """Hash password on setting."""
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        """Verify password against hash."""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Return user's full name."""
        return f'{self.first_name} {self.last_name}'
    
    def can(self, permission):
        """Check if user has a specific permission."""
        return self.role is not None and self.role.has_permission(permission)
    
    def is_admin(self):
        """Check if user is an admin."""
        return self.can(Role.PERMISSION_ADMIN)
    
    def is_supervisor(self):
        """Check if user is a supervisor or higher."""
        return self.can(Role.PERMISSION_MANAGE_USERS)
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login_at = datetime.utcnow()
        db.session.commit()
    
    @staticmethod
    def create_admin(email, username, password, first_name, last_name):
        """Create an admin user."""
        admin_role = Role.query.filter_by(name='Admin').first()
        if admin_role is None:
            Role.insert_roles()
            admin_role = Role.query.filter_by(name='Admin').first()
        
        user = User(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name,
            role=admin_role,
            is_verified=True
        )
        user.password = password
        db.session.add(user)
        db.session.commit()
        return user
