import json
import hashlib
from datetime import datetime, timedelta

SECRET = "ev_charging_secret_key"
GRACE_MINUTES = 10  # allow vehicle to arrive up to 10 min early


def sign_payload(payload_str):
    """Reproduce the same signature used in qr_generator."""
    return hashlib.sha256((payload_str + SECRET).encode()).hexdigest()[:16]


def validate_qr(payload_str):
    """
    Validates a scanned QR code payload.
    Checks:
      1. Valid JSON with required fields
      2. Tamper-proof signature
      3. Current time is within the slot window (with grace period)
    Returns True if access granted, False otherwise.
    """
    try:
        data = json.loads(payload_str)
    except json.JSONDecodeError:
        print("ACCESS DENIED — QR payload is not valid JSON")
        return False

    # Check required fields
    required = {"ev_id", "charger", "start_time", "end_time", "date", "sig"}
    missing = required - data.keys()
    if missing:
        print(f"ACCESS DENIED — Missing fields in QR: {missing}")
        return False

    # Verify signature (tamper detection)
    received_sig = data.pop("sig")
    base_str = json.dumps(data, sort_keys=True)
    expected_sig = sign_payload(base_str)

    if received_sig != expected_sig:
        print(f"ACCESS DENIED for {data.get('ev_id', '?')} — QR tampered or invalid")
        return False

    # Restore sig for completeness
    data["sig"] = received_sig

    try:
        ev_id = data["ev_id"]
        date_str = data["date"]
        start_time_str = data["start_time"]
        end_time_str = data["end_time"]

        slot_start = datetime.strptime(f"{date_str} {start_time_str}", "%Y-%m-%d %H:%M")
        slot_end = datetime.strptime(f"{date_str} {end_time_str}", "%Y-%m-%d %H:%M")

        # Handle midnight crossing
        if slot_end < slot_start:
            slot_end += timedelta(days=1)

        current_datetime = datetime.now()
        early_entry = slot_start - timedelta(minutes=GRACE_MINUTES)

        if early_entry <= current_datetime <= slot_end:
            print(f"ACCESS GRANTED for {ev_id} | Charger {data['charger']} | "
                  f"{start_time_str} - {end_time_str}")
            return True
        else:
            if current_datetime < early_entry:
                wait = int((early_entry - current_datetime).total_seconds() / 60)
                print(f"ACCESS DENIED for {ev_id} — Too early, slot opens in {wait} min")
            else:
                print(f"ACCESS DENIED for {ev_id} — Slot expired at {end_time_str}")
            return False

    except KeyError as e:
        print(f"ACCESS DENIED — Missing field: {e}")
        return False
    except Exception as e:
        print(f"ACCESS DENIED — Unexpected error: {e}")
        return False