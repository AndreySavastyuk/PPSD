import os
import bcrypt
from sqlalchemy.orm import Session
from models.models import User

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify if the provided password matches the stored hashed password.
    
    Args:
        plain_password (str): Plain text password to verify
        hashed_password (str): Hashed password from the database
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def authenticate_user(db: Session, username: str, password: str) -> User:
    """
    Authenticate a user with username and password.
    
    Args:
        db (Session): Database session
        username (str): Username to authenticate
        password (str): Password to verify
        
    Returns:
        User: User object if authentication successful, None otherwise
    """
    user = db.query(User).filter(User.username == username).first()
    
    if not user or not verify_password(password, user.password_hash):
        return None
    
    if not user.is_active:
        return None
    
    return user

def get_current_user(db: Session, username: str) -> User:
    """
    Get the current user from the database.
    
    Args:
        db (Session): Database session
        username (str): Username to look up
        
    Returns:
        User: User object if found, None otherwise
    """
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, password: str, full_name: str, role: str, 
                can_edit: bool = False, can_view: bool = True, can_delete: bool = False, 
                can_admin: bool = False, telegram_id: str = None) -> User:
    """
    Create a new user in the database.
    
    Args:
        db (Session): Database session
        username (str): Username for the new user
        password (str): Password for the new user
        full_name (str): Full name of the user
        role (str): Role of the user (admin, warehouse, qc, lab)
        can_edit (bool): Whether the user can edit records
        can_view (bool): Whether the user can view records
        can_delete (bool): Whether the user can delete records
        can_admin (bool): Whether the user has admin privileges
        telegram_id (str): Telegram ID for notifications
        
    Returns:
        User: Created user object
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        return None
    
    # Hash the password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create new user
    new_user = User(
        username=username,
        password_hash=password_hash,
        full_name=full_name,
        role=role,
        can_edit=can_edit,
        can_view=can_view,
        can_delete=can_delete,
        can_admin=can_admin,
        telegram_id=telegram_id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

def update_user(db: Session, user_id: int, **kwargs) -> User:
    """
    Update a user in the database.
    
    Args:
        db (Session): Database session
        user_id (int): ID of the user to update
        **kwargs: Fields to update
        
    Returns:
        User: Updated user object
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    # Update password if provided
    if 'password' in kwargs:
        password_hash = bcrypt.hashpw(kwargs['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        kwargs['password_hash'] = password_hash
        del kwargs['password']
    
    # Update user fields
    for key, value in kwargs.items():
        if hasattr(user, key):
            setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    
    return user 