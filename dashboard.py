import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from firebase_service import get_station_summary, get_vehicle_usage
from tariff_engine import TariffEngine, TARIFF_SCHEDULE

st.set_page_config(
    page_title="VoltPort — EV Charging",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Outfit:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #060d0d !important;
    color: #e0ede8;
    font-family: 'Outfit', sans-serif;
}
[data-testid="stAppViewContainer"] { padding: 0 !important; }
[data-testid="stHeader"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stVerticalBlock"] { gap: 0 !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }

/* Streamlit button overrides */
.stButton > button {
    background: transparent !important;
    border: 1px solid #1a3a2a !important;
    color: #6ee7b0 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 1px !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #0d2a1a !important;
    border-color: #2ecc71 !important;
    color: #2ecc71 !important;
}
.stButton > button[kind="primary"] {
    background: #0d2a1a !important;
    border-color: #2ecc71 !important;
    color: #2ecc71 !important;
}
div[data-testid="stSelectbox"] label { display: none !important; }
div[data-testid="stSelectbox"] > div > div {
    background: #0a1a12 !important;
    border: 1px solid #1a3a2a !important;
    border-radius: 10px !important;
    color: #e0ede8 !important;
    font-family: 'DM Mono', monospace !important;
}
div[data-testid="stTextInput"] label {
    font-family: 'Outfit', sans-serif !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
}
div[data-testid="stTextInput"] input {
    background: #0a1a12 !important;
    border: 1px solid #1a3a2a !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 1rem !important;
}
div[data-testid="stTextInput"] input::placeholder { color: #3a6a4a !important; }
div[data-testid="stPlotlyChart"] { background: transparent !important; }

/* ── Animations ── */
@keyframes fadeUp   { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
@keyframes blink    { 0%,100% { opacity:1; } 50% { opacity:0.25; } }
@keyframes scanline { 0% { top: 8px; opacity:0.8; } 100% { top: calc(100% - 8px); opacity:0; } }
@keyframes pulse    { 0%,100% { box-shadow: 0 0 0 0 rgba(46,204,113,0); } 60% { box-shadow: 0 0 0 8px rgba(46,204,113,0.1); } }

/* ── Nav ── */
.vp-nav {
    background: #080f0f;
    border-bottom: 1px solid #0f2a1a;
    padding: 0 2.5rem;
    height: 62px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.vp-logo {
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    font-size: 2.2rem;
    color: #2ecc71;
    letter-spacing: -0.5px;
}
.vp-logo span { color: #ffffff; font-weight: 300; }
.vp-now {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    color: #8ab8a0;
}

/* ── Hero ── */
.vp-hero {
    background: #080f0f;
    border-bottom: 1px solid #0f2a1a;
    padding: 2.5rem 2.5rem 2rem;
    animation: fadeUp 0.5s ease both;
}
.vp-hero-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #0a2018;
    border: 1px solid #1a4a2a;
    border-radius: 20px;
    padding: 4px 12px;
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: #2ecc71;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 1rem;
}
.vp-hero-tag::before {
    content: '';
    width: 6px; height: 6px;
    background: #2ecc71;
    border-radius: 50%;
    animation: blink 1.8s ease-in-out infinite;
}
.vp-hero-title {
    font-size: 2.4rem;
    font-weight: 700;
    color: #ffffff;
    line-height: 1.1;
    margin-bottom: 0.5rem;
    letter-spacing: -0.5px;
}
.vp-hero-sub {
    font-size: 1rem;
    color: #b0d4bc;
    font-family: 'DM Mono', monospace;
    letter-spacing: 0.3px;
}

/* ── Section ── */
.vp-section {
    padding: 2rem 2.5rem;
    border-bottom: 1px solid #0a1e14;
    animation: fadeUp 0.4s ease both;
}
.vp-section-title {
    font-size: 1rem;
    font-weight: 700;
    color: #c8e6d4;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    font-family: 'Outfit', sans-serif;
    margin-bottom: 1.4rem;
    display: flex;
    align-items: center;
    gap: 10px;
}
.vp-section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #0f2a1a;
}

/* ── Cards ── */
.vp-card {
    background: #0a1410;
    border: 1px solid #0f2a1a;
    border-radius: 14px;
    padding: 1.4rem;
    transition: border-color 0.2s, transform 0.2s;
    animation: fadeUp 0.4s ease both;
}
.vp-card:hover {
    border-color: #1a4a2a;
    transform: translateY(-1px);
}
.vp-card.green  { border-color: rgba(46,204,113,0.35); animation: pulse 3s ease-in-out infinite; }
.vp-card.amber  { border-color: rgba(245,158,11,0.3); }
.vp-card.red    { border-color: rgba(239,68,68,0.3); }

/* ── Metrics ── */
.vp-metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
}
.vp-metric {
    background: #0a1410;
    border: 1px solid #0f2a1a;
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    animation: fadeUp 0.4s ease both;
    transition: border-color 0.2s;
}
.vp-metric:hover { border-color: #1a4a2a; }
.vp-metric-label {
    font-family: 'DM Mono', monospace;
    font-size:0.75rem;
    color: #8ab8a0;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.vp-metric-val {
    font-family: 'DM Mono', monospace;
    font-size: 1.9rem;
    font-weight: 500;
    color: #ffffff;
    line-height: 1;
}
.vp-metric-unit {
    font-family: 'DM Mono', monospace;
    font-size:0.75rem;
    color: #8ab8a0;
    margin-top: 0.3rem;
}
.vp-metric.g .vp-metric-val { color: #2ecc71; }
.vp-metric.a .vp-metric-val { color: #f59e0b; }
.vp-metric.r .vp-metric-val { color: #ef4444; }
.vp-metric.b .vp-metric-val { color: #38bdf8; }

/* ── Charger grid ── */
.vp-chargers {
    display: grid;
    grid-template-columns: repeat(3,1fr);
    gap: 14px;
}
.vp-charger {
    background: #0a1410;
    border: 1px solid #0f2a1a;
    border-radius: 14px;
    padding: 1.4rem;
    position: relative;
    overflow: hidden;
    animation: fadeUp 0.4s ease both;
}
.vp-charger::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 14px 14px 0 0;
}
.vp-charger.charging::after  { background: #2ecc71; }
.vp-charger.available::after { background: #38bdf8; }
.vp-charger.reserved::after  { background: #f59e0b; }
.vp-charger.throttled::after { background: #f97316; }
.vp-charger.charging  { border-color: rgba(46,204,113,0.3); }
.vp-charger.available { border-color: rgba(56,189,248,0.2); }
.vp-charger-num  { font-family:'DM Mono',monospace; font-size:0.75rem; color:#8ab8a0; letter-spacing:2px; text-transform:uppercase; margin-bottom:0.7rem; }
.vp-charger-stat { font-size:1.1rem; font-weight:600; margin-bottom:0.3rem; }
.vp-charger.charging  .vp-charger-stat { color:#2ecc71; }
.vp-charger.available .vp-charger-stat { color:#38bdf8; }
.vp-charger.reserved  .vp-charger-stat { color:#f59e0b; }
.vp-charger.throttled .vp-charger-stat { color:#f97316; }
.vp-charger-ev   { font-family:'DM Mono',monospace; font-size:0.9rem; color:#e8f4ee; }
.vp-charger-foot { font-family:'DM Mono',monospace; font-size:0.75rem; color:#8ab8a0; margin-top:0.9rem; padding-top:0.8rem; border-top:1px solid #0f2a1a; }

/* ── Booking card ── */
.vp-booking {
    background: #0a1a12;
    border: 1px solid rgba(46,204,113,0.3);
    border-radius: 16px;
    padding: 1.8rem;
    animation: pulse 4s ease-in-out infinite;
}
.vp-booking-ev   { font-size:1.8rem; font-weight:700; color:#ffffff; margin-bottom:0.2rem; letter-spacing:-0.5px; }
.vp-booking-meta { font-family:'DM Mono',monospace; font-size:0.82rem; color:#8ab8a0; margin-bottom:1.6rem; display:flex; align-items:center; gap:8px; }
.vp-live { width:7px; height:7px; border-radius:50%; background:#2ecc71; display:inline-block; animation:blink 1.5s ease-in-out infinite; }
.vp-live.amber { background:#f59e0b; }
.vp-time-big { font-family:'DM Mono',monospace; font-size:2.8rem; font-weight:500; color:#2ecc71; letter-spacing:-2px; line-height:1; }
.vp-time-big.muted { color:#ffffff; }
.vp-time-lbl { font-family:'DM Mono',monospace; font-size:0.72rem; color:#8ab8a0; letter-spacing:1.5px; text-transform:uppercase; margin-top:0.3rem; }
.vp-divider { height:1px; background:#0f2a1a; margin:1.4rem 0; }
.vp-detail-lbl { font-family:'DM Mono',monospace; font-size:0.72rem; color:#8ab8a0; letter-spacing:1px; text-transform:uppercase; margin-bottom:0.3rem; }
.vp-detail-val { font-family:'DM Mono',monospace; font-size:0.95rem; color:#e8f4ee; }

/* ── Cost card ── */
.vp-cost {
    background: #0a1410;
    border: 1px solid #0f2a1a;
    border-radius: 16px;
    padding: 1.8rem;
    height: 100%;
}
.vp-cost-amt { font-family:'DM Mono',monospace; font-size:2.6rem; font-weight:500; color:#2ecc71; letter-spacing:-1px; line-height:1; margin-bottom:0.3rem; }
.vp-cost-sub { font-family:'DM Mono',monospace; font-size:0.78rem; color:#8ab8a0; margin-bottom:1.4rem; }

/* ── QR wrap ── */
.vp-qr-outer {
    position: relative;
    display: inline-block;
    border: 2px solid #2ecc71;
    border-radius: 12px;
    padding: 10px;
    background: white;
    overflow: hidden;
}
.vp-qr-scan {
    position: absolute;
    left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent 0%, #2ecc71 50%, transparent 100%);
    animation: scanline 2.2s ease-in-out infinite;
    top: 10px;
}

/* ── Table ── */
.vp-tbl { width:100%; border-collapse:collapse; }
.vp-tbl th {
    font-family:'DM Mono',monospace;
    font-size:0.7rem;
    color:#8ab8a0;
    letter-spacing:2px;
    text-transform:uppercase;
    padding:0.7rem 0.9rem;
    border-bottom:1px solid #0f2a1a;
    text-align:left;
    background:#080f0f;
}
.vp-tbl td {
    font-family:'DM Mono',monospace;
    font-size:0.82rem;
    color:#e0ede8;
    padding:0.85rem 0.9rem;
    border-bottom:1px solid #0a1a12;
}
.vp-tbl tr:last-child td { border-bottom:none; }
.vp-tbl tr:hover td { background:#0a1a12; }
.vp-badge {
    display:inline-block;
    padding:2px 7px;
    border-radius:4px;
    font-size:0.6rem;
    font-weight:600;
    letter-spacing:0.5px;
    text-transform:uppercase;
    font-family:'DM Mono',monospace;
}
.b-em  { background:#1a0a0a; color:#ef4444; border:1px solid #3a0a0a; }
.b-now { background:#0a2018; color:#2ecc71; border:1px solid #1a4a2a; }
.b-sch { background:#1a1208; color:#f59e0b; border:1px solid #3a2808; }
.b-op  { background:#0a2018; color:#4ade80; border:1px solid #1a4a2a; }
.b-pk  { background:#1a0a0a; color:#f87171; border:1px solid #3a0a0a; }
.b-std { background:#0a1a2a; color:#38bdf8; border:1px solid #1a3a4a; }
.b-thr { background:#1a0e08; color:#f97316; border:1px solid #3a1a08; }
.b-ok  { background:#0a2018; color:#2ecc71; border:1px solid #1a4a2a; }
.b-str { background:#1a1208; color:#f59e0b; border:1px solid #3a2808; }
.b-crt { background:#1a0a0a; color:#ef4444; border:1px solid #3a0a0a; }

/* ── Load bar ── */
.vp-bar-bg { background:#0a1a12; border-radius:6px; height:10px; overflow:hidden; margin:0.5rem 0; }
.vp-bar-fill { height:100%; border-radius:6px; transition:width 0.6s ease; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_data():
    try:
        return get_station_summary()
    except Exception as e:
        st.error(f"Firebase error: {e}")
        return {}

def get_qr_b64(ev_id):
    qr_dir = "qr_codes"
    if not os.path.exists(qr_dir):
        return None
    matches = [f for f in os.listdir(qr_dir) if f.startswith(ev_id)]
    if not matches:
        return None
    with open(os.path.join(qr_dir, sorted(matches)[-1]), "rb") as f:
        return base64.b64encode(f.read()).decode()

def fmt_time(t):
    if hasattr(t, 'strftime'):
        return t.strftime('%H:%M')
    s = str(t)
    return s[11:16] if len(s) > 10 else s

def state_col(s):
    return {"normal":"#2ecc71","moderate":"#38bdf8","high":"#f59e0b","critical":"#ef4444",
            "stressed":"#f59e0b","severe":"#ef4444"}.get(s,"#3a6a4a")

def grid_col(sig):
    if sig >= 85: return "#2ecc71"
    if sig >= 70: return "#38bdf8"
    if sig >= 55: return "#f59e0b"
    return "#ef4444"

def tariff_col(band):
    return {"off-peak":"#2ecc71","standard":"#38bdf8","peak":"#ef4444"}.get(band,"#3a6a4a")


# ── Session state ─────────────────────────────────────────────────────────────

if "view" not in st.session_state:
    st.session_state.view = "owner"

# ── Nav ───────────────────────────────────────────────────────────────────────

now_str = datetime.now().strftime("%a %d %b  %H:%M")
c1, c2, c3 = st.columns([1, 2, 1])
with c1:
    st.markdown('<div class="vp-nav" style="background:transparent;border:none;padding:0.8rem 0"><div class="vp-logo">Volt<span>Port</span></div></div>', unsafe_allow_html=True)
with c2:
    b1, b2 = st.columns(2)
    with b1:
        if st.button("⚡  Owner", key="btn_owner",
                     type="primary" if st.session_state.view == "owner" else "secondary",
                     use_container_width=True):
            st.session_state.view = "owner"
            st.rerun()
    with b2:
        if st.button("⚙  Admin", key="btn_admin",
                     type="primary" if st.session_state.view == "admin" else "secondary",
                     use_container_width=True):
            st.session_state.view = "admin"
            st.rerun()
with c3:
    st.markdown(f'<div style="text-align:right;font-family:DM Mono,monospace;font-size:0.78rem;color:#8ab8a0;padding-top:0.9rem">{now_str}</div>', unsafe_allow_html=True)

st.markdown('<div style="height:1px;background:#0a2018;margin-bottom:0"></div>', unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────

data         = load_data()
schedule     = data.get("schedule", {})
c_status     = data.get("charger_status", {})
load_st      = data.get("load_status", {})
grid_st      = data.get("grid_status", {})
vehicle_usage_all = data.get("vehicle_usage", {}) or {}
immediate    = schedule.get("immediate", []) or []
sched_later  = schedule.get("scheduled", []) or []
all_slots    = immediate + sched_later
tariff       = TariffEngine()


# ════════════════════════════════════════════════════════════════
# OWNER VIEW
# ════════════════════════════════════════════════════════════════

if st.session_state.view == "owner":

    st.markdown("""
    <div class="vp-hero">
        <div class="vp-hero-tag">VoltPort EV Charging</div>
        <div class="vp-hero-title">My Charging Portal</div>
        <div class="vp-hero-sub">Track your session · View your slot · Get your QR</div>
    </div>
    """, unsafe_allow_html=True)

    # Vehicle lookup
    st.markdown('<div class="vp-section">', unsafe_allow_html=True)
    st.markdown('<div class="vp-section-title">Look up your booking</div>', unsafe_allow_html=True)
    ev_input = st.text_input(
        "Enter your vehicle ID",
        placeholder="e.g. EV_1, EV_2 ...",
        label_visibility="visible"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    selected  = ev_input.strip().upper() if ev_input else None
    my_slot   = next((s for s in all_slots if s["EV_ID"] == selected), None) if selected else None
    is_now    = any(s["EV_ID"] == selected for s in immediate) if selected else False

    if not selected:
        st.markdown("""
        <div style="padding:1.5rem 0 0;font-family:'Outfit',sans-serif;font-size:1rem;font-weight:500;color:#b0d4bc;line-height:1.6">
            Enter your vehicle ID above to view your booking details and QR code.
        </div>
        """, unsafe_allow_html=True)
    elif not my_slot:
        st.markdown(f"""
        <div style="padding:1rem 0 0;font-family:'Outfit',sans-serif;font-size:1rem;font-weight:500;color:#f59e0b">
            No booking found for <b style="color:#ffffff">{selected}</b>. Check your vehicle ID and try again.
        </div>
        """, unsafe_allow_html=True)
    else:
        start      = my_slot.get("Start_Time","")
        end        = my_slot.get("End_Time","")
        charger    = my_slot.get("Charger","—")
        soc        = my_slot.get("SOC","—")
        wait       = my_slot.get("Wait_Minutes",0)
        est_kwh    = my_slot.get("Estimated_kWh","—")
        est_cost   = my_slot.get("Estimated_Cost_INR","—")
        band       = my_slot.get("Tariff_Band","standard")
        eff_kw     = my_slot.get("Effective_kW","—")
        grid_act   = my_slot.get("Grid_Action","full")
        rate       = my_slot.get("Tariff_Rate","—")
        status_txt = "Charging now" if is_now else f"Starts in {wait} min"
        dot_cls    = "vp-live" if is_now else "vp-live amber"

        # Booking + cost
        st.markdown('<div class="vp-section">', unsafe_allow_html=True)
        st.markdown('<div class="vp-section-title">Your booking</div>', unsafe_allow_html=True)
        col_b, col_c = st.columns([3, 2])

        with col_b:
            grid_color_val = "#f97316" if grid_act == "throttle" else "#2ecc71"
            st.markdown(f"""
            <div class="vp-booking">
                <div class="vp-booking-ev">{selected}</div>
                <div class="vp-booking-meta">
                    <span class="{dot_cls}"></span>
                    Charger {charger} &nbsp;·&nbsp; {status_txt}
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-bottom:0">
                    <div>
                        <div class="vp-time-big">{fmt_time(start)}</div>
                        <div class="vp-time-lbl">Start time</div>
                    </div>
                    <div>
                        <div class="vp-time-big muted">{fmt_time(end)}</div>
                        <div class="vp-time-lbl">End time</div>
                    </div>
                </div>
                <div class="vp-divider"></div>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem">
                    <div>
                        <div class="vp-detail-lbl">Battery SOC</div>
                        <div class="vp-detail-val">{soc}%</div>
                    </div>
                    <div>
                        <div class="vp-detail-lbl">Power</div>
                        <div class="vp-detail-val">{eff_kw} kW</div>
                    </div>
                    <div>
                        <div class="vp-detail-lbl">Grid</div>
                        <div class="vp-detail-val" style="color:{grid_color_val}">{grid_act.upper()}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_c:
            tc = tariff_col(band)
            band_display = "OFF-PEAK" if band == "off-peak" else band.upper()
            st.markdown(f"""
            <div class="vp-cost">
                <div class="vp-detail-lbl" style="margin-bottom:0.6rem">Estimated cost</div>
                <div class="vp-cost-amt">₹{est_cost}</div>
                <div class="vp-cost-sub">~{est_kwh} kWh delivered</div>
                <div class="vp-divider"></div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem">
                    <div>
                        <div class="vp-detail-lbl">Tariff band</div>
                        <div class="vp-detail-val" style="color:{tc};font-weight:600">{band_display}</div>
                    </div>
                    <div>
                        <div class="vp-detail-lbl">Rate</div>
                        <div class="vp-detail-val">₹{rate}/kWh</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # ── 1. Slot notification ─────────────────────────────────
        if not is_now and my_slot:
            try:
                start_dt = start if hasattr(start, 'hour') else datetime.strptime(str(start), "%Y-%m-%d %H:%M:%S")
                mins_until = int((start_dt - datetime.now()).total_seconds() / 60)
                if 0 < mins_until <= 15:
                    st.toast(f"⚡ Your slot starts in {mins_until} min — head to Charger {charger} now!", icon="⚡")
                    st.markdown(f"""
                    <div style="background:#0a2018;border:1px solid #2ecc71;border-radius:12px;
                                padding:1rem 1.4rem;margin:0 0 0 0;display:flex;align-items:center;gap:12px;
                                animation:pulse 2s ease-in-out infinite">
                        <span style="font-size:1.4rem">⚡</span>
                        <div>
                            <div style="font-family:'Outfit',sans-serif;font-size:1rem;font-weight:700;color:#2ecc71;margin-bottom:0.2rem">
                                Slot starting in {mins_until} min
                            </div>
                            <div style="font-family:'DM Mono',monospace;font-size:0.8rem;color:#8ab8a0">
                                Head to Charger {charger} now · Bring your QR code
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                elif mins_until <= 0 and mins_until > -10:
                    st.markdown(f"""
                    <div style="background:#0a2018;border:1px solid #f59e0b;border-radius:12px;
                                padding:1rem 1.4rem;margin:0 0 0 0;display:flex;align-items:center;gap:12px">
                        <span style="font-size:1.4rem">⏰</span>
                        <div>
                            <div style="font-family:'Outfit',sans-serif;font-size:1rem;font-weight:700;color:#f59e0b;margin-bottom:0.2rem">
                                Your slot is open now
                            </div>
                            <div style="font-family:'DM Mono',monospace;font-size:0.8rem;color:#8ab8a0">
                                Charger {charger} · 10 min grace period applies
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            except Exception:
                pass

        # ── 2. Peak hour warning ──────────────────────────────────
        if my_slot and not is_now:
            try:
                current_rate = my_slot.get("Tariff_Rate", 0)
                delayed = my_slot.get("Tariff_Delayed", False)
                if isinstance(current_rate, (int, float)) and float(current_rate) >= 9.0 and not delayed:
                    # Find cheapest rate in next 8 hours
                    best_hour = min(range(24), key=lambda h: TARIFF_SCHEDULE[h])
                    best_rate = TARIFF_SCHEDULE[best_hour]
                    kwh = my_slot.get("Estimated_kWh", 0)
                    if isinstance(kwh, (int, float)) and kwh > 0:
                        current_cost = round(float(kwh) * float(current_rate), 2)
                        best_cost    = round(float(kwh) * best_rate, 2)
                        savings      = round(current_cost - best_cost, 2)
                        if savings > 0:
                            st.markdown(f"""
                            <div style="background:#1a1208;border:1px solid rgba(245,158,11,0.4);
                                        border-radius:12px;padding:1.2rem 1.4rem;
                                        margin:1.5rem 0 0 0;display:flex;align-items:flex-start;gap:12px">
                                <span style="font-size:1.4rem;flex-shrink:0">💡</span>
                                <div style="flex:1">
                                    <div style="font-family:'Outfit',sans-serif;font-size:1rem;
                                                font-weight:700;color:#f59e0b;margin-bottom:0.4rem">
                                        Peak hour — you could save ₹{savings}
                                    </div>
                                    <div style="font-family:'DM Mono',monospace;font-size:0.82rem;
                                                color:#8ab8a0;line-height:1.7">
                                        Current rate: <span style="color:#ef4444">₹{current_rate}/kWh (PEAK)</span><br>
                                        Cheapest rate: <span style="color:#2ecc71">₹{best_rate}/kWh at {best_hour:02d}:00 (OFF-PEAK)</span><br>
                                        Charging after midnight could save you <span style="color:#f59e0b;font-weight:500">₹{savings}</span> on this session.
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
            except Exception:
                pass

        # ── QR ────────────────────────────────────────────────────
        if not is_now:
            st.markdown('<div class="vp-section">', unsafe_allow_html=True)
            st.markdown('<div class="vp-section-title">Gate access QR</div>', unsafe_allow_html=True)
            qr_b64 = get_qr_b64(selected)
            if qr_b64:
                col_q1, col_q2 = st.columns([1, 2])
                with col_q1:
                    st.markdown(f"""
                    <div class="vp-qr-outer">
                        <img src="data:image/png;base64,{qr_b64}" width="190" style="display:block"/>
                        <div class="vp-qr-scan"></div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_q2:
                    st.markdown(f"""
                    <div style="padding:0.5rem 0 0">
                        <div class="vp-detail-lbl" style="margin-bottom:0.8rem">How to use</div>
                        <div style="display:flex;flex-direction:column;gap:0.8rem">
                            <div style="display:flex;gap:10px;align-items:flex-start">
                                <span style="background:#0a2018;border:1px solid #1a4a2a;color:#2ecc71;font-family:DM Mono,monospace;font-size:0.65rem;width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0">1</span>
                                <span style="font-size:0.9rem;color:#e0ede8;line-height:1.5">Arrive at <b style="color:#ffffff">Charger {charger}</b> at your scheduled time</span>
                            </div>
                            <div style="display:flex;gap:10px;align-items:flex-start">
                                <span style="background:#0a2018;border:1px solid #1a4a2a;color:#2ecc71;font-family:DM Mono,monospace;font-size:0.65rem;width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0">2</span>
                                <span style="font-size:0.9rem;color:#e0ede8;line-height:1.5">Scan QR at the gate terminal</span>
                            </div>
                            <div style="display:flex;gap:10px;align-items:flex-start">
                                <span style="background:#0a2018;border:1px solid #1a4a2a;color:#2ecc71;font-family:DM Mono,monospace;font-size:0.65rem;width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0">3</span>
                                <span style="font-size:0.9rem;color:#e0ede8;line-height:1.5">10-minute grace period applies</span>
                            </div>
                        </div>
                        <div class="vp-divider"></div>
                        <div class="vp-detail-lbl">Valid window</div>
                        <div style="font-family:'DM Mono',monospace;font-size:1rem;color:#2ecc71;font-weight:500;margin-top:0.3rem">
                            {fmt_time(start)} — {fmt_time(end)}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("QR not yet generated — run scheduler_v2.py first.")
            st.markdown('</div>', unsafe_allow_html=True)

        # ── 3. Session history ────────────────────────────────────
        usage = vehicle_usage_all.get(selected, {}) if vehicle_usage_all else {}

        st.markdown('<div class="vp-section">', unsafe_allow_html=True)
        st.markdown('<div class="vp-section-title">Session history</div>', unsafe_allow_html=True)

        if usage and usage.get("total_sessions", 0) > 0:
            total_sessions = usage.get("total_sessions", 0)
            total_kwh      = usage.get("total_kwh", 0)
            total_spent    = usage.get("total_revenue_inr", 0)
            last_charged   = usage.get("last_charged", "—")
            avg_kwh        = round(total_kwh / total_sessions, 2) if total_sessions > 0 else 0
            avg_cost       = round(total_spent / total_sessions, 2) if total_sessions > 0 else 0

            h1, h2, h3, h4 = st.columns(4)
            for col, lbl, val, unit in [
                (h1, "Total sessions",  str(total_sessions), "charges"),
                (h2, "Total energy",    f"{total_kwh}",      "kWh used"),
                (h3, "Total spent",     f"₹{total_spent}",   "lifetime"),
                (h4, "Avg per session", f"₹{avg_cost}",      f"~{avg_kwh} kWh"),
            ]:
                with col:
                    st.markdown(f"""
                    <div class="vp-metric g">
                        <div class="vp-metric-label">{lbl}</div>
                        <div class="vp-metric-val">{val}</div>
                        <div class="vp-metric-unit">{unit}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="font-family:'DM Mono',monospace;font-size:0.78rem;color:#8ab8a0;
                        margin-top:1rem;padding-top:1rem;border-top:1px solid #0f2a1a">
                Last charged: <span style="color:#e0ede8">{last_charged}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="font-family:'DM Mono',monospace;font-size:0.85rem;color:#3a6a4a;
                        padding:1rem 0;font-style:italic">
                No previous sessions found for this vehicle.
                History appears here after your first completed charge.
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # Tariff chart
    st.markdown('<div class="vp-section">', unsafe_allow_html=True)
    st.markdown("<div class='vp-section-title'>Today's tariff</div>", unsafe_allow_html=True)
    hours  = list(range(24))
    rates  = [TARIFF_SCHEDULE[h] for h in hours]
    colors = ["#2ecc71" if r <= 4.5 else "#ef4444" if r >= 9.0 else "#38bdf8" for r in rates]
    fig = go.Figure(go.Bar(
        x=[f"{h:02d}:00" for h in hours], y=rates,
        marker_color=colors,
        hovertemplate="<b>%{x}</b><br>₹%{y}/kWh<extra></extra>",
    ))
    fig.add_vline(x=datetime.now().hour, line_color="#f0faf4", line_width=1.5,
                  line_dash="dot", annotation_text="now",
                  annotation_font_color="#f0faf4", annotation_font_size=10)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=8,b=0), height=190,
        xaxis=dict(showgrid=False, tickfont=dict(color="#3a6a4a",size=9,family="DM Mono"),
                   tickangle=-45, linecolor="#0f2a1a"),
        yaxis=dict(showgrid=True, gridcolor="#0a2018",
                   tickfont=dict(color="#3a6a4a",size=9,family="DM Mono"), tickprefix="₹"),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("""
    <div style="display:flex;gap:1.4rem;font-family:'DM Mono',monospace;font-size:0.8rem;color:#8ab8a0;margin-top:0.3rem">
        <span><span style="color:#2ecc71">▮</span> Off-peak ≤ ₹4.5</span>
        <span><span style="color:#38bdf8">▮</span> Standard</span>
        <span><span style="color:#ef4444">▮</span> Peak ≥ ₹9.0</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="padding:1.2rem 2.5rem">', unsafe_allow_html=True)
    if st.button("↻  Refresh", key="ref_owner"):
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# ADMIN VIEW
# ════════════════════════════════════════════════════════════════

else:

    st.markdown("""
    <div class="vp-hero">
        <div class="vp-hero-tag">Station Admin</div>
        <div class="vp-hero-title">Control Centre</div>
        <div class="vp-hero-sub">Live load · Grid status · All sessions</div>
    </div>
    """, unsafe_allow_html=True)

    total_kw    = load_st.get("total_kw", 0)
    t_rating    = load_st.get("transformer_rating_kw", 25)
    util_pct    = load_st.get("utilisation_pct", 0)
    load_state  = load_st.get("state", "normal")
    grid_sig    = grid_st.get("grid_signal", 0)
    grid_state  = grid_st.get("grid_state", "unknown")
    imm_count   = len(immediate)
    sch_count   = len(sched_later)

    # Metrics
    st.markdown('<div class="vp-section">', unsafe_allow_html=True)
    st.markdown('<div class="vp-section-title">Station overview</div>', unsafe_allow_html=True)

    m1,m2,m3,m4,m5,m6 = st.columns(6)
    util_cls   = "r" if util_pct > 80 else "a" if util_pct > 60 else "g"
    grid_cls   = "r" if grid_sig < 55 else "a" if grid_sig < 70 else "g"

    for col, label, val, unit, cls in [
        (m1, "Total load",    f"{total_kw}",  f"kW / {t_rating}kW",          util_cls),
        (m2, "Utilisation",   f"{util_pct}%", load_state.upper(),             util_cls),
        (m3, "Grid signal",   f"{grid_sig}",  grid_state.upper(),             grid_cls),
        (m4, "Total EVs",     f"{len(all_slots)}", "in queue",                "b"),
        (m5, "Charging now",  f"{imm_count}", "immediate",                    "g"),
        (m6, "Scheduled",     f"{sch_count}", "pending",                      ""),
    ]:
        with col:
            st.markdown(f"""
            <div class="vp-metric {cls}">
                <div class="vp-metric-label">{label}</div>
                <div class="vp-metric-val">{val}</div>
                <div class="vp-metric-unit">{unit}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Load bar
    st.markdown('<div class="vp-section">', unsafe_allow_html=True)
    st.markdown('<div class="vp-section-title">Transformer load</div>', unsafe_allow_html=True)
    fill   = min(util_pct, 100)
    bc     = "#ef4444" if fill > 80 else "#f59e0b" if fill > 60 else "#2ecc71"
    headroom = round(t_rating - total_kw, 1)
    st.markdown(f"""
    <div style="font-family:'DM Mono',monospace;font-size:0.78rem;color:#8ab8a0;
                display:flex;justify-content:space-between;margin-bottom:0.4rem">
        <span>0 kW</span>
        <span style="color:{bc};font-weight:500">{total_kw} kW active — {fill:.0f}% utilised</span>
        <span>{t_rating} kW max</span>
    </div>
    <div class="vp-bar-bg">
        <div class="vp-bar-fill" style="width:{fill}%;background:{bc}"></div>
    </div>
    <div style="font-family:'DM Mono',monospace;font-size:0.78rem;color:#8ab8a0;margin-top:0.4rem">
        {headroom} kW headroom · State: <span style="color:{bc}">{load_state.upper()}</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Charger cards
    st.markdown('<div class="vp-section">', unsafe_allow_html=True)
    st.markdown('<div class="vp-section-title">Live chargers</div>', unsafe_allow_html=True)
    ch1, ch2, ch3 = st.columns(3)
    for col, i in zip([ch1,ch2,ch3], [1,2,3]):
        info   = c_status.get(f"charger_{i}", {})
        status = info.get("status","available")
        ev     = info.get("ev_id") or "—"
        kw     = info.get("allowed_kw") or "—"
        upd    = info.get("updated_at","—")
        with col:
            st.markdown(f"""
            <div class="vp-charger {status}">
                <div class="vp-charger-num">Charger 0{i}</div>
                <div class="vp-charger-stat">{status.upper()}</div>
                <div class="vp-charger-ev">{ev}</div>
                <div class="vp-charger-foot">{kw} kW &nbsp;·&nbsp; {upd}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Schedule table
    st.markdown('<div class="vp-section">', unsafe_allow_html=True)
    st.markdown('<div class="vp-section-title">All sessions</div>', unsafe_allow_html=True)
    if all_slots:
        rows = ""
        for s in all_slots:
            ev    = s.get("EV_ID","—")
            ch    = s.get("Charger","—")
            st_   = fmt_time(s.get("Start_Time",""))
            en_   = fmt_time(s.get("End_Time",""))
            soc_  = s.get("SOC","—")
            kw_   = s.get("Effective_kW","—")
            kwh_  = s.get("Estimated_kWh","—")
            cost_ = s.get("Estimated_Cost_INR","—")
            band_ = s.get("Tariff_Band","standard").lower().replace("-","")
            ga_   = s.get("Grid_Action","full").lower()
            emg_  = s.get("Emergency", False)
            imm_  = any(x["EV_ID"] == ev for x in immediate)

            b_em  = '<span class="vp-badge b-em">EMERG</span> ' if emg_ else ""
            b_sl  = f'<span class="vp-badge {"b-now" if imm_ else "b-sch"}">{"NOW" if imm_ else "SCHED"}</span>'
            b_tf  = f'<span class="vp-badge {"b-op" if band_=="offpeak" else "b-pk" if band_=="peak" else "b-std"}">{"OFF-PK" if band_=="offpeak" else band_.upper()}</span>'
            b_gr  = f'<span class="vp-badge {"b-ok" if ga_=="full" else "b-thr" if ga_=="throttle" else "b-str"}">{ga_.upper()}</span>'
            end_col = "#3a6a4a"

            rows += f"""<tr>
                <td><span style="color:#f0faf4;font-weight:500">{ev}</span> {b_em}</td>
                <td>0{ch}</td>
                <td style="color:#2ecc71">{st_}</td>
                <td style="color:{end_col}">{en_}</td>
                <td>{soc_}%</td>
                <td>{kw_} kW</td>
                <td>{kwh_} kWh</td>
                <td style="color:#2ecc71">₹{cost_}</td>
                <td>{b_tf}</td>
                <td>{b_gr}</td>
                <td>{b_sl}</td>
            </tr>"""

        st.markdown(f"""
        <div style="background:#080f0f;border:1px solid #0f2a1a;border-radius:12px;overflow:auto">
            <table class="vp-tbl">
                <thead><tr>
                    <th>Vehicle</th><th>Charger</th><th>Start</th><th>End</th>
                    <th>SOC</th><th>Power</th><th>Energy</th><th>Cost</th>
                    <th>Tariff</th><th>Grid</th><th>Status</th>
                </tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No data — run scheduler_v2.py first.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Charts
    st.markdown('<div class="vp-section">', unsafe_allow_html=True)
    st.markdown('<div class="vp-section-title">Energy & cost</div>', unsafe_allow_html=True)
    if all_slots:
        cc1, cc2 = st.columns(2)
        ev_labels = [s["EV_ID"] for s in all_slots]
        with cc1:
            fig1 = go.Figure(go.Bar(
                x=ev_labels, y=[s.get("Estimated_kWh",0) for s in all_slots],
                marker_color="#2ecc71", marker_line_width=0,
                hovertemplate="<b>%{x}</b><br>%{y} kWh<extra></extra>",
            ))
            fig1.update_layout(
                title=dict(text="energy per vehicle (kWh)", font=dict(color="#3a6a4a",size=11,family="DM Mono"), x=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=36,b=0), height=210,
                xaxis=dict(showgrid=False, tickfont=dict(color="#3a6a4a",size=10,family="DM Mono"), linecolor="#0f2a1a"),
                yaxis=dict(showgrid=True, gridcolor="#0a2018", tickfont=dict(color="#3a6a4a",size=10,family="DM Mono"), ticksuffix=" kWh"),
                showlegend=False,
            )
            st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar":False})
        with cc2:
            fig2 = go.Figure(go.Bar(
                x=ev_labels, y=[s.get("Estimated_Cost_INR",0) for s in all_slots],
                marker_color=[tariff_col(s.get("Tariff_Band","standard")) for s in all_slots],
                marker_line_width=0,
                hovertemplate="<b>%{x}</b><br>₹%{y}<extra></extra>",
            ))
            fig2.update_layout(
                title=dict(text="cost per vehicle (INR)", font=dict(color="#3a6a4a",size=11,family="DM Mono"), x=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=36,b=0), height=210,
                xaxis=dict(showgrid=False, tickfont=dict(color="#3a6a4a",size=10,family="DM Mono"), linecolor="#0f2a1a"),
                yaxis=dict(showgrid=True, gridcolor="#0a2018", tickfont=dict(color="#3a6a4a",size=10,family="DM Mono"), tickprefix="₹"),
                showlegend=False,
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})
    st.markdown('</div>', unsafe_allow_html=True)

    # Grid decisions
    st.markdown('<div class="vp-section">', unsafe_allow_html=True)
    st.markdown('<div class="vp-section-title">Grid decisions</div>', unsafe_allow_html=True)
    decisions = grid_st.get("decisions", [])
    if decisions:
        rows = ""
        for d in decisions:
            gc = grid_col(d.get("grid_signal",0))
            gs = d.get("grid_state","normal")
            ga = d.get("action","full")
            b_gs = f'<span class="vp-badge {"b-ok" if gs=="normal" else "b-str" if gs=="stressed" else "b-crt"}">{gs.upper()}</span>'
            rows += f"""<tr>
                <td style="color:#f0faf4;font-weight:500">{d.get('ev_id','—')}</td>
                <td style="color:{gc}">{d.get('grid_signal','—')}/100</td>
                <td>{b_gs}</td>
                <td>{d.get('allowed_kw','—')} kW</td>
                <td>{int(d.get('throttle_factor',1)*100)}%</td>
                <td style="color:#3a6a4a;font-size:0.72rem">{d.get('message','—')}</td>
            </tr>"""
        st.markdown(f"""
        <div style="background:#080f0f;border:1px solid #0f2a1a;border-radius:12px;overflow:auto">
            <table class="vp-tbl">
                <thead><tr><th>Vehicle</th><th>Signal</th><th>State</th><th>Allowed kW</th><th>Throttle</th><th>Message</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No grid data — run scheduler_v2.py first.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Refresh
    st.markdown('<div style="padding:1.2rem 2.5rem;display:flex;align-items:center;gap:1rem">', unsafe_allow_html=True)
    if st.button("↻  Refresh", key="ref_admin"):
        st.rerun()
    st.markdown(f'<span style="font-family:DM Mono,monospace;font-size:0.78rem;color:#8ab8a0">Last fetched: {now_str}</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)