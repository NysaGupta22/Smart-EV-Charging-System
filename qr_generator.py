import qrcode
import json
import os
import hashlib
import base64
import io
from datetime import datetime

SECRET = "ev_charging_secret_key"


def sign_payload(payload_str):
    """Generate a short HMAC-style signature to detect tampering."""
    return hashlib.sha256((payload_str + SECRET).encode()).hexdigest()[:16]


def generate_qr(slot_info):
    """
    Generates a QR code for a scheduled vehicle.
    - Saves PNG locally
    - Also returns base64 string for Firebase storage
    Returns (file_path, payload_str, base64_str)
    """
    base_payload = {
        "ev_id": slot_info["EV_ID"],
        "charger": slot_info["Charger"],
        "start_time": slot_info["Start_Time"].strftime("%H:%M") if hasattr(slot_info["Start_Time"], "strftime") else str(slot_info["Start_Time"])[11:16],
        "end_time": slot_info["End_Time"].strftime("%H:%M") if hasattr(slot_info["End_Time"], "strftime") else str(slot_info["End_Time"])[11:16],
        "date": slot_info["Start_Time"].strftime("%Y-%m-%d") if hasattr(slot_info["Start_Time"], "strftime") else str(slot_info["Start_Time"])[:10],
    }

    base_str = json.dumps(base_payload, sort_keys=True)
    base_payload["sig"] = sign_payload(base_str)
    payload_str = json.dumps(base_payload)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(payload_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Save PNG locally
    os.makedirs("qr_codes", exist_ok=True)
    timestamp_tag = slot_info["Start_Time"].strftime("%Y%m%d_%H%M") if hasattr(slot_info["Start_Time"], "strftime") else str(slot_info["Start_Time"]).replace(" ","_")[:16].replace(":","")
    file_path = f"qr_codes/{slot_info['EV_ID']}_{timestamp_tag}.png"

    try:
        img.save(file_path)
    except IOError as e:
        print(f"Failed to save QR for {slot_info['EV_ID']}: {e}")
        return None, None, None

    # Also encode as base64 for Firebase
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Upload to Firebase
    try:
        from firebase_admin import db
        db.reference(f"qr_codes/{slot_info['EV_ID']}").set({
            "image_b64": b64_str,
            "payload":   payload_str,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        print(f"QR uploaded to Firebase for {slot_info['EV_ID']}")
    except Exception as e:
        print(f"QR Firebase upload skipped: {e}")

    return file_path, payload_str, b64_str