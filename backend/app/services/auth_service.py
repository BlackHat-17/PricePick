from firebase_admin import auth as firebase_auth

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)

    async def verify_firebase_token(self, id_token: str):
        """
        Verify Firebase ID Token sent from frontend
        """
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            uid = decoded_token["uid"]
            return decoded_token
        except firebase_auth.ExpiredIdTokenError:
            raise HTTPException(status_code=401, detail="Token expired")
        except firebase_auth.InvalidIdTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")
