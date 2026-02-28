import heapq
from datetime import datetime, timedelta
from qr_generator import generate_qr

class ChargingStation:

    def __init__(self, total_chargers=3, charger_power=7, target_soc=80):
        self.total_chargers = total_chargers
        self.charger_power = charger_power
        self.target_soc = target_soc
        self.chargers = [None] * total_chargers
        self.priority_queue = []

    def calculate_priority(self, soc, emergency, arrival_time):
        if emergency:
            return (0, soc, arrival_time)
        return (1, soc, arrival_time)

    def estimate_charging_time(self, battery_capacity, soc):
        energy_needed = battery_capacity * (self.target_soc - soc) / 100
        hours = energy_needed / self.charger_power
        return int(hours * 60)

    def add_vehicle(self, ev_id, soc, battery_capacity, emergency, arrival_time):
        priority = self.calculate_priority(soc, emergency, arrival_time)
        heapq.heappush(
            self.priority_queue,
            (priority, ev_id, soc, battery_capacity, emergency, arrival_time)
        )

    def get_next_available_charger(self):
        if None in self.chargers:
            return self.chargers.index(None)
        return min(range(self.total_chargers), key=lambda i: self.chargers[i])

    def schedule(self):
        immediate = []
        scheduled = []

        while self.priority_queue:
            priority, ev_id, soc, battery_capacity, emergency, arrival_time = heapq.heappop(self.priority_queue)

            charging_minutes = self.estimate_charging_time(battery_capacity, soc)

            charger_index = self.get_next_available_charger()
            available_time = self.chargers[charger_index]

            if available_time is None or available_time <= arrival_time:
                start_time = arrival_time
                is_immediate = True
            else:
                start_time = available_time
                is_immediate = False

            finish_time = start_time + timedelta(minutes=charging_minutes)
            self.chargers[charger_index] = finish_time

            slot_info = {
                "EV_ID": ev_id,
                "Charger": charger_index + 1,
                "Start_Time": start_time,
                "End_Time": finish_time,
                "Emergency": emergency,
                "SOC": soc
            }

            if is_immediate:
                immediate.append(slot_info)
            else:
                scheduled.append(slot_info)

        return {
            "immediate": immediate,
            "scheduled": scheduled
        }


# Simulation
if __name__ == "__main__":
    station = ChargingStation()
    now = datetime.now()

    station.add_vehicle("EV_1", 40, 40, False, now)
    station.add_vehicle("EV_2", 20, 50, False, now)
    station.add_vehicle("EV_3", 70, 35, False, now)
    station.add_vehicle("EV_4", 10, 60, False, now)
    station.add_vehicle("EV_5", 50, 45, True, now)

    results = station.schedule()

    print("\n--- Immediate Charging ---\n")
    for r in results["immediate"]:
        print(r)

    print("\n--- Scheduled Later (QR Needed) ---\n")
    for r in results["scheduled"]:
        print(r)

    print("\n--- Generating QR Codes ---\n")
    for r in results["scheduled"]:
        qr_path, payload = generate_qr(r)
        print(f"QR generated for {r['EV_ID']}")
        print(f"Saved at: {qr_path}")
        print(f"Payload: {payload}\n")