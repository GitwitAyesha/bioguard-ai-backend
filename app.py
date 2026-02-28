from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load .env before anything else
load_dotenv()

from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.face_routes import face_bp
from services.auth_service import create_default_admin

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(admin_bp, url_prefix="/api/admin")
app.register_blueprint(face_bp, url_prefix="/api/face")


# ------------------ RESET ADMIN (run once if needed) ------------------
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
            print(f"Deleted old admin: {user.get('email')}")

    admin_id = str(uuid.uuid4())
    db.reference("users").child(admin_id).set({
        "id": admin_id,
        "email": "admin@admin.com",
        "password": hash_password("admin123"),
        "role": "admin",
        "face_embedding": None,
        "failed_attempts": 0
    })

    print("Fresh admin created: admin@admin.com / admin123")
    return jsonify({"message": "Admin reset successful. Email: admin@admin.com, Password: admin123"}), 200


if __name__ == "__main__":
    create_default_admin()
    app.run(debug=True, port=5001)