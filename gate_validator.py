import json
from datetime import datetime, timedelta


def validate_qr(payload_str):
    try:
        data = json.loads(payload_str)

        ev_id = data["ev_id"]
        start_time_str = data["start_time"]
        end_time_str = data["end_time"]
        date_str = data["date"]

        current_datetime = datetime.now()

        slot_start = datetime.strptime(
            f"{date_str} {start_time_str}",
            "%Y-%m-%d %H:%M"
        )

        slot_end = datetime.strptime(
            f"{date_str} {end_time_str}",
            "%Y-%m-%d %H:%M"
        )

        # Handle midnight crossing properly
        if slot_end < slot_start:
            slot_end = slot_end + timedelta(days=1)

        if slot_start <= current_datetime <= slot_end:
            print(f"✅ ACCESS GRANTED for {ev_id}")
            return True
        else:
            print(f"❌ ACCESS DENIED for {ev_id} (Outside time slot)")
            return False

    except Exception as e:
        print("❌ Invalid QR format")
        print("Error:", e)
        return False