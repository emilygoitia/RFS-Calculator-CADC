# rfs_calculator_app_mano_v4.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime

# ---- Hard block if plotly isn't installed (so the message is clear on Cloud) ----
try:
    import plotly.express as px
except ModuleNotFoundError:
    st.error("Plotly isn’t installed on this deployment. Add `plotly==5.20.0` to requirements.txt (pinned) and Restart the app.")
    st.stop()

# ======================= Branding =======================
MANO_BLUE = "#1b6a87"
MANO_OFFWHITE = "#f4f6f6"
MANO_GREY = "#24333b"
FITOUT_COLOR = "#DECADE"   # requested color
L3_COLOR = "#88D18A"
L4_COLOR = "#FFBC24"
L5_COLOR = "#F75C03"

BRAND_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Raleway:wght@300;400;500;600;700&display=swap');
:root {{
  --mano-blue: {MANO_BLUE};
  --mano-offwhite: {MANO_OFFWHITE};
  --mano-grey: {MANO_GREY};
}}
html, body, [class*="css"]  {{ font-family: 'Raleway', sans-serif; }}
.stApp {{ background: var(--mano-offwhite); }}
h1, h2, h3, h4, h5, h6 {{ color: var(--mano-grey); font-weight: 600; }}
.block-container {{ padding-top: 1.0rem; }}
section[data-testid="stSidebar"] > div {{ background: white; border-right: 4px solid var(--mano-blue); }}
.stButton>button, .stDownloadButton>button {{
  background: var(--mano-blue); color: white; border: 0; border-radius: 12px; padding: .5rem 1rem;
}}
.dataframe tbody tr:nth-child(even) {{ background: rgba(27,106,135,0.05); }}
.small-muted {{ color: #5c6b73; font-size: 0.875rem; }}
.kpi-card {{
  background: white; border-radius: 16px; padding: 16px;
  border-left: 6px solid var(--mano-blue); box-shadow: 0 2px 10px rgba(0,0,0,0.05);
}}
</style>
"""
st.set_page_config(page_title="Mano RFS Calculator", layout="wide", page_icon="📦")
st.markdown(BRAND_CSS, unsafe_allow_html=True)

# ======================= Built-in Equipment (from your table) =======================
RAW_EQUIPMENT = [
    {"Equipment":"Air Cooled Chiller",               "scope":"house", "PO":"10/1/2025",  "FabStart":"10/23/2025", "ExpectedShip":"4/30/2026", "Delivered":"5/20/2026", "buffer_wd_before_L3":30},
    {"Equipment":"Computer Room Air Conditioner",    "scope":"hall",  "PO":"8/11/2025",  "FabStart":"9/1/2025",  "ExpectedShip":"3/23/2026", "Delivered":"4/13/2026", "buffer_wd_before_L3":15},
    {"Equipment":"Generator",                        "scope":"house", "PO":"2/14/2025",  "FabStart":"6/13/2025", "ExpectedShip":"4/28/2026", "Delivered":"5/18/2026", "buffer_wd_before_L3":30},
    {"Equipment":"Main Switchboard",                 "scope":"house", "PO":"8/4/2025",   "FabStart":"8/25/2025", "ExpectedShip":"2/23/2026", "Delivered":"3/16/2026", "buffer_wd_before_L3":30},
    {"Equipment":"Maintenance Bypass Board",         "scope":"house", "PO":"8/4/2025",   "FabStart":"8/25/2025", "ExpectedShip":"3/2/2026",  "Delivered":"3/23/2026", "buffer_wd_before_L3":30},
    {"Equipment":"Mechanical Panels",                "scope":"house", "PO":"9/2/2025",   "FabStart":"9/23/2025", "ExpectedShip":"6/23/2026", "Delivered":"7/14/2026", "buffer_wd_before_L3":30},
    {"Equipment":"Modular Electrical Room",          "scope":"house", "PO":"8/11/2025",  "FabStart":"11/10/2025","ExpectedShip":"7/21/2026", "Delivered":"7/27/2026", "buffer_wd_before_L3":30},
    {"Equipment":"Padmount Transformer",             "scope":"house", "PO":"6/17/2025",  "FabStart":"7/8/2025",  "ExpectedShip":"12/9/2025", "Delivered":"1/20/2026", "buffer_wd_before_L3":30},
    {"Equipment":"Power Distribution Unit",          "scope":"hall",  "PO":"8/11/2025",  "FabStart":"9/1/2025",  "ExpectedShip":"6/29/2026", "Delivered":"7/20/2026", "buffer_wd_before_L3":15},
    {"Equipment":"Static Transfer Switch",           "scope":"hall",  "PO":"8/11/2025",  "FabStart":"9/1/2025",  "ExpectedShip":"5/4/2026",  "Delivered":"5/25/2026", "buffer_wd_before_L3":15},
    {"Equipment":"Uninterruptible Power Supply",     "scope":"hall",  "PO":"8/11/2025",  "FabStart":"9/1/2025",  "ExpectedShip":"6/16/2026", "Delivered":"6/30/2026", "buffer_wd_before_L3":15},
    {"Equipment":"UPS Battery Cabinet",              "scope":"hall",  "PO":"8/12/2025",  "FabStart":"9/2/2025",  "ExpectedShip":"3/31/2026", "Delivered":"4/14/2026", "buffer_wd_before_L3":15},
    {"Equipment":"UPS Board",                        "scope":"hall",  "PO":"8/4/2025",   "FabStart":"8/25/2025", "ExpectedShip":"3/16/2026", "Delivered":"4/6/2026",  "buffer_wd_before_L3":15},
    {"Equipment":"UPS Board Reserve",                "scope":"hall",  "PO":"8/4/2025",   "FabStart":"8/25/2025", "ExpectedShip":"3/16/2026", "Delivered":"4/6/2026",  "buffer_wd_before_L3":15},
]

# ======================= Holiday / Workday helpers =======================
def nth_weekday_of_month(year, month, weekday, n):
    import calendar
    c = calendar.Calendar()
    days = [d for d in c.itermonthdates(year, month) if d.weekday() == weekday and d.month == month]
    return days[-1] if n == -1 else days[n-1]

def us_federal_holidays(year):
    import datetime as dt
    holidays = set()
    def observed(month, day):
        d = dt.date(year, month, day)
        if d.weekday() == 5:   # Sat
            return {d, d - dt.timedelta(days=1)}
        elif d.weekday() == 6: # Sun
            return {d, d + dt.timedelta(days=1)}
        return {d}
    holidays |= observed(1, 1)
    holidays.add(nth_weekday_of_month(year, 1, 0, 3))
    holidays.add(nth_weekday_of_month(year, 2, 0, 3))
    holidays.add(nth_weekday_of_month(year, 5, 0, -1))
    holidays |= observed(6, 19)
    holidays |= observed(7, 4)
    holidays.add(nth_weekday_of_month(year, 9, 0, 1))
    holidays.add(nth_weekday_of_month(year,10, 0, 2))
    holidays |= observed(11,11)
    holidays.add(nth_weekday_of_month(year,11, 3, 4))
    holidays |= observed(12,25)
    return holidays

def expand_holidays(years):
    hs = set()
    for y in years: hs |= us_federal_holidays(y)
    return hs

def add_workdays(start_date, duration_days, holidays, workdays_per_week=5):
    if start_date is None or duration_days == 0: return start_date
    d = start_date
    step = 1 if duration_days > 0 else -1
    remaining = abs(int(duration_days))
    while remaining > 0:
        d += timedelta(days=step)
        dow = d.weekday()
        is_weekend = (dow == 6) or (dow == 5 and workdays_per_week == 5)
        if is_weekend or d in holidays: continue
        remaining -= 1
    return d

def to_date(x):
    if not x: return None
    try: return pd.to_datetime(x).date()
    except: return None

def workdays_between(d1, d2, ww=5, holidays=set()):
    if d1 is None or d2 is None: return None
    days = 0
    step = 1 if d2 >= d1 else -1
    d = d1
    while d != d2:
        d += timedelta(days=step)
        dow = d.weekday()
        is_weekend = (dow == 6) or (dow == 5 and ww == 5)
        if not is_weekend and d not in holidays:
            days += 1 if step > 0 else -1
    return days

def clamp(d, lo, hi):
    if d is None: return None
    if lo and d < lo: d = lo
    if hi and d > hi: d = hi
    return d

# ======================= Sidebar (Inputs) =======================
with st.sidebar:
    st.header("Calendar & Work Week")
    this_year = date.today().year
    year_choices = list(range(this_year, 2041))  # through 2040
    years = st.multiselect("Holiday Years Included", year_choices, default=year_choices)
    holidays = expand_holidays(years)
    six_day_construction = st.checkbox("Use 6‑day workweek for construction activities", value=False)

    st.divider()
    st.header("Presets")
    preset = st.selectbox("Durations Preset", ["Typical", "Aggressive (-10%)", "Conservative (+15%)"])

    st.divider()
    st.header("Gate Dates")
    base_building_name = st.text_input("Base Building Name", value="Building")
    ntp = st.date_input("Notice to Proceed", value=date(this_year, 1, 15))
    ldp = st.date_input("Land Disturbance Permit", value=date(this_year, 2, 1))
    bp  = st.date_input("Building Permit", value=date(this_year, 5, 1))
    perm_power = st.date_input("Permanent Power Delivery", value=date(this_year, 12, 1))
    temp_power_allowed = st.checkbox("Allow L3/L4 on Temporary Power", value=False)
    temp_power_date = st.date_input("Temporary Power Available", value=None, disabled=not temp_power_allowed)

    st.divider()
    st.header("Buildings")
    num_buildings = st.number_input("Number of Buildings", min_value=1, max_value=10, value=2, step=1)
    building_offset = st.number_input("Offset between buildings (days)", min_value=0, max_value=3650, value=90, step=5)

    st.divider()
    st.header("Halls & Capacity")
    building_mw = st.number_input("Building MW (each building)", min_value=1.0, value=24.0, step=1.0)
    num_halls = st.number_input("Number of Data Halls (each building)", min_value=1, max_value=50, value=4, step=1)
    max_parallel = st.number_input("Max halls in parallel", min_value=0, max_value=50, value=0, step=1,
                                   help="0 means no limit.")
    cadence_days = st.number_input("Spacing Between Data Halls (days)", min_value=0, max_value=365, value=90)

    st.divider()
    st.header("Durations (working days)")
    # Base defaults
    site_work = 60; coreshell = 160; fitout = 60; L3d = 40; L4d = 10; L5d = 3
    scale = {"Typical":1.0, "Aggressive (-10%)":0.9, "Conservative (+15%)":1.15}[preset]
    site_work = int(round(site_work*scale)); coreshell = int(round(coreshell*scale))
    fitout = int(round(fitout*scale)); L3d = int(round(L3d*scale)); L4d = int(round(L4d*scale)); L5d = max(1,int(round(L5d*scale)))
    site_work = st.slider("Site Work", 40, 180, site_work)
    coreshell = st.slider("Core & Shell", 60, 300, coreshell)
    dryin_pct = st.slider("Dry‑In point within Core & Shell (%)", 10, 90, 60,
                          help="Dry‑In is the earliest allowed set for house equipment.")
    fitout = st.slider("Hall Fitout", 20, 200, fitout)
    L3d = st.slider("Commissioning L3", 5, 90, L3d)
    L4d = st.slider("Commissioning L4", 5, 60, L4d)
    L5d = st.slider("Commissioning L5", 1, 30, L5d)

    if st.button("Reset to Defaults"):
        st.session_state.clear()
        st.rerun()

# ======================= Scheduling per building =======================
WW_CONST = 6 if six_day_construction else 5
WW_ADMIN = 5
mw_per_hall = building_mw / num_halls

def schedule_building(build_idx:int):
    bname = f"{base_building_name} {build_idx}"
    offset = (build_idx-1) * int(building_offset)
    gates = {
        "ntp": ntp + timedelta(days=offset),
        "ldp": ldp + timedelta(days=offset),
        "bp": bp + timedelta(days=offset),
        "perm_power": perm_power + timedelta(days=offset),
        "temp_power": (temp_power_date + timedelta(days=offset)) if (temp_power_allowed and temp_power_date) else None,
    }

    civil_start = max(gates["ntp"], gates["ldp"])
    civil_finish = add_workdays(civil_start, site_work, holidays, workdays_per_week=WW_CONST)
    cs_start = max(civil_finish, gates["bp"])
    cs_finish = add_workdays(cs_start, coreshell, holidays, workdays_per_week=WW_CONST)
    core_shell_complete = cs_finish
    dryin_wd = max(1, int(round(coreshell * (dryin_pct/100.0))))
    dryin_date = add_workdays(cs_start, dryin_wd, holidays, workdays_per_week=WW_CONST)

    hall1_earliest = core_shell_complete + timedelta(days=15)
    spacer = int(cadence_days) if cadence_days > 0 else 60
    cap_parallel = int(max_parallel) if int(max_parallel) > 0 else 10**6

    def commissioning_power_gate():
        return gates["temp_power"] if (temp_power_allowed and gates["temp_power"]) else gates["perm_power"]

    def schedule_one_hall(start_candidate):
        fitout_start = max(start_candidate, core_shell_complete)
        fitout_finish = add_workdays(fitout_start, fitout, holidays, workdays_per_week=WW_CONST)
        pwr_gate_L34 = commissioning_power_gate()
        L3_start = max(fitout_finish, pwr_gate_L34)
        L3_finish = add_workdays(L3_start, L3d, holidays, workdays_per_week=WW_CONST)
        L4_start = L3_finish
        L4_finish = add_workdays(L4_start, L4d, holidays, workdays_per_week=WW_CONST)
        L5_start = max(L4_finish, gates["perm_power"])
        L5_finish = add_workdays(L5_start, L5d, holidays, workdays_per_week=WW_CONST)
        return dict(FitoutStart=fitout_start, FitoutFinish=fitout_finish,
                    L3Start=L3_start, L3Finish=L3_finish,
                    L4Start=L4_start, L4Finish=L4_finish,
                    L5Start=L5_start, L5Finish=L5_finish, RFS=L5_finish)

    halls = []
    active = []
    for idx in range(1, int(num_halls)+1):
        candidate = hall1_earliest if idx == 1 else halls[-1]["FitoutStart"] + timedelta(days=spacer)
        def in_progress(day): return [d for d in active if d > day]
        while len(in_progress(candidate)) >= cap_parallel:
            earliest_free = min(active)
            candidate = max(earliest_free + timedelta(days=1), halls[-1]["FitoutStart"] + timedelta(days=spacer) if idx>1 else candidate)
        h = schedule_one_hall(candidate)
        halls.append(h)
        active.append(h["RFS"])
        active = [d for d in active if d >= candidate]

    return dict(
        building_name=bname,
        civil_start=civil_start, civil_finish=civil_finish,
        cs_start=cs_start, cs_finish=cs_finish,
        core_shell_complete=core_shell_complete,
        dryin_date=dryin_date, perm_power=gates["perm_power"],
        halls=halls, mw_per_hall=mw_per_hall
    )

buildings = [schedule_building(i) for i in range(1, int(num_buildings)+1)]

# ======================= Procurement model (submittals + mfg + shipping) =======================
def modeled_equipment_rows_for_building(b):
    rows = []
    for item in RAW_EQUIPMENT:
        po = to_date(item.get("PO"))
        fab = to_date(item.get("FabStart"))
        ship = to_date(item.get("ExpectedShip"))
        delivered = to_date(item.get("Delivered"))

        submittals_wd = workdays_between(po, fab, ww=WW_ADMIN, holidays=holidays) if po and fab else None
        if submittals_wd is None: submittals_wd = 20       # default ~15–20wd, clamp 15–45
        submittals_wd = max(15, min(submittals_wd, 45))

        mfg_wd = workdays_between(fab, ship, ww=WW_ADMIN, holidays=holidays) if fab and ship else None
        ship_wd = workdays_between(ship, delivered, ww=WW_ADMIN, holidays=holidays) if ship and delivered else 15

        arrival = None
        if po:
            arrival = add_workdays(po, submittals_wd, holidays, workdays_per_week=WW_ADMIN)
            if mfg_wd: arrival = add_workdays(arrival, mfg_wd, holidays, workdays_per_week=WW_ADMIN)
            if ship_wd: arrival = add_workdays(arrival, ship_wd, holidays, workdays_per_week=WW_ADMIN)

        buf = int(item["buffer_wd_before_L3"])
        if item["scope"] == "house":
            anchor = b["halls"][0]["L3Start"]
            ideal = add_workdays(anchor, -buf, holidays, workdays_per_week=WW_ADMIN)
            roj = clamp(ideal, b["dryin_date"], None)
            total_wd = (submittals_wd or 0) + (mfg_wd or 0) + (ship_wd or 0)
            release = add_workdays(roj, -total_wd, holidays, workdays_per_week=WW_ADMIN) if roj else None
            rows.append({
                "Building Name": b["building_name"],
                "Equipment": item["Equipment"],
                "Scope": "House",
                "Submittals (wd)": submittals_wd,
                "Manufacturing (wd)": mfg_wd,
                "Shipping (wd)": ship_wd,
                "Modeled Arrival": arrival,
                "ROJ (predicted)": roj,
                "Release/PO (suggested)": release
            })
        else:
            for i, h in enumerate(b["halls"], start=1):
                ideal = add_workdays(h["L3Start"], -buf, holidays, workdays_per_week=WW_ADMIN)
                roj_h = clamp(ideal, h["FitoutStart"], h["FitoutFinish"])
                total_wd = (submittals_wd or 0) + (mfg_wd or 0) + (ship_wd or 0)
                release_h = add_workdays(roj_h, -total_wd, holidays, workdays_per_week=WW_ADMIN) if roj_h else None
                rows.append({
                    "Building Name": b["building_name"],
                    "Equipment": f'{item["Equipment"]} (Hall {i})',
                    "Scope": "Hall",
                    "Submittals (wd)": submittals_wd,
                    "Manufacturing (wd)": mfg_wd,
                    "Shipping (wd)": ship_wd,
                    "Modeled Arrival": arrival,
                    "ROJ (predicted)": roj_h,
                    "Release/PO (suggested)": release_h
                })
    return rows

equip_rows = []
for b in buildings:
    equip_rows.extend(modeled_equipment_rows_for_building(b))
EQUIP_DF = pd.DataFrame(equip_rows)

# ======================= UI =======================
st.title("📦 Mano RFS Calculator")

tab1, tab2, tab3 = st.tabs(["Results", "Timeline", "Equipment List"])

with tab1:
    st.subheader("Key Milestones per Building")
    for b in buildings:
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"""<div class="kpi-card"><div>{b['building_name']} — Civil Start</div>
                        <h4 style="margin:0;color:{MANO_BLUE}">{b['civil_start']:%b %d, %Y}</h4></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class="kpi-card"><div>{b['building_name']} — Dry‑In</div>
                        <h4 style="margin:0;color:{MANO_BLUE}">{b['dryin_date']:%b %d, %Y}</h4></div>""", unsafe_allow_html=True)
        c3.markdown(f"""<div class="kpi-card"><div>{b['building_name']} — Core & Shell Complete</div>
                        <h4 style="margin:0;color:{MANO_BLUE}">{b['core_shell_complete']:%b %d, %Y}</h4></div>""", unsafe_allow_html=True)
        c4.markdown(f"""<div class="kpi-card"><div>{b['building_name']} — Permanent Power</div>
                        <h4 style="margin:0;color:{MANO_BLUE}">{b['perm_power']:%b %d, %Y}</h4></div>""", unsafe_allow_html=True)

    st.subheader("Hall RFS (All Buildings)")
    rows = []
    for b in buildings:
        for j, h in enumerate(b["halls"], start=1):
            rows.append({
                "Building Name": b["building_name"],
                "Hall": j,
                "MW per Hall": round(b["mw_per_hall"],2),
                "Fitout Start": h["FitoutStart"],
                "Fitout Finish": h["FitoutFinish"],
                "L3 Start": h["L3Start"],
                "RFS (L5 Finish)": h["RFS"]
            })
    rfs_df = pd.DataFrame(rows)
    st.dataframe(rfs_df, hide_index=True, use_container_width=True)
    st.download_button("Download RFS (CSV)", rfs_df.to_csv(index=False).encode("utf-8"), "rfs_multi_building.csv", "text/csv")

with tab2:
    st.subheader("Timeline")
    gantt_rows = []
    for b in buildings:
        gantt_rows.append({"Task": f"{b['building_name']} • Core & Shell", "Start": b["cs_start"], "Finish": b["cs_finish"], "Phase":"Core&Shell"})
        for j, h in enumerate(b["halls"], start=1):
            gantt_rows += [
                {"Task": f"{b['building_name']} • Hall {j} • Fitout", "Start": h["FitoutStart"], "Finish": h["FitoutFinish"], "Phase":"Fitout"},
                {"Task": f"{b['building_name']} • Hall {j} • L3",     "Start": h["L3Start"],    "Finish": h["L3Finish"],   "Phase":"L3"},
                {"Task": f"{b['building_name']} • Hall {j} • L4",     "Start": h["L4Start"],    "Finish": h["L4Finish"],   "Phase":"L4"},
                {"Task": f"{b['building_name']} • Hall {j} • L5",     "Start": h["L5Start"],    "Finish": h["L5Finish"],   "Phase":"L5"},
            ]
    gdf = pd.DataFrame(gantt_rows)
    color_map = {
        "Core&Shell": MANO_BLUE,
        "Fitout": FITOUT_COLOR,
        "L3": L3_COLOR,
        "L4": L4_COLOR,
        "L5": L5_COLOR,
    }
    fig = px.timeline(gdf, x_start="Start", x_end="Finish", y="Task",
                      color="Phase", color_discrete_map=color_map, title="Project Timeline")
    fig.update_y
