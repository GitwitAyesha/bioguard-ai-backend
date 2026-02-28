from config import get_db
from utils.security import hash_password, verify_password
from services.otp_service import generate_otp
from services.log_service import log_event
import uuid
import face_recognition
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import traceback

db = get_db()


def clean_base64(base64_string):
    if not base64_string:
        return None
    if "," in base64_string:
        return base64_string.split(",")[1]
    return base64_string


def process_face(face_base64):
    try:
        face_base64 = clean_base64(face_base64)
        image_data = base64.b64decode(face_base64)
        image = Image.open(BytesIO(image_data)).convert("RGB")
        image = np.array(image, dtype=np.uint8)
        image = np.ascontiguousarray(image)
        encodings = face_recognition.face_encodings(image, model="small")
        if len(encodings) != 1:
            return None
        return encodings[0].tolist()
    except Exception:
        traceback.print_exc()
        return None


def create_default_admin():
    users = db.reference("users").get() or {}
    for user in users.values():
        if user.get("role") == "admin":
            return
    admin_id = str(uuid.uuid4())
    db.reference("users").child(admin_id).set({
        "id": admin_id,
        "email": "admin@admin.com",
        "password": hash_password("admin123"),
        "role": "admin",
        "face_embedding": None,
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
            embedding = process_face(face_base64)
            if not embedding:
                return None
        new_id = str(uuid.uuid4())
        db.reference("users").child(new_id).set({
            "id": new_id,
            "email": email,
            "password": hash_password(password),
            "role": "user",
            "face_embedding": embedding,
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

        # ── Wrong password ──────────────────────────────────────────────
        if not verify_password(password, user["password"]):
            log_event(uid, email, "LOGIN", "FAILED_PASSWORD")
            # Return uid so frontend can send OTP after 3 session attempts
            return uid, "invalid"

        # ── Admin: no face needed ───────────────────────────────────────
        if user.get("role") == "admin":
            log_event(uid, email, "LOGIN", "SUCCESS_ADMIN")
            return user, "success"

        # ── Password-only call: just confirming credentials are valid ───
        if not face_base64:
            return None, "credentials_ok"

        # ── Face verification ───────────────────────────────────────────
        face_match = False
        if user.get("face_embedding"):
            embedding = process_face(face_base64)
            if embedding:
                known = np.array(user["face_embedding"])
                result = face_recognition.compare_faces(
                    [known], np.array(embedding), tolerance=0.6
                )
                face_match = result[0]

        if face_match:
            db.reference("users").child(uid).update({"failed_attempts": 0})
            log_event(uid, email, "LOGIN", "SUCCESS")
            return user, "success"
        else:
            # Face mismatch → send OTP
            generate_otp(uid, email)
            log_event(uid, email, "LOGIN", "OTP_REQUIRED")
            return uid, "otp_required"

    return None, "invalid"