import heapq
from datetime import datetime, timedelta


class ChargingStation:

    def __init__(self, total_chargers=3, charger_power=7, target_soc=80):
        self.total_chargers = total_chargers
        self.charger_power = charger_power  # kW
        self.target_soc = target_soc
        self.chargers = [None] * total_chargers  # stores finish times
        self.priority_queue = []

    # ----------------------------
    # Priority Calculation
    # ----------------------------
    def calculate_priority(self, soc, emergency, arrival_time):
        if emergency:
            return (0, soc, arrival_time)
        return (1, soc, arrival_time)

    # ----------------------------
    # Charging Time Estimation
    # ----------------------------
    def estimate_charging_time(self, battery_capacity, soc):
        energy_needed = battery_capacity * (self.target_soc - soc) / 100
        hours = energy_needed / self.charger_power
        return int(hours * 60)  # minutes

    # ----------------------------
    # Add Vehicle to Queue
    # ----------------------------
    def add_vehicle(self, ev_id, soc, battery_capacity, emergency, arrival_time):
        priority = self.calculate_priority(soc, emergency, arrival_time)
        heapq.heappush(
            self.priority_queue,
            (priority, ev_id, soc, battery_capacity, emergency, arrival_time)
        )

    # ----------------------------
    # Find Next Available Charger
    # ----------------------------
    def get_next_available_charger(self):
        if None in self.chargers:
            return self.chargers.index(None)
        return min(range(self.total_chargers), key=lambda i: self.chargers[i])

    # ----------------------------
    # Scheduling Engine
    # ----------------------------
    def schedule(self):
        results = []

        while self.priority_queue:
            priority, ev_id, soc, battery_capacity, emergency, arrival_time = heapq.heappop(self.priority_queue)

            charging_minutes = self.estimate_charging_time(battery_capacity, soc)

            charger_index = self.get_next_available_charger()
            available_time = self.chargers[charger_index]

            # If charger free now
            if available_time is None or available_time <= arrival_time:
                start_time = arrival_time
            else:
                start_time = available_time

            finish_time = start_time + timedelta(minutes=charging_minutes)

            # Update charger availability
            self.chargers[charger_index] = finish_time

            # Structured response object
            slot_info = {
                "EV_ID": ev_id,
                "Charger": charger_index + 1,
                "Start_Time": start_time.strftime("%H:%M"),
                "End_Time": finish_time.strftime("%H:%M"),
                "Emergency": emergency,
                "SOC": soc
            }

            results.append(slot_info)

        return results


# ----------------------------
# Simulation
# ----------------------------
if __name__ == "__main__":

    station = ChargingStation()

    now = datetime.now()

    station.add_vehicle("EV_1", 40, 40, False, now)
    station.add_vehicle("EV_2", 20, 50, False, now)
    station.add_vehicle("EV_3", 70, 35, False, now)
    station.add_vehicle("EV_4", 10, 60, False, now)
    station.add_vehicle("EV_5", 50, 45, True, now)

    schedule_results = station.schedule()

    for result in schedule_results:
        print(result)