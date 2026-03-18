"""
demo_mode.py — One-Click Demo Setup for Presentation
Populates Firebase with a carefully crafted scenario that shows
every feature of the system working simultaneously.

Run this 2 minutes before your demo:
    PYTHONPATH=. python3 demo_mode.py

What it sets up:
    Charger 1 → EV_ALPHA  EMERGENCY, charging now, throttled by grid
    Charger 2 → EV_BETA   Low SOC (8%), charging now
    Charger 3 → EV_GAMMA  Scheduled off-peak, QR generated, peak warning
    EV_DELTA  → Queued, scheduled off-peak slot
    EV_EPSILON→ Queued, standard rate

Dashboard will show:
    - Load bar at 84% (HIGH state)
    - Grid STRESSED at 72/100
    - Emergency vehicle on Charger 1
    - Peak hour warning for EV_GAMMA
    - Tariff savings card
    - Session history for returning vehicles
"""

from datetime import datetime, timedelta
from firebase_service import (
    upload_schedule, upload_load_status,
    upload_grid_summary, update_charger_status,
    upload_energy_log
)
from qr_generator import generate_qr
from grid_aware_charger import GridSignal

now = datetime.now()

print("\n" + "="*60)
print("  VoltPort Demo Mode — Setting up presentation scenario")
print("="*60)


# ── 1. Craft the schedule ────────────────────────────────────────────────────

