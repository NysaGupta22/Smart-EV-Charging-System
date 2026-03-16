import firebase_admin
from firebase_admin import credentials, db
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
key_path = os.path.join(BASE_DIR, "firebase_key.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(key_path)
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://smart-ev-charging-system-4ae41-default-rtdb.asia-southeast1.firebasedatabase.app"
    })


def serialize_data(data):
    if isinstance(data, dict):
        return {k: serialize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_data(v) for v in data]
    elif isinstance(data, datetime):
        return data.strftime("%Y-%m-%d %H:%M:%S")
    return data


def upload_schedule(data):
    try:
        db.reference("charging_schedule").set(serialize_data(data))
        print("Schedule uploaded to Firebase")
    except Exception as e:
        print(f"Firebase upload failed: {e}")


def get_schedule():
    try:
        return db.reference("charging_schedule").get()
    except Exception as e:
        print(f"Firebase fetch failed: {e}")
        return None


def update_charger_status(charger_id, status, ev_id=None, allowed_kw=None):
    try:
        db.reference(f"charger_status/charger_{charger_id}").set({
            "status": status,
            "ev_id": ev_id,
            "allowed_kw": allowed_kw,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        print(f"Charger status update failed: {e}")


def get_charger_status():
    try:
        return db.reference("charger_status").get() or {}
    except Exception as e:
        print(f"Charger status fetch failed: {e}")
        return {}


def upload_energy_log(ev_id, session_data):
    try:
        timestamp_key = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean = serialize_data(session_data)
        db.reference(f"energy_log/{ev_id}/{timestamp_key}").set(clean)

        usage_ref = db.reference(f"vehicle_usage/{ev_id}")
        existing = usage_ref.get() or {}
        usage_ref.set({
            "ev_id": ev_id,
            "total_sessions": existing.get("total_sessions", 0) + 1,
            "total_kwh": round(existing.get("total_kwh", 0) + session_data["energy_delivered_kwh"], 3),
            "total_revenue_inr": round(existing.get("total_revenue_inr", 0) + session_data["revenue_inr"], 2),
            "last_charged": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        print(f"Energy log saved for {ev_id}")
    except Exception as e:
        print(f"Energy log upload failed: {e}")


def get_energy_log():
    try:
        return db.reference("energy_log").get() or {}
    except Exception as e:
        print(f"Energy log fetch failed: {e}")
        return {}


def get_vehicle_usage():
    try:
        return db.reference("vehicle_usage").get() or {}
    except Exception as e:
        print(f"Vehicle usage fetch failed: {e}")
        return {}


def upload_load_status(load_status):
    try:
        db.reference("load_status").set(serialize_data(load_status))
    except Exception as e:
        print(f"Load status upload failed: {e}")


def upload_grid_summary(grid_summary):
    try:
        db.reference("grid_status").set(serialize_data(grid_summary))
    except Exception as e:
        print(f"Grid status upload failed: {e}")


def get_station_summary():
    try:
        return {
            "schedule": db.reference("charging_schedule").get() or {},
            "charger_status": db.reference("charger_status").get() or {},
            "load_status": db.reference("load_status").get() or {},
            "grid_status": db.reference("grid_status").get() or {},
            "vehicle_usage": db.reference("vehicle_usage").get() or {},
        }
    except Exception as e:
        print(f"Station summary fetch failed: {e}")
        return {}