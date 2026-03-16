from datetime import datetime


class LoadManager:
    """
    Tracks real-time power draw across all chargers.
    Enforces transformer/station capacity limits.
    Supports dynamic power throttling per charger.
    """

    def __init__(self, max_station_kw=21.0, transformer_rating_kw=25.0, charger_power_kw=7.0):
        self.max_station_kw = max_station_kw          # soft limit (station design)
        self.transformer_rating_kw = transformer_rating_kw  # hard limit (never exceed)
        self.charger_power_kw = charger_power_kw      # rated power per charger
        self.active_loads = {}                         # {charger_id: kw_draw}

    def current_load(self):
        """Total power draw across all active chargers."""
        return sum(self.active_loads.values())

    def available_headroom(self):
        """How much more power can be added before hitting transformer limit."""
        return self.transformer_rating_kw - self.current_load()

    def can_add_charger(self, requested_kw=None):
        """Check if adding a new charger would breach transformer rating."""
        requested_kw = requested_kw or self.charger_power_kw
        return (self.current_load() + requested_kw) <= self.transformer_rating_kw

    def add_load(self, charger_id, kw=None):
        """Register a charger as active. Returns actual kw allocated."""
        kw = kw or self.charger_power_kw

        if not self.can_add_charger(kw):
            # Throttle to whatever headroom remains
            headroom = self.available_headroom()
            if headroom <= 0:
                print(f"[LOAD] Charger {charger_id} BLOCKED — transformer at limit "
                      f"({self.current_load():.1f}/{self.transformer_rating_kw}kW)")
                return 0
            print(f"[LOAD] Charger {charger_id} THROTTLED to {headroom:.1f}kW "
                  f"(transformer headroom limited)")
            kw = headroom

        self.active_loads[charger_id] = kw
        self._log_status()
        return kw

    def remove_load(self, charger_id):
        """Deregister a charger (session ended)."""
        if charger_id in self.active_loads:
            released = self.active_loads.pop(charger_id)
            print(f"[LOAD] Charger {charger_id} released {released:.1f}kW — "
                  f"new total: {self.current_load():.1f}kW")
            self._log_status()

    def get_status(self):
        """Return structured load summary for Firebase / dashboard."""
        load = self.current_load()
        headroom = self.available_headroom()

        if load >= self.transformer_rating_kw:
            state = "critical"
        elif load >= self.max_station_kw:
            state = "high"
        elif load >= self.max_station_kw * 0.6:
            state = "moderate"
        else:
            state = "normal"

        return {
            "total_kw": round(load, 2),
            "transformer_rating_kw": self.transformer_rating_kw,
            "max_station_kw": self.max_station_kw,
            "headroom_kw": round(headroom, 2),
            "utilisation_pct": round((load / self.transformer_rating_kw) * 100, 1),
            "state": state,
            "active_chargers": dict(self.active_loads),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def _log_status(self):
        s = self.get_status()
        print(f"[LOAD] Total: {s['total_kw']}kW / {s['transformer_rating_kw']}kW "
              f"({s['utilisation_pct']}%) — State: {s['state'].upper()}")