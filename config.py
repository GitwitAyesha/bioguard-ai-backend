import os
import json
import tempfile
import firebase_admin
from firebase_admin import credentials, db

def initialize_firebase():
    if firebase_admin._apps:
        return  # Already initialized

    firebase_key_json = os.environ.get("FIREBASE_KEY_JSON")

    if firebase_key_json:
        # Production (Render): key is stored as environment variable
        key_dict = json.loads(firebase_key_json)
        cred = credentials.Certificate(key_dict)
    else:
        # Local development: key is a file
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        cred_path = os.path.join(BASE_DIR, "firebase_key.json")
        cred = credentials.Certificate(cred_path)

    firebase_admin.initialize_app(cred, {
        "databaseURL": os.environ.get(
            "FIREBASE_DB_URL",
            "https://bioguard-ai-949a4-default-rtdb.firebaseio.com/"
        )
    })

initialize_firebase()

def get_db():
    return db