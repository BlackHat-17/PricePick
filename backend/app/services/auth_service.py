from fastapi import HTTPException
from firebase_admin import auth as firebase_auth
import logging

logger = logging.getLogger(__name__)

class AuthService:
    async def verify_firebase_token(self, id_token: str):
        """
        Verify Firebase ID Token from frontend
        """
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            return decoded_token  # contains uid, email, name, etc.
        except firebase_auth.ExpiredIdTokenError:
            raise HTTPException(status_code=401, detail="Token expired")
        except firebase_auth.InvalidIdTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid Firebase token")
