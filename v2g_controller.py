"""
v2g_controller.py — Vehicle-to-Grid (V2G) Controller

Implements bidirectional charging:
  G2V (Grid to Vehicle): normal charging
  V2G (Vehicle to Grid): EV discharges energy back to stabilise the grid

Real-world implementations:
  - Nissan Leaf CHAdeMO with V2G charger
  - Ford F-150 Lightning Intelligent Backup Power
  - Volkswagen ID.4 bidirectional charging (EU)
  - Hyundai IONIQ 5 V2L/V2G

Grid stabilisation logic:
  - Grid signal < 40: request V2G from eligible vehicles
  - Vehicles must have SOC > 50% to participate (protect battery)
  - Owner is compensated at feed-in tariff rate
  - Session automatically resumes G2V when grid recovers
"""

from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional


# ── Constants ─────────────────────────────────────────────────────────────────

# Grid signal thresholds for V2G activation
V2G_TRIGGER_SIGNAL    = 40   # below this → request V2G
V2G_CRITICAL_SIGNAL   = 20   # below this → mandatory V2G for all eligible
V2G_RESUME_SIGNAL     = 60   # above this → resume normal charging

# V2G eligibility
V2G_MIN_SOC           = 50   # vehicle must have >50% to give back
V2G_DISCHARGE_LIMIT   = 30   # never drain below 30% via V2G
V2G_MAX_POWER_KW      = 6.0  # max discharge power per vehicle

# Economics
GRID_FEED_IN_RATE     = 6.0  # ₹/kWh paid to EV owner for V2G energy
GRID_BUY_RATE         = 9.0  # ₹/kWh station pays for grid energy (peak)
V2G_PROFIT_MARGIN     = GRID_BUY_RATE - GRID_FEED_IN_RATE  # ₹/kWh station saves


@dataclass
class V2GSession:
    """Tracks a single V2G discharge event."""
    ev_id:          str
    charger_id:     int
    soc_at_start:   float
    discharge_kw:   float
    start_time:     str
    end_time:       Optional[str] = None
    energy_returned_kwh: float = 0.0
    compensation_inr:    float = 0.0
    status:         str = "active"   # active | completed | cancelled


