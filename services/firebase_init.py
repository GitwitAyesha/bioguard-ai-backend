import firebase_admin
from firebase_admin import db

# Load Firebase key
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)

# Initialize Firestore DB
db = firestore.client()
