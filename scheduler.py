import heapq
from datetime import datetime, timedelta

TOTAL_CHARGERS = 3
CHARGER_POWER = 7  # kW
TARGET_SOC = 80  # %

priority_queue = []
chargers = [None] * TOTAL_CHARGERS


def calculate_priority(soc, emergency, arrival_time):
    if emergency:
        return (0, soc, arrival_time)
    else:
        return (1, soc, arrival_time)


def estimate_charging_time(battery_capacity, soc):
    energy_needed = battery_capacity * (TARGET_SOC - soc) / 100
    hours = energy_needed / CHARGER_POWER
    minutes = int(hours * 60)
    return minutes


def assign_charger(current_time, charging_minutes):
    for i in range(TOTAL_CHARGERS):
        if chargers[i] is None or chargers[i] <= current_time:
            finish_time = current_time + timedelta(minutes=charging_minutes)
            chargers[i] = finish_time
            return i, finish_time
    return None, None


def next_available_time():
    return min(chargers)


def vehicle_arrival(ev_id, soc, battery_capacity, emergency, arrival_time):
    priority = calculate_priority(soc, emergency, arrival_time)
    heapq.heappush(priority_queue, (priority, ev_id, soc, battery_capacity, emergency, arrival_time))


def process_queue(current_time):
    while priority_queue:
        priority, ev_id, soc, battery_capacity, emergency, arrival_time = heapq.heappop(priority_queue)

        charging_minutes = estimate_charging_time(battery_capacity, soc)

        charger_index, finish_time = assign_charger(current_time, charging_minutes)

        if charger_index is not None:
            print(f"{ev_id} → Assigned to Charger {charger_index + 1}")
            print(f"   Charging Time: {charging_minutes} minutes")
            print(f"   Finishes at: {finish_time.strftime('%H:%M')}")
        else:
            slot_time = next_available_time()
            print(f"{ev_id} → Chargers Full")
            print(f"   Slot Assigned at: {slot_time.strftime('%H:%M')}")
            break


# Simulation
current_time = datetime.now()

vehicle_arrival("EV_1", 40, 40, False, current_time)
vehicle_arrival("EV_2", 20, 50, False, current_time)
vehicle_arrival("EV_3", 70, 35, False, current_time)
vehicle_arrival("EV_4", 10, 60, False, current_time)
vehicle_arrival("EV_5", 50, 45, True, current_time)

print("\n--- Processing Queue ---\n")
process_queue(current_time)