from datetime import datetime
import random


# Simulated grid signal thresholds
GRID_NORMAL_MAX = 100      # % — full power allowed
GRID_STRESSED_MAX = 70     # % — throttle to 70% of rated power
GRID_CRITICAL_MAX = 40     # % — throttle to 40% (emergency vehicles full, others reduced)
GRID_EMERGENCY_CUTOFF = 20 # % — only emergency vehicles charge


class GridSignal:
    """
    Simulates a real-time grid signal.
    In production this would poll a utility API or OCPP grid signal.
    Values: 0-100 (100 = grid fully healthy, 0 = grid collapse)
    """

    def __init__(self, mode="simulate"):
        self.mode = mode           # "simulate" | "manual"
        self._manual_value = 100   # used when mode = "manual"

    def get_signal(self):
        """Return current grid health (0–100)."""
        if self.mode == "manual":
            return self._manual_value

        # Simulate realistic grid variation by time of day
        hour = datetime.now().hour
        if 16 <= hour <= 20:
            # Evening peak — more stress
            base = random.randint(55, 85)
        elif 0 <= hour <= 5:
            # Night — very stable
            base = random.randint(85, 100)
        else:
            base = random.randint(70, 95)

        return base

    def set_manual(self, value):
        """Override grid signal manually (for testing/demo)."""
        self._manual_value = max(0, min(100, value))
        self.mode = "manual"

    def set_simulate(self):
        self.mode = "simulate"


class GridAwareCharger:
    """
    Implements dynamic smart charging based on real-time grid signal.
    Adjusts per-charger power allocation to protect grid stability.
    This is the core of what Tesla Powerwall and OCPP 2.0 implement.
    """

    def __init__(self, charger_power_kw=7.0, grid_signal: GridSignal = None):
        self.charger_power_kw = charger_power_kw
        self.grid = grid_signal or GridSignal()

    def get_grid_state(self, signal=None):
        """Classify grid signal into named states."""
        signal = signal if signal is not None else self.grid.get_signal()

        if signal >= GRID_NORMAL_MAX:
            return "normal"
        elif signal >= GRID_STRESSED_MAX:
            return "stressed"
        elif signal >= GRID_CRITICAL_MAX:
            return "critical"
        elif signal >= GRID_EMERGENCY_CUTOFF:
            return "severe"
        else:
            return "blackout_risk"

    def get_allowed_power(self, is_emergency=False, signal=None):
        """
        Calculate allowed charging power in kW for a vehicle.
        Emergency vehicles always get full power (unless blackout risk).
        """
        signal = signal if signal is not None else self.grid.get_signal()
        state = self.get_grid_state(signal)

        if state == "normal":
            factor = 1.0
        elif state == "stressed":
            factor = 0.7
        elif state == "critical":
            factor = 1.0 if is_emergency else 0.4
        elif state == "severe":
            factor = 1.0 if is_emergency else 0.2
        else:  # blackout_risk
            factor = 1.0 if is_emergency else 0.0

        allowed_kw = round(self.charger_power_kw * factor, 2)
        return allowed_kw, state, factor

    def evaluate_vehicle(self, slot_info):
        """
        Evaluate a single scheduled vehicle against current grid conditions.
        Returns full grid decision dict for this vehicle.
        """
        signal = self.grid.get_signal()
        allowed_kw, state, factor = self.get_allowed_power(
            is_emergency=slot_info["Emergency"],
            signal=signal
        )

        if allowed_kw == 0:
            action = "suspend"
            message = f"Grid {state.upper()} — non-emergency charging suspended"
        elif factor < 1.0:
            action = "throttle"
            pct = int(factor * 100)
            message = f"Grid {state.upper()} — throttled to {pct}% ({allowed_kw}kW)"
        else:
            action = "full"
            message = f"Grid normal — full power ({allowed_kw}kW)"

        # Recalculate charge time at throttled rate
        if allowed_kw > 0:
            energy_needed = slot_info.get("battery_capacity", 40) * (80 - slot_info["SOC"]) / 100
            adjusted_minutes = int((energy_needed / allowed_kw) * 60)
        else:
            adjusted_minutes = None

        return {
            "ev_id": slot_info["EV_ID"],
            "grid_signal": signal,
            "grid_state": state,
            "action": action,
            "allowed_kw": allowed_kw,
            "rated_kw": self.charger_power_kw,
            "throttle_factor": factor,
            "adjusted_charge_minutes": adjusted_minutes,
            "message": message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def evaluate_all(self, slots):
        """Run grid evaluation across all scheduled slots."""
        signal = self.grid.get_signal()
        state = self.get_grid_state(signal)

        results = []
        for slot in slots:
            decision = self.evaluate_vehicle(slot)
            results.append(decision)
            print(f"[GRID] {slot['EV_ID']} — {decision['message']}")

        summary = {
            "grid_signal": signal,
            "grid_state": state,
            "total_vehicles": len(slots),
            "full_power": sum(1 for r in results if r["action"] == "full"),
            "throttled": sum(1 for r in results if r["action"] == "throttle"),
            "suspended": sum(1 for r in results if r["action"] == "suspend"),
            "decisions": results
        }

        print(f"\n[GRID SUMMARY] Signal: {signal}/100 | State: {state.upper()} | "
              f"Full: {summary['full_power']} | Throttled: {summary['throttled']} | "
              f"Suspended: {summary['suspended']}")

        return summary