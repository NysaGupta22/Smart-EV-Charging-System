import heapq
from datetime import datetime, timedelta

from load_manager import LoadManager
from tariff_engine import TariffEngine
from grid_aware_charger import GridAwareCharger, GridSignal
from energy_accountant import EnergyAccountant


class ChargingStation:

    def __init__(
        self,
        total_chargers=3,
        charger_power=7.0,
        target_soc=80,
        max_station_kw=21.0,
        transformer_rating_kw=25.0,
    ):
        self.total_chargers = total_chargers
        self.charger_power = charger_power
        self.target_soc = target_soc
        self.chargers = [None] * total_chargers
        self.priority_queue = []
        self._counter = 0

        # New modules
        self.load_manager = LoadManager(
            max_station_kw=max_station_kw,
            transformer_rating_kw=transformer_rating_kw,
            charger_power_kw=charger_power,
        )
        self.tariff_engine = TariffEngine()
        self.grid_signal = GridSignal(mode="simulate")
        self.grid_charger = GridAwareCharger(
            charger_power_kw=charger_power,
            grid_signal=self.grid_signal,
        )
        self.energy_accountant = EnergyAccountant()

        # Store battery_capacity per EV (needed for energy accounting)
        self._vehicle_capacities = {}

    def calculate_priority(self, soc, emergency, arrival_time):
        if emergency:
            return (0, soc, arrival_time)
        return (1, soc, arrival_time)

    def estimate_charging_time(self, battery_capacity, soc, actual_kw=None):
        actual_kw = actual_kw or self.charger_power
        energy_needed = battery_capacity * (self.target_soc - soc) / 100
        hours = energy_needed / actual_kw
        return int(hours * 60)

    def add_vehicle(self, ev_id, soc, battery_capacity, emergency, arrival_time):
        if soc >= self.target_soc:
            print(f"[SKIP] {ev_id} already at {soc}% SOC (target: {self.target_soc}%)")
            return

        self._vehicle_capacities[ev_id] = battery_capacity
        priority = self.calculate_priority(soc, emergency, arrival_time)
        self._counter += 1
        heapq.heappush(
            self.priority_queue,
            (priority, self._counter, ev_id, soc, battery_capacity, emergency, arrival_time)
        )

    def get_next_available_charger(self):
        for i, c in enumerate(self.chargers):
            if c is None:
                return i
        return min(range(self.total_chargers), key=lambda i: self.chargers[i])

    def schedule(self):
        immediate = []
        scheduled = []

        while self.priority_queue:
            priority, _, ev_id, soc, battery_capacity, emergency, arrival_time = heapq.heappop(
                self.priority_queue
            )

            # ── 1. Load management check ─────────────────────────────────
            charger_index = self.get_next_available_charger()
            allocated_kw = self.load_manager.add_load(charger_index + 1)

            if allocated_kw == 0:
                # Transformer fully saturated — delay this vehicle
                print(f"[LOAD] {ev_id} delayed — transformer saturated")
                delay_start = max(self.chargers, key=lambda c: c or datetime.min) or arrival_time
                start_time = delay_start
                is_immediate = False
                allocated_kw = self.charger_power  # will be allocated when a slot frees up
            else:
                available_time = self.chargers[charger_index]
                if available_time is None or available_time <= arrival_time:
                    start_time = arrival_time
                    is_immediate = True
                else:
                    start_time = available_time
                    is_immediate = False

            # ── 2. Grid-aware power adjustment ───────────────────────────
            grid_decision = self.grid_charger.evaluate_vehicle({
                "EV_ID": ev_id,
                "Emergency": emergency,
                "SOC": soc,
                "Start_Time": start_time,
                "battery_capacity": battery_capacity,
            })
            effective_kw = min(allocated_kw, grid_decision["allowed_kw"])
            if effective_kw <= 0 and not emergency:
                effective_kw = 0  # suspended

            # ── 3. Tariff-based scheduling ────────────────────────────────
            slot_draft = {
                "EV_ID": ev_id,
                "Emergency": emergency,
                "SOC": soc,
                "Start_Time": start_time,
                "battery_capacity": battery_capacity,
            }
            delay, reason, window = self.tariff_engine.should_delay(slot_draft, battery_capacity)
            if delay:
                start_time = window["recommended_start"]
                is_immediate = False
                print(f"[TARIFF] {ev_id} — {reason}")

            # ── 4. Final time calculation ─────────────────────────────────
            actual_kw = effective_kw if effective_kw > 0 else self.charger_power
            charging_minutes = self.estimate_charging_time(battery_capacity, soc, actual_kw)
            finish_time = start_time + timedelta(minutes=charging_minutes)
            self.chargers[charger_index] = finish_time

            wait_minutes = int((start_time - arrival_time).total_seconds() / 60)

            # ── 5. Energy estimate ────────────────────────────────────────
            tariff_rate = self.tariff_engine.get_rate(start_time)
            energy_est = self.energy_accountant.estimate_from_slot(
                slot_draft, battery_capacity, tariff_rate
            )

            slot_info = {
                "EV_ID": ev_id,
                "Charger": charger_index + 1,
                "Start_Time": start_time,
                "End_Time": finish_time,
                "Emergency": emergency,
                "SOC": soc,
                "Wait_Minutes": wait_minutes,
                # Load management
                "Allocated_kW": round(allocated_kw, 2),
                "Effective_kW": round(effective_kw, 2),
                # Grid
                "Grid_State": grid_decision["grid_state"],
                "Grid_Action": grid_decision["action"],
                # Tariff
                "Tariff_Rate": tariff_rate,
                "Tariff_Band": "peak" if self.tariff_engine.is_peak(start_time) else (
                               "off-peak" if self.tariff_engine.is_off_peak(start_time) else "standard"),
                "Tariff_Delayed": delay,
                # Energy
                "Estimated_kWh": energy_est["estimated_kwh"],
                "Estimated_Cost_INR": energy_est["estimated_revenue_inr"],
            }

            if is_immediate:
                immediate.append(slot_info)
            else:
                scheduled.append(slot_info)

        return {"immediate": immediate, "scheduled": scheduled}


