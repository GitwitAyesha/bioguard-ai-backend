from config import get_db
from utils.security import hash_password, verify_password
from services.otp_service import generate_otp
from services.log_service import log_event
import uuid
import base64
import numpy as np
from io import BytesIO
from PIL import Image
import tempfile
import os
import traceback

db = get_db()


def clean_base64(base64_string):
    if not base64_string:
        return None
    if "," in base64_string:
        return base64_string.split(",")[1]
    return base64_string


def get_embedding(face_base64):
    tmp_path = None
    try:
        from deepface import DeepFace
        face_base64 = clean_base64(face_base64)
        image_data  = base64.b64decode(face_base64)
        image       = Image.open(BytesIO(image_data)).convert("RGB")
        tmp         = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        image.save(tmp.name, format="JPEG")
        tmp.close()
        tmp_path = tmp.name
        result = DeepFace.represent(
            img_path          = tmp_path,
            model_name        = "Facenet",
            enforce_detection = False,
        )
        if result and len(result) > 0:
            return result[0]["embedding"]
        return None
    except Exception:
        traceback.print_exc()
        return None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def faces_match(embedding1, embedding2, threshold=10.0):
    a = np.array(embedding1)
    b = np.array(embedding2)
    distance = float(np.linalg.norm(a - b))
    print(f"[FACE] Distance: {distance:.4f} (threshold: {threshold})")
    return distance < threshold


def create_default_admin():
    users = db.reference("users").get() or {}
    for user in users.values():
        if user.get("role") == "admin":
            return
    admin_id = str(uuid.uuid4())
    db.reference("users").child(admin_id).set({
        "id":              admin_id,
        "email":           "admin@admin.com",
        "password":        hash_password("admin123"),
        "role":            "admin",
        "face_embedding":  None,
        "failed_attempts": 0
    })
    print("Default admin created.")


def signup_user(name, email, password, face_base64):
    try:
        if not email or not password:
            return None
        users = db.reference("users").get() or {}
        for user in users.values():
            if user.get("email") == email:
                return None
        embedding = None
        if face_base64:
            embedding = get_embedding(face_base64)
            if not embedding:
                return None
        new_id = str(uuid.uuid4())
        db.reference("users").child(new_id).set({
            "id":              new_id,
            "email":           email,
            "password":        hash_password(password),
            "role":            "user",
            "face_embedding":  embedding,
            "failed_attempts": 0
        })
        return new_id
    except Exception:
        traceback.print_exc()
        return None


def login_user(email, password, face_base64=None):
    users = db.reference("users").get() or {}

    for uid, user in users.items():
        if user.get("email") != email:
            continue

        if not verify_password(password, user["password"]):
            log_event(uid, email, "LOGIN", "FAILED_PASSWORD")
            return uid, "invalid"

        if user.get("role") == "admin":
            log_event(uid, email, "LOGIN", "SUCCESS_ADMIN")
            return user, "success"

        if not face_base64:
            return None, "credentials_ok"

        face_match = False
        stored_embedding = user.get("face_embedding")
        if stored_embedding:
            live_embedding = get_embedding(face_base64)
            if live_embedding:
                face_match = faces_match(stored_embedding, live_embedding)

        if face_match:
            db.reference("users").child(uid).update({"failed_attempts": 0})
            log_event(uid, email, "LOGIN", "SUCCESS")
            return user, "success"
        else:
            generate_otp(uid, email)
            log_event(uid, email, "LOGIN", "OTP_REQUIRED")
            return uid, "otp_required"

    return None, "invalid"