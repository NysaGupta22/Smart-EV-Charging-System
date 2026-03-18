"""
simulation.py — Realistic EV Charging Station Day Simulation
Simulates vehicles arriving throughout the day with random SOC values.
Writes live data to Firebase so the dashboard updates in real time.

Usage:
    PYTHONPATH=. python3 simulation.py           # run full day simulation
    PYTHONPATH=. python3 simulation.py --fast    # compressed time (demo friendly)
"""

import time
import random
import argparse
from datetime import datetime, timedelta
from scheduler_v2 import ChargingStation
from firebase_service import (
    upload_schedule, upload_load_status,
    upload_grid_summary, update_charger_status
)

# ── Vehicle profiles ──────────────────────────────────────────────────────────
# Realistic arrivals based on time of day
ARRIVAL_PROFILES = [
    # (hour, label, soc_range, emergency_prob, battery_capacity)
    (6,  "Morning commuter",  (15, 45), 0.0,  40),
    (7,  "Early office",      (20, 50), 0.0,  50),
    (8,  "Rush hour",         (10, 35), 0.05, 60),
    (9,  "Late starter",      (30, 60), 0.0,  45),
    (12, "Lunch break",       (40, 70), 0.0,  35),
    (13, "Midday",            (25, 55), 0.0,  50),
    (17, "Evening rush",      (10, 40), 0.08, 60),
    (18, "Peak commute",      (15, 45), 0.05, 55),
    (19, "After work",        (20, 50), 0.0,  40),
    (22, "Night owl",         (30, 65), 0.0,  45),
    (23, "Late night",        (35, 70), 0.0,  50),
]

def generate_ev_id(counter):
    return f"EV_{counter:03d}"

def run_simulation(fast_mode=False):
    """
    Run a full day simulation.
    fast_mode: compresses time so demo runs in minutes not hours
    """
    print("\n" + "="*60)
    print("  VoltPort Smart EV Charging — Day Simulation")
    print("="*60)

    counter   = 1
    station   = ChargingStation(total_chargers=3, charger_power=7.0)
    now       = datetime.now()
    time_mult = 60 if fast_mode else 3600  # 1 min = 1 hour in fast mode

    print(f"\nMode: {'FAST (1 min = 1 hr)' if fast_mode else 'REAL TIME'}")
    print(f"Start: {now.strftime('%H:%M:%S')}\n")

    for hour, label, soc_range, emg_prob, capacity in ARRIVAL_PROFILES:
        # Calculate when this vehicle arrives
        arrival = now.replace(hour=hour, minute=random.randint(0,59), second=0)
        if arrival < now:
            arrival += timedelta(days=1)

        wait_seconds = (arrival - datetime.now()).total_seconds()
        if fast_mode:
            wait_seconds = max(0, wait_seconds / time_mult)

        if wait_seconds > 0:
            print(f"  Next arrival in {wait_seconds:.0f}s — {label} at {arrival.strftime('%H:%M')}")
            time.sleep(min(wait_seconds, 30 if fast_mode else 300))

        # Generate vehicle
        ev_id     = generate_ev_id(counter)
        soc       = random.randint(*soc_range)
        emergency = random.random() < emg_prob
        counter  += 1

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {ev_id} arrived")
        print(f"  Profile:   {label}")
        print(f"  SOC:       {soc}%")
        print(f"  Capacity:  {capacity} kWh")
        print(f"  Emergency: {'YES ⚡' if emergency else 'No'}")

        station.add_vehicle(ev_id, soc, capacity, emergency, datetime.now())

        # Schedule and push to Firebase
        results = station.schedule()
        upload_schedule(results)
        upload_load_status(station.load_manager.get_status())

        all_slots = results["immediate"] + results["scheduled"]
        grid_summary = station.grid_charger.evaluate_all(all_slots)
        upload_grid_summary(grid_summary)

        # Update charger statuses
        for slot in results["immediate"]:
            update_charger_status(
                slot["Charger"], "charging",
                ev_id=slot["EV_ID"],
                allowed_kw=slot.get("Effective_kW")
            )

        print(f"  → Scheduled. Firebase updated.")
        print(f"  → Load: {station.load_manager.get_status()['total_kw']}kW / 25kW")

        # Small pause between vehicles
        time.sleep(3 if fast_mode else 10)

    print("\n" + "="*60)
    print("  Simulation complete!")
    print("="*60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true", help="Run in compressed time")
    args = parser.parse_args()
    run_simulation(fast_mode=args.fast)