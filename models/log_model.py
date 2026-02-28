from config import get_db
import datetime
import uuid

db = get_db()

def log_event(user_id, event_type, description):
    log_id = str(uuid.uuid4())
    db.reference(f"logs/{log_id}").set({
        "id": log_id,
        "user_id": user_id,
        "event_type": event_type,
        "description": description,
        "timestamp": str(datetime.datetime.utcnow())
    })
