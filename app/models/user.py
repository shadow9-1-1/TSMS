"""
User model for authentication and authorization.

Implements role-based access control (RBAC) with enum-based roles:
- Admin: Full system access
- Supervisor: Manage teachers and view reports
- Teacher: Manage own students and courses

Features:
- Password hashing with Werkzeug
- Role checking methods
- Status management
- Flask-Login integration
"""

from datetime import datetime
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from app.extensions import db


class UserRole(Enum):
    """Enumeration for user roles."""
    ADMIN = 'admin'
    SUPERVISOR = 'supervisor'
    TEACHER = 'teacher'


class UserStatus(Enum):
    """Enumeration for user account status."""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    SUSPENDED = 'suspended'
    PENDING = 'pending'


class User(UserMixin, db.Model):
    """
    User model for authentication and authorization.
    
    Handles user accounts with role-based access control.
    Linked to Teacher or Supervisor profiles based on role.
    
    Attributes:
        id: Primary key
        name: Full name of the user
        username: Unique username for login
        email: Unique email address
        password_hash: Hashed password (never store plain text)
        role: User role (admin, supervisor, teacher)
        status: Account status (active, inactive, suspended, pending)
        created_at: Timestamp of account creation
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.TEACHER)
    status = db.Column(db.Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime)
    
    # Relationships
    teacher_profile = db.relationship(
        'Teacher', 
        backref='user', 
        uselist=False, 
        cascade='all, delete-orphan',
        lazy='joined'
    )
    supervisor_profile = db.relationship(
        'Supervisor', 
        backref='user', 
        uselist=False, 
        cascade='all, delete-orphan',
        lazy='joined'
    )
    
    def __repr__(self):
        return f'<User {self.username} ({self.role.value})>'
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.status is None:
            self.status = UserStatus.ACTIVE
    
    # Password handling
    @property
    def password(self):
        """Prevent password from being read."""
        raise AttributeError('Password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        """Hash password on setting."""
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        """Verify a password against the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """Set a new password (alternative to property setter)."""
        self.password_hash = generate_password_hash(password)
    
    # Role checking methods
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN
    
    def is_supervisor(self):
        """Check if user has supervisor role."""
        return self.role == UserRole.SUPERVISOR
    
    def is_teacher(self):
        """Check if user has teacher role."""
        return self.role == UserRole.TEACHER
    
    def has_role(self, role_name):
        """Check if user has a specific role."""
        if isinstance(role_name, str):
            return self.role.value == role_name.lower()
        elif isinstance(role_name, UserRole):
            return self.role == role_name
        return False
    
    def can_manage_teachers(self):
        """Check if user can manage teachers (admin or supervisor)."""
        return self.role in (UserRole.ADMIN, UserRole.SUPERVISOR)
    
    def can_manage_students(self):
        """Check if user can manage students (any authenticated role)."""
        return self.role in (UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.TEACHER)
    
    def can_manage_users(self):
        """Check if user can manage other users (admin only)."""
        return self.role == UserRole.ADMIN
    
    # Status checking methods
    def is_active_account(self):
        """Check if account is active."""
        return self.status == UserStatus.ACTIVE
    
    def activate(self):
        """Activate user account."""
        self.status = UserStatus.ACTIVE
    
    def deactivate(self):
        """Deactivate user account."""
        self.status = UserStatus.INACTIVE
    
    def suspend(self):
        """Suspend user account."""
        self.status = UserStatus.SUSPENDED
    
    # Utility methods
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary representation."""
        data = {
            'id': self.id,
            'name': self.name,
            'username': self.username,
            'role': self.role.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_sensitive:
            data['email'] = self.email
            data['last_login_at'] = self.last_login_at.isoformat() if self.last_login_at else None
        return data
    
    @staticmethod
    def create_user(name, username, email, password, role=UserRole.TEACHER):
        """Factory method to create a new user."""
        user = User(
            name=name,
            username=username.lower(),
            email=email.lower(),
            role=role
        )
        user.password = password
        return user
    
    @staticmethod
    def create_admin(name, username, email, password):
        """Create an admin user."""
        user = User.create_user(name, username, email, password, UserRole.ADMIN)
        user.status = UserStatus.ACTIVE
        db.session.add(user)
        db.session.commit()
        return user
