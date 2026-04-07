import json
import hashlib
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, db
import time

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://smart-ev-charging-system-4ae41-default-rtdb.asia-southeast1.firebasedatabase.app"
})

SECRET = "ev_charging_secret_key"
GRACE_MINUTES = 10

def sign_payload(payload_str):
    return hashlib.sha256((payload_str + SECRET).encode()).hexdigest()[:16]

def validate_qr(payload_str):
    try:
        data = json.loads(payload_str)
    except json.JSONDecodeError:
        return {"valid": False, "message": "Invalid JSON"}

    required = {"ev_id", "charger", "start_time", "end_time", "date", "sig"}
    missing = required - data.keys()
    if missing:
        return {"valid": False, "message": f"Missing fields: {missing}"}

    received_sig = data.pop("sig")
    base_str = json.dumps(data, sort_keys=True)
    expected_sig = sign_payload(base_str)

    if received_sig != expected_sig:
        return {"valid": False, "message": "Tampered QR"}

    data["sig"] = received_sig

    try:
        slot_start = datetime.strptime(f"{data['date']} {data['start_time']}", "%Y-%m-%d %H:%M")
        slot_end   = datetime.strptime(f"{data['date']} {data['end_time']}",   "%Y-%m-%d %H:%M")

        if slot_end < slot_start:
            slot_end += timedelta(days=1)

        now = datetime.now()
        early_entry = slot_start - timedelta(minutes=GRACE_MINUTES)

        if early_entry <= now <= slot_end:
            print(f"ACCESS GRANTED for {data['ev_id']}")
            return {"valid": True, "ev_id": data["ev_id"], "charger": data["charger"]}
        else:
            print(f"ACCESS DENIED for {data['ev_id']}")
            return {"valid": False, "message": "Outside slot window"}

    except Exception as e:
        return {"valid": False, "message": str(e)}

def validate_and_trigger(payload_str):
    result = validate_qr(payload_str)

    if result["valid"]:
        # First reset to neutral
        db.reference("gate_command").set({
            "action": "none",
            "status": "done",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        time.sleep(0.5)  # let ESP32 see the reset
        
        # Now write the open command
        db.reference("gate_command").set({
            "action": "open",
            "ev_id": result["ev_id"],
            "charger": result["charger"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending"
        })
        print("Gate command sent — waiting for ESP32...")
        
    else:
        db.reference("gate_command").set({
            "action": "deny",
            "reason": result["message"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending"
        })

    return result