"""
Authentication service for user authentication and authorization
"""

from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import logging
import jwt
from fastapi import HTTPException, status

from app.models.user import User
from app.services.user_service import UserService
from config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """
    Service class for authentication and authorization
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username/email and password
        """
        try:
            # Try to find user by username or email
            user = await self.user_service.get_user_by_username(username)
            if not user:
                user = await self.user_service.get_user_by_email(username)
            
            if not user:
                return None
            
            # Check if account is locked
            if user.is_locked:
                logger.warning(f"Login attempt for locked account: {username}")
                return None
            
            # Verify password
            if not await self.user_service.verify_user_password(user, password):
                # Increment failed login attempts
                user.failed_login_attempts += 1
                
                # Lock account after 5 failed attempts
                if user.failed_login_attempts >= 5:
                    user.lock_account()
                    logger.warning(f"Account locked due to failed login attempts: {username}")
                
                self.db.commit()
                return None
            
            # Reset failed login attempts on successful login
            if user.failed_login_attempts > 0:
                user.unlock_account()
                self.db.commit()
            
            return user
            
        except Exception as e:
            logger.error(f"Authentication failed for {username}: {str(e)}")
            return None
    
    async def create_access_token(self, user_id: int) -> str:
        """
        Create JWT access token for user
        """
        try:
            # Token payload
            payload = {
                "user_id": user_id,
                "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
                "iat": datetime.utcnow(),
                "type": "access"
            }
            
            # Create token
            token = jwt.encode(
                payload,
                settings.SECRET_KEY,
                algorithm=settings.ALGORITHM
            )
            
            return token
            
        except Exception as e:
            logger.error(f"Failed to create access token for user {user_id}: {str(e)}")
            raise
    
    async def verify_access_token(self, token: str) -> Optional[dict]:
        """
        Verify and decode JWT access token
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Check token type
            if payload.get("type") != "access":
                return None
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Access token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid access token")
            return None
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            return None
    
    async def get_current_user(self, token: str) -> Optional[User]:
        """
        Get current user from access token
        """
        try:
            # Verify token
            payload = await self.verify_access_token(token)
            if not payload:
                return None
            
            # Get user
            user_id = payload.get("user_id")
            if not user_id:
                return None
            
            user = await self.user_service.get_user(user_id)
            if not user or not user.is_active:
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Failed to get current user: {str(e)}")
            return None
    
    async def refresh_access_token(self, token: str) -> Optional[str]:
        """
        Refresh access token
        """
        try:
            # Verify current token
            payload = await self.verify_access_token(token)
            if not payload:
                return None
            
            # Create new token
            user_id = payload.get("user_id")
            if not user_id:
                return None
            
            return await self.create_access_token(user_id)
            
        except Exception as e:
            logger.error(f"Failed to refresh access token: {str(e)}")
            return None
    
    async def revoke_token(self, token: str) -> bool:
        """
        Revoke access token (add to blacklist)
        """
        try:
            # In a production system, you would add the token to a blacklist
            # stored in Redis or database
            
            # For now, we'll just return True
            # The token will naturally expire based on its expiration time
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke token: {str(e)}")
            return False
    
    async def update_last_login(self, user_id: int) -> bool:
        """
        Update user's last login time
        """
        try:
            return await self.user_service.update_last_login(user_id)
        except Exception as e:
            logger.error(f"Failed to update last login for user {user_id}: {str(e)}")
            return False
    
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Change user password
        """
        try:
            # Get user
            user = await self.user_service.get_user(user_id)
            if not user:
                return False
            
            # Verify old password
            if not await self.user_service.verify_user_password(user, old_password):
                return False
            
            # Update password
            hashed_password = self.user_service._hash_password(new_password)
            user.hashed_password = hashed_password
            
            self.db.commit()
            
            logger.info(f"Password changed for user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to change password for user {user_id}: {str(e)}")
            return False
    
    async def reset_password(self, email: str) -> bool:
        """
        Initiate password reset process
        """
        try:
            # Get user by email
            user = await self.user_service.get_user_by_email(email)
            if not user:
                # Don't reveal if email exists or not
                return True
            
            # Generate reset token
            reset_token = self._generate_reset_token(user.id)
            
            # In a real implementation, you would:
            # 1. Store reset token in database with expiration
            # 2. Send reset email with token
            # 3. User clicks link with token to reset password
            
            logger.info(f"Password reset initiated for user {user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset password for email {email}: {str(e)}")
            return False
    
    def _generate_reset_token(self, user_id: int) -> str:
        """
        Generate password reset token
        """
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(hours=1),  # 1 hour expiration
            "iat": datetime.utcnow(),
            "type": "password_reset"
        }
        
        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
    
    async def verify_reset_token(self, token: str) -> Optional[int]:
        """
        Verify password reset token and return user ID
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Check token type
            if payload.get("type") != "password_reset":
                return None
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                return None
            
            return payload.get("user_id")
            
        except jwt.ExpiredSignatureError:
            logger.warning("Password reset token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid password reset token")
            return None
        except Exception as e:
            logger.error(f"Reset token verification failed: {str(e)}")
            return None
