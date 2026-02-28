from flask import Blueprint, request, jsonify
from config import get_db
from services.face_service import capture_face_from_image, compare_faces
import base64
import numpy as np

face_bp = Blueprint("face", __name__)
db = get_db()


@face_bp.route("/verify-face", methods=["POST"])
def verify_face():
    data       = request.json
    email      = data.get("email")
    image_data = data.get("image")

    if not email or not image_data:
        return jsonify({"error": "Email and image required"}), 400

    users = db.reference("users").get() or {}
    user_id   = None
    user_data = None

    for uid, user in users.items():
        if user.get("email") == email:
            user_id   = uid
            user_data = user
            break

    if not user_data:
        return jsonify({"error": "User not found"}), 404

    try:
        image_bytes = base64.b64decode(image_data.split(",")[1])
    except Exception:
        return jsonify({"error": "Invalid image format"}), 400

    new_embedding, err = capture_face_from_image(image_bytes)
    if err:
        return jsonify({"error": err}), 400

    known_embedding = user_data.get("face_embedding")
    match = compare_faces(known_embedding, new_embedding)

    if match:
        db.reference("users").child(user_id).update({"failed_attempts": 0})
        return jsonify({"status": "success"}), 200
    else:
        failed = user_data.get("failed_attempts", 0) + 1
        db.reference("users").child(user_id).update({"failed_attempts": failed})

        if failed >= 3:
            return jsonify({
                "status":  "otp_required",
                "user_id": user_id
            }), 403

        return jsonify({"status": "failed"}), 401