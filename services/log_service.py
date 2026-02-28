from config import get_db
import uuid
import datetime

db = get_db()

def log_event(user_id, email, event_type, status, details=""):
    log_id = str(uuid.uuid4())
    db.reference("logs").child(log_id).set({
        "id": log_id,
        "user_id": user_id,
        "email": email,
        "event_type": event_type,
        "status": status,
        "details": details,
        "timestamp": datetime.datetime.utcnow().isoformat()
    })
