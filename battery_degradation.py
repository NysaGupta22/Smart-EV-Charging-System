"""
battery_degradation.py — Battery Degradation-Aware Charging Model

Based on real lithium-ion battery degradation research:
- Charging beyond 80% SOC accelerates cathode stress
- Charging rate above 0.5C causes lithium plating
- Deep discharge below 10% damages anode
- High temperature during fast charging accelerates SEI growth

References:
    - Attia et al., "Closed-loop optimization of fast-charging
      protocols for batteries with machine learning" (Nature, 2020)
    - Millner, "Modeling Lithium Ion Battery Degradation in
      Electric Vehicles" (IEEE CIASG, 2010)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ── Constants ─────────────────────────────────────────────────────────────────

# SOC stress multipliers (relative degradation rate)
# Based on electrolyte oxidation curves for NMC chemistry
SOC_STRESS = {
    (0,  10):  3.5,   # deep discharge — anode damage
    (10, 20):  1.8,   # low SOC stress
    (20, 50):  1.0,   # ideal range (baseline)
    (50, 70):  1.1,   # slight increase
    (70, 80):  1.4,   # elevated cathode stress
    (80, 90):  2.2,   # high cathode oxidation
    (90, 100): 3.8,   # severe degradation — avoid
}

# C-rate stress multipliers (charge current / capacity)
# Above 0.5C lithium plating begins on graphite anode
CRATE_STRESS = {
    (0.0, 0.3): 1.0,   # gentle — ideal
    (0.3, 0.5): 1.1,   # moderate
    (0.5, 0.7): 1.5,   # elevated — lithium plating begins
    (0.7, 1.0): 2.4,   # high — significant plating
    (1.0, 2.0): 4.0,   # very high — rapid degradation
}

# Cycle life baseline for NMC (typical apartment EV battery)
BASELINE_CYCLE_LIFE = 1500   # full cycles to 80% capacity retention
CALENDAR_LIFE_YEARS = 10     # years at ideal conditions

# Recommended charging windows
IDEAL_SOC_MIN = 20
IDEAL_SOC_MAX = 80
EMERGENCY_SOC_MAX = 90       # only for emergencies
DEEP_DISCHARGE_THRESHOLD = 15


@dataclass
class BatteryProfile:
    """
    Represents the health and history of a specific EV battery.
    In production this would be persisted per vehicle in Firebase.
    """
    ev_id:            str
    capacity_kwh:     float         # rated capacity
    chemistry:        str = "NMC"   # NMC, LFP, NCA
    manufacture_year: int = 2022

    # Health tracking
    cycle_count:      float = 0.0   # cumulative equivalent full cycles
    calendar_age_days:int   = 0
    current_soh:      float = 100.0 # State of Health (100% = new)

    # Session history
    total_sessions:   int   = 0
    total_kwh_charged:float = 0.0
    deep_discharges:  int   = 0     # times below 15%
    high_soc_charges: int   = 0     # times charged above 85%

    warnings:         list  = field(default_factory=list)


def get_soc_stress(soc: float) -> float:
    """Return degradation stress multiplier for a given SOC."""
    for (low, high), stress in SOC_STRESS.items():
        if low <= soc < high:
            return stress
    return 1.0


def get_crate_stress(c_rate: float) -> float:
    """Return degradation stress multiplier for a given C-rate."""
    for (low, high), stress in CRATE_STRESS.items():
        if low <= c_rate < high:
            return stress
    return 1.0


def calculate_c_rate(charging_kw: float, capacity_kwh: float) -> float:
    """C-rate = charging power / battery capacity."""
    if capacity_kwh <= 0:
        return 0
    return charging_kw / capacity_kwh


def recommend_target_soc(profile: BatteryProfile, emergency: bool = False) -> int:
    """
    Recommend optimal target SOC based on battery health and use case.

    Healthy battery: charge to 80%
    Degraded battery (SOH < 85%): charge to 75% to slow further degradation
    Emergency: allow up to 90%
    LFP chemistry: can safely go to 100%
    """
    if emergency:
        return EMERGENCY_SOC_MAX

    if profile.chemistry == "LFP":
        return 100  # LFP (BYD, some Tesla) is fine at 100%

    if profile.current_soh < 85:
        return 75   # degraded battery — be gentler

    if profile.current_soh < 92:
        return 78

    return 80  # healthy NMC — standard recommendation


def recommend_charge_rate(profile: BatteryProfile, available_kw: float) -> float:
    """
    Recommend safe charging rate based on battery health.
    Limits C-rate to protect degraded batteries.
    """
    max_crate = 0.5  # default safe limit

    if profile.current_soh < 80:
        max_crate = 0.3   # severely degraded — charge very gently
    elif profile.current_soh < 90:
        max_crate = 0.4   # moderately degraded

    max_safe_kw = max_crate * profile.capacity_kwh
    return min(available_kw, max_safe_kw)


def analyze_session(
    profile:    BatteryProfile,
    soc_start:  float,
    soc_end:    float,
    charging_kw:float,
) -> dict:
    """
    Analyze a charging session for degradation impact.
    Returns recommendations and degradation estimates.
    """
    warnings  = []
    tips      = []
    c_rate    = calculate_c_rate(charging_kw, profile.capacity_kwh)

    # SOC checks
    if soc_start < DEEP_DISCHARGE_THRESHOLD:
        warnings.append(f"Deep discharge detected ({soc_start}% SOC) — damages anode over time")
        profile.deep_discharges += 1

    if soc_end > 85:
        warnings.append(f"Charging to {soc_end}% — above 80% accelerates cathode oxidation")
        profile.high_soc_charges += 1
        tips.append("Set charge limit to 80% for daily use")

    if soc_end > 95:
        warnings.append("Charging above 95% causes severe electrolyte oxidation — avoid unless necessary")

    # C-rate checks
    if c_rate > 0.7:
        warnings.append(f"High charge rate ({c_rate:.2f}C) — lithium plating risk on graphite anode")
        tips.append(f"Reduce charge rate to {0.5 * profile.capacity_kwh:.1f}kW max for battery longevity")
    elif c_rate > 0.5:
        tips.append("Moderate charge rate — acceptable but slower charging extends battery life")

    # Calculate degradation for this session
    energy_charged  = profile.capacity_kwh * (soc_end - soc_start) / 100
    equiv_cycles    = energy_charged / profile.capacity_kwh  # fraction of full cycle

    avg_soc         = (soc_start + soc_end) / 2
    soc_factor      = get_soc_stress(avg_soc)
    crate_factor    = get_crate_stress(c_rate)
    degradation     = equiv_cycles * soc_factor * crate_factor

    # Update profile
    profile.cycle_count      += degradation
    profile.total_sessions   += 1
    profile.total_kwh_charged += energy_charged

    # Update SOH — simplified linear model
    # Real models use Arrhenius equation but this is accurate enough
    soh_loss = (degradation / BASELINE_CYCLE_LIFE) * 20  # 20% SOH lost over lifetime
    profile.current_soh = max(0, profile.current_soh - soh_loss)

    # Remaining life estimate
    remaining_cycles  = max(0, BASELINE_CYCLE_LIFE - profile.cycle_count)
    avg_cycles_per_day = max(0.1, profile.cycle_count / max(1, profile.total_sessions)) * 0.3
    remaining_days    = remaining_cycles / avg_cycles_per_day if avg_cycles_per_day > 0 else 9999
    remaining_years   = remaining_days / 365

    # Health grade
    if profile.current_soh >= 95:
        health_grade = "Excellent"
        health_color = "#16a34a"
    elif profile.current_soh >= 88:
        health_grade = "Good"
        health_color = "#0284c7"
    elif profile.current_soh >= 80:
        health_grade = "Fair"
        health_color = "#d97706"
    else:
        health_grade = "Poor"
        health_color = "#dc2626"

    # Optimal next charge recommendation
    recommended_target = recommend_target_soc(profile)
    recommended_rate   = recommend_charge_rate(profile, charging_kw)

    return {
        "ev_id":              profile.ev_id,
        "session_number":     profile.total_sessions,
        "soc_start":          soc_start,
        "soc_end":            soc_end,
        "energy_charged_kwh": round(energy_charged, 3),
        "c_rate":             round(c_rate, 3),
        "c_rate_label":       "High" if c_rate > 0.7 else "Moderate" if c_rate > 0.5 else "Safe",
        "degradation_units":  round(degradation, 4),
        "current_soh":        round(profile.current_soh, 2),
        "health_grade":       health_grade,
        "health_color":       health_color,
        "cycle_count":        round(profile.cycle_count, 2),
        "remaining_cycles":   round(remaining_cycles, 0),
        "estimated_years_left":round(remaining_years, 1),
        "warnings":           warnings,
        "tips":               tips,
        "recommended_target_soc": recommended_target,
        "recommended_max_kw": round(recommended_rate, 2),
        "deep_discharges":    profile.deep_discharges,
        "high_soc_charges":   profile.high_soc_charges,
        "timestamp":          datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def get_slot_recommendation(
    ev_id:       str,
    soc:         float,
    capacity_kwh:float,
    charging_kw: float,
    emergency:   bool = False,
    soh:         float = 100.0,
) -> dict:
    """
    Quick recommendation for the scheduler — no full profile needed.
    Used during slot assignment to adjust target SOC and charge rate.
    """
    profile = BatteryProfile(
        ev_id=ev_id,
        capacity_kwh=capacity_kwh,
        current_soh=soh,
    )

    target_soc   = recommend_target_soc(profile, emergency)
    safe_rate_kw = recommend_charge_rate(profile, charging_kw)
    c_rate       = calculate_c_rate(safe_rate_kw, capacity_kwh)

    warnings = []
    if soc < DEEP_DISCHARGE_THRESHOLD:
        warnings.append(f"Battery at {soc}% — deep discharge detected")
    if soh < 85:
        warnings.append(f"Battery health at {soh}% — reduced charging rate recommended")

    # Recalculate time with safe rate
    energy_needed  = capacity_kwh * (target_soc - soc) / 100
    charge_minutes = int((energy_needed / safe_rate_kw) * 60) if safe_rate_kw > 0 else 0

    return {
        "ev_id":           ev_id,
        "original_target": 80,
        "recommended_target_soc": target_soc,
        "original_kw":     charging_kw,
        "recommended_kw":  safe_rate_kw,
        "c_rate":          round(c_rate, 3),
        "adjusted_minutes":charge_minutes,
        "soh":             soh,
        "warnings":        warnings,
        "degradation_aware": True,
    }