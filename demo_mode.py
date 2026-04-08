"""
demo_mode.py — Presentation Demo Setup
Run this on the morning of your presentation.
Sets up slots so EV_ALPHA and EV_GAMMA are always valid for QR scanning during 9am-6pm.
"""

from datetime import datetime, timedelta
from firebase_service import (
    upload_schedule, upload_load_status,
    upload_grid_summary, update_charger_status,
    upload_energy_log
)
from qr_generator import generate_qr
from firebase_admin import db as rtdb

now = datetime.now()

print("\n" + "="*60)
print("  VoltPort Demo Mode — Presentation Setup")
print(f"  Current time: {now.strftime('%H:%M')}")
print("="*60)

# ── Demo window: 9AM to 6PM today — always valid during presentation
slot_start = now.replace(hour=9,  minute=0, second=0, microsecond=0)   # 9:00 AM
slot_end   = now.replace(hour=18, minute=0, second=0, microsecond=0)   # 6:00 PM

immediate = [
    # ── EV_ALPHA — fixed to demo window so QR is always valid ──
    {
        "EV_ID":               "EV_ALPHA",
        "Charger":             1,
        "Start_Time":          slot_start.strftime("%Y-%m-%d %H:%M:%S"),
        "End_Time":            slot_end.strftime("%Y-%m-%d %H:%M:%S"),
        "Emergency":           True,
        "SOC":                 12,
        "Wait_Minutes":        0,
        "Allocated_kW":        7.0,
        "Effective_kW":        4.9,
        "Grid_State":          "stressed",
        "Grid_Action":         "full",
        "Tariff_Rate":         9.0,
        "Tariff_Band":         "peak",
        "Tariff_Delayed":      False,
        "Estimated_kWh":       33.6,
        "Estimated_Cost_INR":  302.4,
        "battery_capacity":    60,
        "SOH":                 94.0,
        "Recommended_Target_SOC": 80,
        "Recommended_kW":      4.9,
        "C_Rate":              0.08,
        "Battery_Warnings":    ["Deep discharge detected (12% SOC)"],
        "V2G_Eligible":        False,
        "V2G_Active":          False,
        "V2G_Earning_INR":     0,
    },
    {
        "EV_ID":               "EV_BETA",
        "Charger":             2,
        "Start_Time":          (now - timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S"),
        "End_Time":            (now + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
        "Emergency":           False,
        "SOC":                 8,
        "Wait_Minutes":        0,
        "Allocated_kW":        7.0,
        "Effective_kW":        4.9,
        "Grid_State":          "stressed",
        "Grid_Action":         "throttle",
        "Tariff_Rate":         9.0,
        "Tariff_Band":         "peak",
        "Tariff_Delayed":      False,
        "Estimated_kWh":       43.2,
        "Estimated_Cost_INR":  388.8,
        "battery_capacity":    50,
        "SOH":                 76.0,
        "Recommended_Target_SOC": 75,
        "Recommended_kW":      3.5,
        "C_Rate":              0.07,
        "Battery_Warnings":    [
            "Deep discharge detected (8% SOC)",
            "Battery health at 76% — reduced rate recommended",
        ],
        "V2G_Eligible":        False,
        "V2G_Active":          False,
        "V2G_Earning_INR":     0,
    },
    # ── EV_GAMMA — QR DEMO VEHICLE ────────────────────────────
    # Slot fixed: 9:00 AM to 6:00 PM today
    # QR will ALWAYS be valid during presentation hours
    {
        "EV_ID":               "EV_GAMMA",
        "Charger":             3,
        "Start_Time":          slot_start.strftime("%Y-%m-%d %H:%M:%S"),
        "End_Time":            slot_end.strftime("%Y-%m-%d %H:%M:%S"),
        "Emergency":           False,
        "SOC":                 35,
        "Wait_Minutes":        0,
        "Allocated_kW":        7.0,
        "Effective_kW":        4.9,
        "Grid_State":          "stressed",
        "Grid_Action":         "throttle",
        "Tariff_Rate":         4.0,
        "Tariff_Band":         "off-peak",
        "Tariff_Delayed":      True,
        "Estimated_kWh":       24.5,
        "Estimated_Cost_INR":  98.0,
        "battery_capacity":    45,
        "SOH":                 88.0,
        "Recommended_Target_SOC": 78,
        "Recommended_kW":      4.9,
        "C_Rate":              0.11,
        "Battery_Warnings":    [],
        "V2G_Eligible":        False,
        "V2G_Active":          False,
        "V2G_Earning_INR":     0,
    },
]

scheduled = [
    {
        "EV_ID":               "EV_DELTA",
        "Charger":             1,
        "Start_Time":          (now + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "End_Time":            (now + timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"),
        "Emergency":           False,
        "SOC":                 45,
        "Wait_Minutes":        120,
        "Allocated_kW":        7.0,
        "Effective_kW":        4.9,
        "Grid_State":          "stressed",
        "Grid_Action":         "throttle",
        "Tariff_Rate":         4.0,
        "Tariff_Band":         "off-peak",
        "Tariff_Delayed":      True,
        "Estimated_kWh":       17.5,
        "Estimated_Cost_INR":  70.0,
        "battery_capacity":    40,
        "SOH":                 97.0,
        "Recommended_Target_SOC": 80,
        "Recommended_kW":      4.9,
        "C_Rate":              0.12,
        "Battery_Warnings":    [],
        "V2G_Eligible":        True,
        "V2G_Active":          False,
        "V2G_Earning_INR":     0,
    },
    {
        "EV_ID":               "EV_EPSILON",
        "Charger":             2,
        "Start_Time":          (now + timedelta(hours=3, minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
        "End_Time":            (now + timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"),
        "Emergency":           False,
        "SOC":                 55,
        "Wait_Minutes":        210,
        "Allocated_kW":        7.0,
        "Effective_kW":        7.0,
        "Grid_State":          "normal",
        "Grid_Action":         "full",
        "Tariff_Rate":         4.0,
        "Tariff_Band":         "off-peak",
        "Tariff_Delayed":      True,
        "Estimated_kWh":       12.25,
        "Estimated_Cost_INR":  49.0,
        "battery_capacity":    55,
        "SOH":                 100.0,
        "Recommended_Target_SOC": 80,
        "Recommended_kW":      7.0,
        "C_Rate":              0.13,
        "Battery_Warnings":    [],
        "V2G_Eligible":        True,
        "V2G_Active":          True,
        "V2G_Earning_INR":     14.7,
    },
]

results = {"immediate": immediate, "scheduled": scheduled}
upload_schedule(results)
print("\n[1/6] Schedule uploaded")

# ── Load status
load_status = {
    "total_kw":              21.0,
    "transformer_rating_kw": 25.0,
    "max_station_kw":        21.0,
    "headroom_kw":           4.0,
    "utilisation_pct":       84.0,
    "state":                 "high",
    "active_chargers":       {"1": 7.0, "2": 7.0, "3": 7.0},
    "timestamp":             now.strftime("%Y-%m-%d %H:%M:%S"),
}
upload_load_status(load_status)
print("[2/6] Load status uploaded — 84% HIGH")

# ── Grid status
grid_summary = {
    "grid_signal":    72,
    "grid_state":     "stressed",
    "total_vehicles": 5,
    "full_power":     1,
    "throttled":      4,
    "suspended":      0,
    "decisions": [
        {"ev_id":"EV_ALPHA",   "grid_signal":72, "grid_state":"stressed",
         "action":"full",     "allowed_kw":7.0, "throttle_factor":1.0,
         "message":"Emergency vehicle — full power override (grid exempt)",
         "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")},
        {"ev_id":"EV_BETA",    "grid_signal":72, "grid_state":"stressed",
         "action":"throttle", "allowed_kw":4.9, "throttle_factor":0.7,
         "message":"Grid STRESSED — throttled to 70% (4.9kW)",
         "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")},
        {"ev_id":"EV_GAMMA",   "grid_signal":72, "grid_state":"stressed",
         "action":"throttle", "allowed_kw":4.9, "throttle_factor":0.7,
         "message":"Grid STRESSED — throttled to 70% (4.9kW)",
         "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")},
        {"ev_id":"EV_DELTA",   "grid_signal":72, "grid_state":"stressed",
         "action":"throttle", "allowed_kw":4.9, "throttle_factor":0.7,
         "message":"Grid STRESSED — throttled to 70% (4.9kW)",
         "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")},
        {"ev_id":"EV_EPSILON", "grid_signal":72, "grid_state":"stressed",
         "action":"v2g",      "allowed_kw":-6.0, "throttle_factor":-0.86,
         "message":"V2G active — discharging 6kW to grid, earning ₹6/kWh",
         "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")},
    ]
}
upload_grid_summary(grid_summary)
print("[3/6] Grid status uploaded — STRESSED 72/100")

# ── Charger statuses
update_charger_status(1, "charging",  ev_id="EV_ALPHA",  allowed_kw=7.0)
update_charger_status(2, "charging",  ev_id="EV_BETA",   allowed_kw=4.9)
update_charger_status(3, "charging",  ev_id="EV_GAMMA",  allowed_kw=4.9)
print("[4/6] Charger statuses updated")

# ── Session history
histories = {
    "EV_ALPHA": {
        "ev_id":             "EV_ALPHA",
        "total_sessions":    8,
        "total_kwh":         284.4,
        "total_revenue_inr": 1706.4,
        "last_charged":      (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
    },
    "EV_BETA": {
        "ev_id":             "EV_BETA",
        "total_sessions":    3,
        "total_kwh":         97.2,
        "total_revenue_inr": 486.0,
        "last_charged":      (now - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
    },
    "EV_GAMMA": {
        "ev_id":             "EV_GAMMA",
        "total_sessions":    12,
        "total_kwh":         392.0,
        "total_revenue_inr": 1764.0,
        "last_charged":      (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
    },
}
for ev_id, history in histories.items():
    rtdb.reference(f"vehicle_usage/{ev_id}").set(history)
print("[5/6] Session history uploaded")

# ── QR codes
for slot in immediate:
    try:
        result = generate_qr(slot)
        if result and result[0]:
            print(f"       QR generated: {result[0]}")
    except Exception as e:
        print(f"       QR skipped for {slot['EV_ID']}: {e}")
print("[6/6] QR codes generated")

print("\n" + "="*60)
print("  Demo ready!")
print("="*60)
print(f"""
QR DEMO VEHICLES: EV_ALPHA + EV_GAMMA
  EV_ALPHA — Charger 01 | Emergency | Slot: {slot_start.strftime('%H:%M')} — {slot_end.strftime('%H:%M')}
  EV_GAMMA — Charger 03 | Off-peak  | Slot: {slot_start.strftime('%H:%M')} — {slot_end.strftime('%H:%M')}

PRESENTATION FLOW:
  1. Open VoltPort website → Admin view
     Show: load 84%, grid stressed, 3 chargers active

  2. Switch to Owner view → type EV_ALPHA
     Show: emergency vehicle, full power, QR code, session history

  3. Type EV_BETA
     Show: low SOC, battery warnings, degraded health

  4. Type EV_GAMMA
     Show: QR code, valid slot, off-peak tariff saved

  5. Run webcam_scanner.py → point at EV_ALPHA or EV_GAMMA QR
     Show: QR validated → Firebase → ESP32 → servo opens

  6. Type EV_EPSILON in admin
     Show: V2G active, earning ₹14.7
""")