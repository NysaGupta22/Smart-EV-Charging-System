import cv2
from pyzbar import pyzbar
from gate_validator import validate_and_trigger

ESP32_STREAM_URL = "http://192.168.1.10/stream"

print("Connecting to ESP32-CAM stream...")
cap = cv2.VideoCapture(ESP32_STREAM_URL)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Stream error — retrying...")
        cap = cv2.VideoCapture(ESP32_STREAM_URL)
        continue

    qrs = pyzbar.decode(frame)
    for qr in qrs:
        data = qr.data.decode("utf-8")
        print(f"RAW QR DATA: {data}")
        result = validate_and_trigger(data)
        print(f"Result: {result}")

    cv2.imshow("VoltPort QR Scanner", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()