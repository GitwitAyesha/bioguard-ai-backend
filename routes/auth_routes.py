from flask import Blueprint, request, jsonify
from services.auth_service import signup_user, login_user
from services.otp_service import verify_otp, generate_otp
from utils.jwt_handler import generate_token
from config import get_db

auth_bp = Blueprint("auth", __name__)
db = get_db()


# ── SIGNUP ──────────────────────────────────────────────────────────────────
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.json
    result = signup_user(
        data.get("name"),
        data.get("email"),
        data.get("password"),
        data.get("face_embedding")
    )
    if result is None:
        return jsonify({"error": "Signup failed. Email may already be registered."}), 400
    return jsonify({"message": "Account created successfully.", "user_id": result}), 201


# ── LOGIN ────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data       = request.json
    email      = data.get("email")
    password   = data.get("password")
    face_b64   = data.get("face_embedding")   # None on first (credentials-only) call

    result, status = login_user(email, password, face_b64)

    # Wrong password — return uid so frontend can trigger OTP after 3 session attempts
    if status == "invalid":
        return jsonify({
            "error": "Invalid email or password.",
            "user_id": result if isinstance(result, str) else None
        }), 401

    # Password correct, no face submitted yet — tell frontend to open camera
    if status == "credentials_ok":
        return jsonify({"status": "credentials_ok"}), 200

    # Face mismatch → OTP already sent by service
    if status == "otp_required":
        return jsonify({
            "status": "otp_required",
            "user_id": result
        }), 200

    # Full success (face matched or admin)
    if status == "success":
        token = generate_token(result)
        return jsonify({"token": token, "role": result["role"]}), 200

    return jsonify({"error": "Authentication failed."}), 401


# ── SEND OTP (called by frontend after 3 wrong password attempts) ─────────────
@auth_bp.route("/send-otp", methods=["POST"])
def send_otp():
    data    = request.json
    user_id = data.get("user_id")
    email   = data.get("email")
    if not user_id or not email:
        return jsonify({"error": "user_id and email required"}), 400
    generate_otp(user_id, email)
    return jsonify({"status": "otp_sent"}), 200


# ── VERIFY OTP ───────────────────────────────────────────────────────────────
@auth_bp.route("/verify-otp", methods=["POST"])
def verify():
    data    = request.json
    user_id = data.get("user_id")
    otp     = data.get("otp")

    if not user_id or not otp:
        return jsonify({"error": "user_id and OTP required"}), 400

    if verify_otp(user_id, otp):
        user = db.reference("users").child(user_id).get()
        # Reset failed attempts on successful OTP
        db.reference("users").child(user_id).update({"failed_attempts": 0})
        token = generate_token(user)
        return jsonify({"token": token, "role": user["role"]}), 200

    return jsonify({"error": "Invalid or expired OTP."}), 401