from config import get_db
import uuid
import datetime

db = get_db()

def create_user(name, email, password_hash, face_encoding):
    user_id = str(uuid.uuid4())
    db.reference(f"users/{user_id}").set({
        "id": user_id,
        "name": name,
        "email": email,
        "password": password_hash,
        "role": "user",
        "face_encoding": face_encoding.tolist(),  # store as list
        "failed_attempts": 0,
        "created_at": str(datetime.datetime.utcnow())
    })
    return user_id

def get_user_by_email(email):
    users_ref = db.reference("users")
    all_users = users_ref.get()
    if all_users:
        for user_id, user in all_users.items():
            if user.get("email") == email:
                user["id"] = user_id
                return user
    return None

def get_user_by_id(user_id):
    user_ref = db.reference(f"users/{user_id}")
    return user_ref.get()
