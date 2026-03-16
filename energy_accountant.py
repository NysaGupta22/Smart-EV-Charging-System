from datetime import datetime
from firebase_service import upload_energy_log


RATE_PER_KWH = 8.0  # INR per kWh (default, overridden by tariff)


class EnergyAccountant:
    """
    Tracks kWh consumed per vehicle and per session.
    Estimates revenue at current tariff rate.
    Pushes logs to Firebase under energy_log/ and vehicle_usage/.
    """

    def __init__(self, rate_per_kwh=RATE_PER_KWH):
        self.rate_per_kwh = rate_per_kwh
        self.session_logs = []       # list of completed session dicts
        self.station_total_kwh = 0.0

    def calculate_kwh(self, battery_capacity_kwh, soc_start, soc_end):
        """Energy delivered = capacity × delta_soc."""
        delta = max(0, soc_end - soc_start)
        return round(battery_capacity_kwh * delta / 100, 3)

    def calculate_revenue(self, kwh, rate=None):
        """Revenue in INR for a given kWh amount."""
        rate = rate or self.rate_per_kwh
        return round(kwh * rate, 2)

    def record_session(self, ev_id, charger_id, battery_capacity,
                       soc_start, soc_end, start_time, end_time, tariff_rate=None):
        """
        Record a completed charging session.
        Calculates energy, cost, and duration automatically.
        Pushes to Firebase.
        """
        kwh = self.calculate_kwh(battery_capacity, soc_start, soc_end)
        rate = tariff_rate or self.rate_per_kwh
        revenue = self.calculate_revenue(kwh, rate)

        duration_min = int((end_time - start_time).total_seconds() / 60)

        session = {
            "ev_id": ev_id,
            "charger_id": charger_id,
            "soc_start": soc_start,
            "soc_end": soc_end,
            "battery_capacity_kwh": battery_capacity,
            "energy_delivered_kwh": kwh,
            "rate_per_kwh": rate,
            "revenue_inr": revenue,
            "duration_minutes": duration_min,
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.session_logs.append(session)
        self.station_total_kwh += kwh

        print(f"[ENERGY] {ev_id} | {kwh} kWh | ₹{revenue} | {duration_min} min")

        upload_energy_log(ev_id, session)
        return session

    def station_summary(self):
        """Aggregate stats across all sessions in this run."""
        if not self.session_logs:
            return {}

        total_kwh = sum(s["energy_delivered_kwh"] for s in self.session_logs)
        total_revenue = sum(s["revenue_inr"] for s in self.session_logs)
        avg_kwh = total_kwh / len(self.session_logs)
        avg_duration = sum(s["duration_minutes"] for s in self.session_logs) / len(self.session_logs)

        return {
            "total_sessions": len(self.session_logs),
            "total_kwh": round(total_kwh, 3),
            "total_revenue_inr": round(total_revenue, 2),
            "avg_kwh_per_session": round(avg_kwh, 3),
            "avg_duration_minutes": round(avg_duration, 1),
            "sessions": self.session_logs
        }

    def estimate_from_slot(self, slot_info, battery_capacity, tariff_rate=None):
        """
        Estimate energy and revenue for a scheduled slot before charging starts.
        Useful for dashboard preview.
        """
        soc_start = slot_info["SOC"]
        soc_end = 80  # target
        kwh = self.calculate_kwh(battery_capacity, soc_start, soc_end)
        rate = tariff_rate or self.rate_per_kwh
        revenue = self.calculate_revenue(kwh, rate)

        return {
            "ev_id": slot_info["EV_ID"],
            "estimated_kwh": kwh,
            "estimated_revenue_inr": revenue,
            "rate_per_kwh": rate
        }