def format_slot(slot):
    tag = "[EMERGENCY]" if slot["Emergency"] else ""
    grid_tag = f"[GRID:{slot['Grid_Action'].upper()}]" if slot["Grid_Action"] != "full" else ""
    tariff_tag = f"[{slot['Tariff_Band'].upper()}]"
    return (
        f"EV: {slot['EV_ID']} {tag}{grid_tag} | Charger {slot['Charger']} | "
        f"{slot['Start_Time'].strftime('%H:%M')} -> {slot['End_Time'].strftime('%H:%M')} | "
        f"SOC: {slot['SOC']}% | {slot['Effective_kW']}kW | "
        f"~{slot['Estimated_kWh']}kWh | ₹{slot['Estimated_Cost_INR']} {tariff_tag} | "
        f"Wait: {slot['Wait_Minutes']}min"
    )


if __name__ == "__main__":
    from qr_generator import generate_qr
    from gate_validator import validate_qr
    from firebase_service import (
        upload_schedule, upload_load_status,
        upload_grid_summary
    )

    station = ChargingStation()
    now = datetime.now()

    station.add_vehicle("EV_1", 40, 40, False, now)
    station.add_vehicle("EV_2", 20, 50, False, now)
    station.add_vehicle("EV_3", 70, 35, False, now)
    station.add_vehicle("EV_4", 10, 60, False, now)
    station.add_vehicle("EV_5", 50, 45, True,  now)

    results = station.schedule()

    print("\n--- Immediate Charging ---\n")
    for r in results["immediate"]:
        print(format_slot(r))

    print("\n--- Scheduled Later ---\n")
    for r in results["scheduled"]:
        print(format_slot(r))

    print("\n--- QR Generation & Gate Scan ---\n")
    for r in results["scheduled"]:
        qr_path, payload = generate_qr(r)
        print(f"QR saved: {qr_path}")
        validate_qr(payload)
        print()

    # Upload everything to Firebase
    upload_schedule(results)
    upload_load_status(station.load_manager.get_status())

    all_slots = results["immediate"] + results["scheduled"]
    grid_summary = station.grid_charger.evaluate_all(all_slots)
    upload_grid_summary(grid_summary)

    print("\n--- Energy Estimates ---\n")
    summary = station.energy_accountant.station_summary()
    if summary:
        print(f"Total sessions: {summary['total_sessions']}")
        print(f"Total kWh: {summary['total_kwh']}")
        print(f"Total revenue: ₹{summary['total_revenue_inr']}")

    print("\nAll data uploaded to Firebase")