@dataclass
class V2GController:
    """
    Manages V2G operations across all chargers.
    Decides which vehicles should discharge and tracks compensation.
    """
    feed_in_rate:   float = GRID_FEED_IN_RATE
    max_power_kw:   float = V2G_MAX_POWER_KW
    active_sessions:list  = field(default_factory=list)
    completed_sessions:list = field(default_factory=list)
    total_energy_returned: float = 0.0
    total_compensation_inr:float = 0.0
    grid_stabilised_events:int   = 0

    def assess_grid(self, grid_signal: int, vehicles: list) -> dict:
        """
        Main entry point. Given a grid signal and list of vehicles,
        decide what V2G action to take.

        vehicles: list of slot_info dicts from scheduler
        Returns: V2G assessment with actions per vehicle
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if grid_signal >= V2G_RESUME_SIGNAL:
            return {
                "action":      "none",
                "grid_signal": grid_signal,
                "message":     f"Grid healthy ({grid_signal}/100) — normal G2V charging",
                "v2g_active":  False,
                "vehicles":    [],
                "timestamp":   now,
            }

        if grid_signal >= V2G_TRIGGER_SIGNAL:
            return {
                "action":      "monitor",
                "grid_signal": grid_signal,
                "message":     f"Grid stressed ({grid_signal}/100) — monitoring for V2G need",
                "v2g_active":  False,
                "vehicles":    [],
                "timestamp":   now,
            }

        # Grid below threshold — assess V2G
        mandatory = grid_signal < V2G_CRITICAL_SIGNAL
        eligible  = self._find_eligible_vehicles(vehicles)
        actions   = self._assign_v2g(eligible, grid_signal, mandatory)

        total_v2g_kw = sum(a["v2g_kw"] for a in actions if a["participating"])
        stabilised   = total_v2g_kw > 0

        if stabilised:
            self.grid_stabilised_events += 1

        level = "CRITICAL" if mandatory else "LOW"

        return {
            "action":           "v2g_requested" if not mandatory else "v2g_mandatory",
            "grid_signal":      grid_signal,
            "grid_level":       level,
            "message":          f"Grid {level} ({grid_signal}/100) — V2G {'mandatory' if mandatory else 'requested'}",
            "v2g_active":       stabilised,
            "total_v2g_kw":     round(total_v2g_kw, 2),
            "eligible_count":   len(eligible),
            "participating_count": sum(1 for a in actions if a["participating"]),
            "vehicles":         actions,
            "estimated_duration_min": self._estimate_duration(grid_signal),
            "timestamp":        now,
        }

    def _find_eligible_vehicles(self, vehicles: list) -> list:
        """
        Filter vehicles that can participate in V2G.
        Must be: currently charging (not scheduled), SOC > minimum.
        """
        eligible = []
        for v in vehicles:
            soc = v.get("SOC", 0)
            if soc >= V2G_MIN_SOC:
                eligible.append(v)
        return eligible

    def _assign_v2g(self, eligible: list, grid_signal: int, mandatory: bool) -> list:
        """
        Decide V2G participation for each eligible vehicle.
        Sort by SOC descending — highest SOC vehicles discharge first.
        """
        sorted_vehicles = sorted(eligible, key=lambda v: v.get("SOC", 0), reverse=True)
        actions = []

        # How much power we need from V2G
        # Lower grid signal = need more V2G power
        grid_deficit_factor = (V2G_TRIGGER_SIGNAL - grid_signal) / V2G_TRIGGER_SIGNAL
        target_v2g_kw = 15.0 * grid_deficit_factor  # up to 15kW from V2G
        allocated_kw  = 0

        for v in sorted_vehicles:
            soc        = v.get("SOC", 0)
            ev_id      = v.get("EV_ID", "—")
            emergency  = v.get("Emergency", False)
            capacity   = v.get("battery_capacity", 40)

            # Emergency vehicles never participate in V2G
            if emergency:
                actions.append({
                    "ev_id":        ev_id,
                    "participating":False,
                    "reason":       "Emergency vehicle — exempt from V2G",
                    "v2g_kw":       0,
                    "compensation": 0,
                })
                continue

            # Check if we still need more V2G power
            if allocated_kw >= target_v2g_kw and not mandatory:
                actions.append({
                    "ev_id":        ev_id,
                    "participating":False,
                    "reason":       "Grid needs met by other vehicles",
                    "v2g_kw":       0,
                    "compensation": 0,
                })
                continue

            # Calculate safe discharge amount
            max_discharge_soc = soc - V2G_DISCHARGE_LIMIT
            if max_discharge_soc <= 0:
                actions.append({
                    "ev_id":        ev_id,
                    "participating":False,
                    "reason":       f"SOC too low to discharge safely ({soc}% → would go below {V2G_DISCHARGE_LIMIT}%)",
                    "v2g_kw":       0,
                    "compensation": 0,
                })
                continue

            # Power this vehicle can provide
            discharge_kw  = min(self.max_power_kw, target_v2g_kw - allocated_kw)
            discharge_kwh = capacity * max_discharge_soc / 100
            duration_h    = discharge_kwh / discharge_kw if discharge_kw > 0 else 0
            compensation  = round(discharge_kwh * self.feed_in_rate, 2)
            allocated_kw += discharge_kw

            actions.append({
                "ev_id":              ev_id,
                "participating":      True,
                "soc_current":        soc,
                "soc_after":          V2G_DISCHARGE_LIMIT,
                "v2g_kw":             round(discharge_kw, 2),
                "energy_kwh":         round(discharge_kwh, 3),
                "duration_hours":     round(duration_h, 2),
                "compensation_inr":   compensation,
                "reason":             f"Contributing {discharge_kw:.1f}kW to stabilise grid",
                "message":            f"Discharging {discharge_kw:.1f}kW → earning ₹{compensation}",
            })

            # Start tracking session
            self.active_sessions.append(V2GSession(
                ev_id=ev_id,
                charger_id=v.get("Charger", 0),
                soc_at_start=soc,
                discharge_kw=discharge_kw,
                start_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ))

        return actions

    def _estimate_duration(self, grid_signal: int) -> int:
        """Estimate how long V2G event will last in minutes."""
        # Worse signal = longer event
        severity = (V2G_TRIGGER_SIGNAL - grid_signal) / V2G_TRIGGER_SIGNAL
        return int(5 + severity * 25)  # 5 to 30 minutes

    def complete_session(self, ev_id: str, energy_returned: float):
        """Mark a V2G session as complete and record compensation."""
        for session in self.active_sessions:
            if session.ev_id == ev_id and session.status == "active":
                session.end_time          = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                session.energy_returned_kwh = energy_returned
                session.compensation_inr  = round(energy_returned * self.feed_in_rate, 2)
                session.status            = "completed"

                self.total_energy_returned  += energy_returned
                self.total_compensation_inr += session.compensation_inr
                self.completed_sessions.append(session)
                self.active_sessions.remove(session)
                break

    def get_summary(self) -> dict:
        """Station-level V2G performance summary."""
        return {
            "total_v2g_events":         self.grid_stabilised_events,
            "total_energy_returned_kwh":round(self.total_energy_returned, 3),
            "total_owner_compensation": round(self.total_compensation_inr, 2),
            "total_station_savings":    round(self.total_energy_returned * V2G_PROFIT_MARGIN, 2),
            "active_sessions":          len(self.active_sessions),
            "completed_sessions":       len(self.completed_sessions),
            "feed_in_rate":             self.feed_in_rate,
        }

    def get_owner_v2g_report(self, ev_id: str) -> dict:
        """Per-vehicle V2G earnings report for owner dashboard."""
        sessions = [s for s in self.completed_sessions if s.ev_id == ev_id]
        total_energy = sum(s.energy_returned_kwh for s in sessions)
        total_earned = sum(s.compensation_inr for s in sessions)

        return {
            "ev_id":            ev_id,
            "v2g_sessions":     len(sessions),
            "total_energy_kwh": round(total_energy, 3),
            "total_earned_inr": round(total_earned, 2),
            "avg_per_session":  round(total_earned / len(sessions), 2) if sessions else 0,
            "message":          f"You've earned ₹{total_earned:.0f} contributing to grid stability" if sessions else "No V2G sessions yet",
        }