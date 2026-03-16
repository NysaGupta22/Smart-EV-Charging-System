import qrcode
import json
import os
import hashlib
from datetime import datetime

SECRET = "ev_charging_secret_key"


def sign_payload(payload_str):
    """Generate a short HMAC-style signature to detect tampering."""
    return hashlib.sha256((payload_str + SECRET).encode()).hexdigest()[:16]


def generate_qr(slot_info):
    """
    Generates a QR code for a scheduled vehicle.
    - Uses slot's actual start date (not system date) to avoid midnight bugs
    - Adds tamper-proof signature
    - Unique filename per vehicle per session to avoid overwrites
    Returns (file_path, payload_str)
    """

    base_payload = {
        "ev_id": slot_info["EV_ID"],
        "charger": slot_info["Charger"],
        "start_time": slot_info["Start_Time"].strftime("%H:%M"),
        "end_time": slot_info["End_Time"].strftime("%H:%M"),
        "date": slot_info["Start_Time"].strftime("%Y-%m-%d"),  # use slot date not system date
    }

    base_str = json.dumps(base_payload, sort_keys=True)
    base_payload["sig"] = sign_payload(base_str)
    payload_str = json.dumps(base_payload)

    # Styled QR with high error correction (survives 30% damage)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(payload_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    os.makedirs("qr_codes", exist_ok=True)

    # Unique filename: EV_ID + date + start_time to prevent overwrites
    timestamp_tag = slot_info["Start_Time"].strftime("%Y%m%d_%H%M")
    file_path = f"qr_codes/{slot_info['EV_ID']}_{timestamp_tag}.png"

    try:
        img.save(file_path)
    except IOError as e:
        print(f"Failed to save QR for {slot_info['EV_ID']}: {e}")
        return None, None

    return file_path, payload_str