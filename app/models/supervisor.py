"""
Supervisor model for managing supervisor profiles.

Supervisors are linked to User accounts and can oversee teachers and students.
"""

from datetime import datetime
from app.extensions import db
from app.models.user import UserRole


class Supervisor(db.Model):
    """
    Supervisor profile model.
    
    Stores supervisor-specific information linked to a User account.
    Supervisors can oversee teachers and students.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User
        department: Department the supervisor oversees
    """
    __tablename__ = 'supervisors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, 
        db.ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False, 
        unique=True,
        index=True
    )
    department = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Supervisor {self.user.name if self.user else "Unknown"}>'
    
    @property
    def name(self):
        """Get supervisor's name from user profile."""
        return self.user.name if self.user else None
    
    @property
    def email(self):
        """Get supervisor's email from user profile."""
        return self.user.email if self.user else None
    
    def to_dict(self):
        """Convert supervisor to dictionary representation."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'department': self.department,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def create_supervisor(user, department=None, phone=None):
        """
        Create a supervisor profile for a user.
        
        Args:
            user: User instance (must have Supervisor role)
            department: Department name
            phone: Contact phone
            
        Returns:
            Supervisor: New supervisor instance
        """
        if user.role != UserRole.SUPERVISOR:
            raise ValueError("User must have Supervisor role")
        
        supervisor = Supervisor(
            user_id=user.id,
            department=department,
            phone=phone
        )
        db.session.add(supervisor)
        db.session.commit()
        return supervisor
