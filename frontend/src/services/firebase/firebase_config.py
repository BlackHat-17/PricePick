import firebase_admin
from firebase_admin import credentials, auth

# Path to your service account key
cred = credentials.Certificate("app/firebase/serviceAccountKey.json")

# Initialize only once
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
