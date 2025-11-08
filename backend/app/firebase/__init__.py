# backend/firebase/__init__.py
import firebase_admin
from firebase_admin import credentials, firestore
import os

# Path to your Firebase service account
FIREBASE_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    "firebase_config.json"
)

# Initialize the app only once
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CONFIG_PATH)
    firebase_admin.initialize_app(cred)

# Export Firestore client for other modules
db = firestore.client()