immediate = [
    {
        "EV_ID":               "EV_ALPHA",
        "Charger":             1,
        "Start_Time":          (now - timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S"),
        "End_Time":            (now + timedelta(hours=1, minutes=40)).strftime("%Y-%m-%d %H:%M:%S"),
        "Emergency":           True,
        "SOC":                 12,
        "Wait_Minutes":        0,
        "Allocated_kW":        4.9,
        "Effective_kW":        4.9,
        "Grid_State":          "stressed",
        "Grid_Action":         "throttle",
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
        "Battery_Warnings":    ["Deep discharge detected (12% SOC) — damages anode over time"],
        "V2G_Eligible":        False,
        "V2G_Active":          False,
        "V2G_Earning_INR":     0,
    },
    {
        "EV_ID":               "EV_BETA",
        "Charger":             2,
        "Start_Time":          (now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S"),
        "End_Time":            (now + timedelta(hours=5, minutes=20)).strftime("%Y-%m-%d %H:%M:%S"),
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
            "Deep discharge detected (8% SOC) — damages anode over time",
            "Battery health at 76.0% — reduced charging rate recommended",
        ],
        "V2G_Eligible":        False,
        "V2G_Active":          False,
        "V2G_Earning_INR":     0,
    },
]

scheduled = [
    {
        "EV_ID":               "EV_GAMMA",
        "Charger":             3,
        "Start_Time":          (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
        "End_Time":            (now + timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S"),
        "Emergency":           False,
        "SOC":                 35,
        "Wait_Minutes":        60,
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
    {
        "EV_ID":               "EV_DELTA",
        "Charger":             1,
        "Start_Time":          (now + timedelta(hours=2, minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
        "End_Time":            (now + timedelta(hours=6, minutes=30)).strftime("%Y-%m-%d %H:%M:%S"),
        "Emergency":           False,
        "SOC":                 45,
        "Wait_Minutes":        150,
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
        "Start_Time":          (now + timedelta(hours=5, minutes=45)).strftime("%Y-%m-%d %H:%M:%S"),
        "End_Time":            (now + timedelta(hours=8, minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
        "Emergency":           False,
        "SOC":                 55,
        "Wait_Minutes":        345,
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


# ── 2. Load status ────────────────────────────────────────────────────────────

load_status = {
    "total_kw":              21.0,
    "transformer_rating_kw": 25.0,
    "max_station_kw":        21.0,
    "headroom_kw":           4.0,
    "utilisation_pct":       84.0,
    "state":                 "high",
    "active_chargers":       {"1": 7.0, "2": 7.0, "3": 7.0},
    "timestamp":             datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}
upload_load_status(load_status)
print("[2/6] Load status uploaded — 84% HIGH")


# ── 3. Grid status ────────────────────────────────────────────────────────────

grid_summary = {
    "grid_signal":   72,
    "grid_state":    "stressed",
    "total_vehicles": 5,
    "full_power":    0,
    "throttled":     5,
    "suspended":     0,
    "decisions": [
        {"ev_id":"EV_ALPHA",   "grid_signal":72, "grid_state":"stressed", "action":"throttle", "allowed_kw":4.9, "throttle_factor":0.7, "message":"Grid STRESSED — throttled to 70% (4.9kW)", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"ev_id":"EV_BETA",    "grid_signal":72, "grid_state":"stressed", "action":"throttle", "allowed_kw":4.9, "throttle_factor":0.7, "message":"Grid STRESSED — throttled to 70% (4.9kW)", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"ev_id":"EV_GAMMA",   "grid_signal":72, "grid_state":"stressed", "action":"throttle", "allowed_kw":4.9, "throttle_factor":0.7, "message":"Grid STRESSED — throttled to 70% (4.9kW)", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"ev_id":"EV_DELTA",   "grid_signal":72, "grid_state":"stressed", "action":"throttle", "allowed_kw":4.9, "throttle_factor":0.7, "message":"Grid STRESSED — throttled to 70% (4.9kW)", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        {"ev_id":"EV_EPSILON", "grid_signal":72, "grid_state":"stressed", "action":"throttle", "allowed_kw":4.9, "throttle_factor":0.7, "message":"Grid STRESSED — throttled to 70% (4.9kW)", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    ]
}
upload_grid_summary(grid_summary)
print("[3/6] Grid status uploaded — STRESSED 72/100")


# ── 4. Charger statuses ───────────────────────────────────────────────────────

update_charger_status(1, "charging",  ev_id="EV_ALPHA",   allowed_kw=4.9)
update_charger_status(2, "charging",  ev_id="EV_BETA",    allowed_kw=4.9)
update_charger_status(3, "reserved",  ev_id="EV_GAMMA",   allowed_kw=4.9)
print("[4/6] Charger statuses updated")


# ── 5. Session history for returning vehicles ─────────────────────────────────

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

from firebase_service import db
from firebase_admin import db as rtdb

for ev_id, history in histories.items():
    rtdb.reference(f"vehicle_usage/{ev_id}").set(history)

print("[5/6] Session history uploaded for returning vehicles")


# ── 6. QR codes for scheduled vehicles ───────────────────────────────────────

for slot in scheduled:
    try:
        qr_path, payload = generate_qr(slot)
        if qr_path:
            print(f"       QR generated: {qr_path}")
    except Exception as e:
        print(f"       QR skipped for {slot['EV_ID']}: {e}")

print("[6/6] QR codes generated")


# ── Summary ───────────────────────────────────────────────────────────────────

print("\n" + "="*60)
print("  Demo ready! Open your dashboard now.")
print("="*60)
print(f"""
What to show professors:

ADMIN VIEW:
  → Load bar at 84% HIGH — transformer protection working
  → Grid signal 72/100 STRESSED — smart throttling active
  → Charger 1: EV_ALPHA EMERGENCY charging (priority queue)
  → Charger 2: EV_BETA low battery charging
  → Charger 3: EV_GAMMA RESERVED (scheduled off-peak)
  → All vehicles throttled to 4.9kW (grid protection)
  → Energy & cost charts showing per-vehicle breakdown

OWNER VIEW (type each EV ID):
  EV_ALPHA  → Emergency vehicle, charging now, session history (8 sessions)
  EV_GAMMA  → Scheduled slot, QR code displayed, tariff saved ₹X
  EV_BETA   → Low SOC vehicle, charging now, cost estimate
  EV_DELTA  → Future slot, off-peak savings shown
""")