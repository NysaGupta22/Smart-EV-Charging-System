import qrcode
import json
import os
from datetime import datetime


def generate_qr(slot_info):
    """
    Generates a QR code for a scheduled vehicle.
    Returns the file path of the generated QR.
    """

    payload = {
        "ev_id": slot_info["EV_ID"],
        "start_time": slot_info["Start_Time"].strftime("%H:%M"),
        "end_time": slot_info["End_Time"].strftime("%H:%M"),
        "date": datetime.now().strftime("%Y-%m-%d")
    }

    payload_str = json.dumps(payload)

    # Create QR image
    qr = qrcode.make(payload_str)

    # Create folder if not exists
    if not os.path.exists("qr_codes"):
        os.makedirs("qr_codes")

    file_path = f"qr_codes/{slot_info['EV_ID']}.png"
    qr.save(file_path)

    return file_path, payload_str