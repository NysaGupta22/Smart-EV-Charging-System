from datetime import datetime, timedelta
from qr_generator import generate_qr

now = datetime.now()
slot = {
    "EV_ID": "EV001",
    "Charger": "C1",
    "Start_Time": now - timedelta(minutes=5),  # started 5 mins ago
    "End_Time": now + timedelta(hours=1),       # ends in 1 hour
}

file_path, payload, b64 = generate_qr(slot)
print(f"QR saved to: {file_path}")
print(f"Payload: {payload}")