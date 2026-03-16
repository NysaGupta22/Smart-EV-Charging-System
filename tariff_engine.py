from datetime import datetime, timedelta


# Tariff schedule — INR per kWh by hour of day
TARIFF_SCHEDULE = {
    # Off-peak night (cheapest)
    0:  4.0,  1:  4.0,  2:  4.0,  3:  4.0,
    4:  4.0,  5:  4.5,
    # Morning ramp-up
    6:  6.0,  7:  7.5,  8:  8.0,
    # Day peak
    9:  9.0,  10: 9.0,  11: 9.0,
    12: 8.5,  13: 8.5,
    # Afternoon
    14: 8.0,  15: 8.0,
    # Evening peak (most expensive)
    16: 10.0, 17: 10.0, 18: 10.0, 19: 10.0,
    20: 9.5,  21: 9.0,
    # Night wind-down
    22: 7.0,  23: 5.0,
}

PEAK_HOURS = {h for h, r in TARIFF_SCHEDULE.items() if r >= 9.0}
OFF_PEAK_HOURS = {h for h, r in TARIFF_SCHEDULE.items() if r <= 4.5}

# Maximum delay we're willing to push a non-emergency vehicle (hours)
MAX_DELAY_HOURS = 6


class TariffEngine:
    """
    Time-of-use tariff calculator and cost-optimised delay scheduler.
    Delays non-urgent vehicles to cheaper tariff windows when beneficial.
    """

    def get_rate(self, dt=None):
        """Return INR/kWh rate for a given datetime (defaults to now)."""
        dt = dt or datetime.now()
        return TARIFF_SCHEDULE[dt.hour]

    def is_peak(self, dt=None):
        dt = dt or datetime.now()
        return dt.hour in PEAK_HOURS

    def is_off_peak(self, dt=None):
        dt = dt or datetime.now()
        return dt.hour in OFF_PEAK_HOURS

    def find_cheapest_window(self, from_time, duration_minutes, max_delay_hours=MAX_DELAY_HOURS):
        """
        Search forward from from_time to find the cheapest tariff window
        within the allowed delay horizon.
        Returns (start_time, rate, savings_pct) of the best slot found.
        """
        current_rate = self.get_rate(from_time)
        best_time = from_time
        best_rate = current_rate

        # Check every hour in the delay window
        for offset_hours in range(1, max_delay_hours + 1):
            candidate = from_time + timedelta(hours=offset_hours)
            rate = self.get_rate(candidate)
            if rate < best_rate:
                best_rate = rate
                best_time = candidate

        savings_pct = round((1 - best_rate / current_rate) * 100, 1) if current_rate > 0 else 0

        return {
            "recommended_start": best_time,
            "rate": best_rate,
            "current_rate": current_rate,
            "savings_pct": savings_pct,
            "is_delayed": best_time > from_time
        }

    def should_delay(self, slot_info, battery_capacity):
        """
        Decide whether a vehicle should be delayed to a cheaper slot.
        Rules:
          - Never delay emergency vehicles
          - Never delay vehicles with SOC < 20% (low battery)
          - Only delay if savings > 15%
          - Only delay if it won't push past MAX_DELAY_HOURS
        Returns (should_delay: bool, reason: str, window: dict)
        """
        if slot_info["Emergency"]:
            return False, "Emergency vehicle — no delay", {}

        if slot_info["SOC"] < 20:
            return False, f"Low SOC ({slot_info['SOC']}%) — immediate charge needed", {}

        arrival = slot_info["Start_Time"]
        window = self.find_cheapest_window(arrival, 60)  # assume ~1hr minimum charge

        if not window["is_delayed"]:
            return False, "Already at cheapest rate", window

        if window["savings_pct"] < 15:
            return False, f"Savings too small ({window['savings_pct']}%) — not worth delaying", window

        reason = (f"Delaying to {window['recommended_start'].strftime('%H:%M')} "
                  f"saves {window['savings_pct']}% "
                  f"(₹{window['current_rate']} → ₹{window['rate']}/kWh)")
        return True, reason, window

    def tariff_table(self):
        """Return full 24-hour tariff schedule as a list of dicts."""
        rows = []
        for hour, rate in TARIFF_SCHEDULE.items():
            label = "off-peak" if hour in OFF_PEAK_HOURS else ("peak" if hour in PEAK_HOURS else "standard")
            rows.append({
                "hour": hour,
                "time": f"{hour:02d}:00",
                "rate_inr_kwh": rate,
                "band": label
            })
        return rows

    def cost_estimate(self, kwh, start_time):
        """Estimate cost for a given kWh amount starting at start_time."""
        rate = self.get_rate(start_time)
        return {
            "kwh": kwh,
            "rate_inr_kwh": rate,
            "estimated_cost_inr": round(kwh * rate, 2),
            "band": "peak" if self.is_peak(start_time) else (
                    "off-peak" if self.is_off_peak(start_time) else "standard")
        }