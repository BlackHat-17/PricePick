"""
User service for managing user accounts and authentication
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import hashlib
import secrets

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)


class UserService:
    """
    Service class for user-related operations
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user account
        """
        try:
            # Hash password
            hashed_password = self._hash_password(user_data.password)
            
            # Generate API key
            api_key = self._generate_api_key()
            
            # Create user
            user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                phone=user_data.phone,
                api_key=api_key,
                preferences=user_data.preferences or {}
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Created user: {user.id} - {user.username}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create user: {str(e)}")
            raise
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """
        Get a user by ID
        """
        try:
            return self.db.query(User).filter(
                and_(User.id == user_id, User.is_active == True)
            ).first()
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {str(e)}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email
        """
        try:
            return self.db.query(User).filter(
                and_(User.email == email, User.is_active == True)
            ).first()
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {str(e)}")
            raise
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username
        """
        try:
            return self.db.query(User).filter(
                and_(User.username == username, User.is_active == True)
            ).first()
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {str(e)}")
            raise
    
    async def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """
        Get a user by API key
        """
        try:
            return self.db.query(User).filter(
                and_(User.api_key == api_key, User.is_active == True)
            ).first()
        except Exception as e:
            logger.error(f"Failed to get user by API key: {str(e)}")
            raise
    
    async def list_users(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[User]:
        """
        List users with filtering and pagination
        """
        try:
            query = self.db.query(User).filter(User.is_active == True)
            
            # Apply filters
            if filters:
                if filters.get("is_active") is not None:
                    query = query.filter(User.is_active == filters["is_active"])
                
                if filters.get("is_premium") is not None:
                    query = query.filter(User.is_premium == filters["is_premium"])
                
                if filters.get("search"):
                    search_term = f"%{filters['search']}%"
                    query = query.filter(
                        or_(
                            User.username.ilike(search_term),
                            User.email.ilike(search_term),
                            User.first_name.ilike(search_term),
                            User.last_name.ilike(search_term)
                        )
                    )
            
            return query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Failed to list users: {str(e)}")
            raise
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """
        Update a user
        """
        try:
            user = await self.get_user(user_id)
            if not user:
                return None
            
            # Update fields
            update_data = user_data.dict(exclude_unset=True)
            
            # Handle password update
            if "password" in update_data:
                update_data["hashed_password"] = self._hash_password(update_data.pop("password"))
            
            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"Updated user: {user.id} - {user.username}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user {user_id}: {str(e)}")
            raise
    
    async def delete_user(self, user_id: int) -> bool:
        """
        Soft delete a user
        """
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            
            user.is_active = False
            self.db.commit()
            
            logger.info(f"Deleted user: {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete user {user_id}: {str(e)}")
            raise
    
    async def update_user_status(self, user_id: int, is_active: bool) -> bool:
        """
        Update user active status
        """
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            
            user.is_active = is_active
            self.db.commit()
            
            logger.info(f"Updated user status {user_id}: {is_active}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user status {user_id}: {str(e)}")
            raise
    
    async def update_last_login(self, user_id: int) -> bool:
        """
        Update user's last login time
        """
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            
            user.last_login = datetime.utcnow()
            user.login_count += 1
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update last login for user {user_id}: {str(e)}")
            raise
    
    async def increment_api_usage(self, user_id: int) -> bool:
        """
        Increment user's API usage count
        """
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            
            user.increment_api_usage()
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to increment API usage for user {user_id}: {str(e)}")
            raise
    
    async def reset_api_usage(self, user_id: int) -> bool:
        """
        Reset user's API usage count
        """
        try:
            user = await self.get_user(user_id)
            if not user:
                return False
            
            user.reset_api_usage()
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to reset API usage for user {user_id}: {str(e)}")
            raise
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """
        Get user statistics
        """
        try:
            # Total users
            total_users = self.db.query(User).count()
            active_users = self.db.query(User).filter(User.is_active == True).count()
            premium_users = self.db.query(User).filter(User.is_premium == True).count()
            
            # Recent registrations
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_registrations = self.db.query(User).filter(
                User.created_at >= week_ago
            ).count()
            
            # Users with API access
            api_users = self.db.query(User).filter(
                User.api_key.isnot(None)
            ).count()
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": total_users - active_users,
                "premium_users": premium_users,
                "recent_registrations": recent_registrations,
                "api_users": api_users
            }
            
        except Exception as e:
            logger.error(f"Failed to get user stats: {str(e)}")
            return {}
    
    def _hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt
        """
        import bcrypt
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        """
        import bcrypt
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def _generate_api_key(self) -> str:
        """
        Generate a secure API key
        """
        return secrets.token_urlsafe(32)
    
    async def verify_user_password(self, user: User, password: str) -> bool:
        """
        Verify user password
        """
        try:
            return self._verify_password(password, user.hashed_password)
        except Exception as e:
            logger.error(f"Failed to verify password for user {user.id}: {str(e)}")
            return False
