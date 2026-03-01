import os
from flask import Flask, jsonify, request
from dotenv import load_dotenv

load_dotenv()

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.face_routes import face_bp
from services.auth_service import create_default_admin

app = Flask(__name__)


def is_allowed_origin(origin):
    if not origin:
        return False
    allowed = [
        "http://localhost:5173",
        "http://localhost:3000",
        os.environ.get("FRONTEND_URL", ""),
    ]
    if origin in allowed:
        return True
    if "vercel.app" in origin:
        return True
    return False


@app.after_request
def apply_cors(response):
    origin = request.headers.get("Origin", "")
    if is_allowed_origin(origin):
        response.headers["Access-Control-Allow-Origin"]  = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        origin = request.headers.get("Origin", "")
        if is_allowed_origin(origin):
            res = app.make_default_options_response()
            res.headers["Access-Control-Allow-Origin"]      = origin
            res.headers["Access-Control-Allow-Headers"]     = "Content-Type, Authorization"
            res.headers["Access-Control-Allow-Methods"]     = "GET, POST, PUT, DELETE, OPTIONS"
            res.headers["Access-Control-Allow-Credentials"] = "true"
            res.headers["Access-Control-Max-Age"]           = "3600"
            return res


app.register_blueprint(auth_bp,  url_prefix="/api/auth")
app.register_blueprint(admin_bp, url_prefix="/api/admin")
app.register_blueprint(face_bp,  url_prefix="/api/face")


# ── Health check ─────────────────────────────────────────────────────────────
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "alive"}), 200


# ── Reset admin ───────────────────────────────────────────────────────────────
@app.route("/api/reset-admin", methods=["GET"])
def reset_admin():
    from config import get_db
    from utils.security import hash_password
    import uuid
    db = get_db()
    users = db.reference("users").get() or {}
    for uid, user in users.items():
        if user.get("role") == "admin":
            db.reference("users").child(uid).delete()
    admin_id = str(uuid.uuid4())
    db.reference("users").child(admin_id).set({
        "id":              admin_id,
        "email":           "admin@admin.com",
        "password":        hash_password("admin123"),
        "role":            "admin",
        "face_embedding":  None,
        "failed_attempts": 0
    })
    return jsonify({"message": "Admin reset successful. Email: admin@admin.com, Password: admin123"}), 200


# ── Debug routes ──────────────────────────────────────────────────────────────
@app.route("/api/debug/user/<email>", methods=["GET"])
def debug_user(email):
    from config import get_db
    db = get_db()
    users = db.reference("users").get() or {}
    for uid, user in users.items():
        if user.get("email") == email:
            return jsonify({
                "email":           user.get("email"),
                "failed_attempts": user.get("failed_attempts", 0),
                "role":            user.get("role"),
                "has_face":        bool(user.get("face_embedding")),
            }), 200
    return jsonify({"error": "User not found"}), 404


@app.route("/api/debug/reset/<email>", methods=["GET"])
def debug_reset(email):
    from config import get_db
    db = get_db()
    users = db.reference("users").get() or {}
    for uid, user in users.items():
        if user.get("email") == email:
            db.reference("users").child(uid).update({"failed_attempts": 0})
            return jsonify({"message": f"Reset failed_attempts to 0 for {email}"}), 200
    return jsonify({"error": "User not found"}), 404


if __name__ == "__main__":
    create_default_admin()
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False)