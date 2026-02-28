from flask import Blueprint, jsonify
from config import get_db

admin_bp = Blueprint("admin", __name__)
db = get_db()


# ------------------ GET LOGS ------------------
@admin_bp.route("/logs", methods=["GET"])
def get_logs():
    logs = db.reference("logs").get() or {}
    return jsonify(logs), 200


# ------------------ ADMIN STATS ------------------
@admin_bp.route("/stats", methods=["GET"])
def get_stats():
    users = db.reference("users").get() or {}
    logs = db.reference("logs").get() or {}

    # Exclude admin accounts from total user count
    total_users = sum(1 for u in users.values() if u.get("role") != "admin")

    # Count successful logins from logs
    successful_logins = sum(
        1 for log in logs.values()
        if "SUCCESS" in log.get("status", "").upper()
        and "LOGIN" in log.get("event_type", "").upper()
    )

    # Count failed attempts from logs
    failed_attempts = sum(
        1 for log in logs.values()
        if "FAIL" in log.get("status", "").upper()
    )

    # Suspicious = any OTP_REQUIRED event
    suspicious_events = sum(
        1 for log in logs.values()
        if "OTP_REQUIRED" in log.get("status", "").upper()
    )

    # Locked accounts = users with 3+ failed attempts
    locked_accounts = sum(
        1 for u in users.values()
        if u.get("failed_attempts", 0) >= 3
    )

    # OTPs sent = OTP_GENERATED events
    otps_sent = sum(
        1 for log in logs.values()
        if "OTP" in log.get("event_type", "").upper()
    )

    return jsonify({
        "total_users": total_users,
        "successful_logins": successful_logins,
        "failed_attempts": failed_attempts,
        "suspicious_events": suspicious_events,
        "locked_accounts": locked_accounts,
        "otps_sent": otps_sent,
    }), 200