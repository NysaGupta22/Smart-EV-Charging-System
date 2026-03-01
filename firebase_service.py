import firebase_admin
from firebase_admin import credentials, db
import os

# Get absolute path of current directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
key_path = os.path.join(BASE_DIR, "firebase_key.json")

cred = credentials.Certificate(key_path)

firebase_admin.initialize_app(cred, {
    "databaseURL": "https://smart-ev-charging-system-4ae41-default-rtdb.asia-southeast1.firebasedatabase.app"
})

def upload_schedule(data):
    from datetime import datetime

    def serialize_data(data):
        if isinstance(data, dict):
            return {k: serialize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [serialize_data(v) for v in data]
        elif isinstance(data, datetime):
            return data.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return data

    clean_data = serialize_data(data)
    ref = db.reference("charging_schedule")
    ref.set(clean_data)