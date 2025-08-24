# rfs_calculator_app_mano_updates_v2.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime

# ---- Plotly guard (clear message if missing on Cloud) ----
try:
    import plotly.express as px
except ModuleNotFoundError:
    st.error("Plotly isn’t installed. Add `plotly==6.3.0` to requirements.txt and Restart the app.")
    st.stop()

# ======================= Branding =======================
MANO_BLUE = "#1b6a87"
MANO_OFFWHITE = "#f4f6f6"
MANO_GREY = "#24333b"
FITOUT_COLOR = "#DECADE"   # requested color
L3_COLOR = "#F34213"
L4_COLOR = "#F6AE2D"
L5_COLOR = "#8AAA79"

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
st.set_page_config(page_title="Mano RFS Calculator", layout="wide")
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

# ======================= Holiday helpers (multi-country + Easter) =======================
def easter_date(year):
    # Anonymous Gregorian algorithm
    a = year % 19
    b = year // 100; c = year % 100
    d = b // 4; e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19*a + b - d - g + 15) % 30
    i = c // 4; k = c % 4
    l = (32 + 2*e + 2*i - h - k) % 7
    m = (a + 11*h + 22*l) // 451
    month = (h + l - 7*m + 114) // 31
    day = ((h + l - 7*m + 114) % 31) + 1
    return date(year, month, day)

def holidays_us(year):
    # Observed US Federal holidays
    def nth_weekday_of_month(month, weekday, n):
        import calendar
        c = calendar.Calendar()
        days = [d for d in c.itermonthdates(year, month) if d.weekday() == weekday and d.month == month]
        return days[-1] if n == -1 else days[n-1]
    def observed(d):
        if d.weekday()==5: return {d, d - timedelta(days=1)}
        if d.weekday()==6: return {d, d + timedelta(days=1)}
        return {d}
    hs = set()
    hs |= observed(date(year,1,1))
    hs.add(nth_weekday_of_month(1,0,3))
    hs.add(nth_weekday_of_month(2,0,3))
    hs.add(nth_weekday_of_month(5,0,-1))
    hs |= observed(date(year,6,19))
    hs |= observed(date(year,7,4))
    hs.add(nth_weekday_of_month(9,0,1))
    hs.add(nth_weekday_of_month(10,0,2))
    hs |= observed(date(year,11,11))
    hs.add(nth_weekday_of_month(11,3,4))
    hs |= observed(date(year,12,25))
    return hs

def holidays_mexico(year):
    # Main federal holidays (Ley Federal del Trabajo)
    def nth_weekday_of_month(month, weekday, n):
        import calendar
        c = calendar.Calendar()
        days = [d for d in c.itermonthdates(year, month) if d.weekday() == weekday and d.month == month]
        return days[n-1]
    hs = set()
    hs.add(date(year,1,1))  # Año Nuevo
    hs.add(nth_weekday_of_month(2,0,1))  # Día de la Constitución (1st Monday Feb)
    hs.add(nth_weekday_of_month(3,0,3))  # Natalicio Benito Juárez (3rd Monday Mar)
    hs.add(date(year,5,1))  # Día del Trabajo
    hs.add(date(year,9,16)) # Independencia
    hs.add(nth_weekday_of_month(11,0,3)) # Revolución (3rd Monday Nov)
    hs.add(date(year,12,25)) # Navidad
    return hs

def holidays_uk(year):
    # England & Wales common bank holidays (approx.)
    import calendar
    def first_monday(month):
        for d in range(1,8):
            dt = date(year,month,d)
            if dt.weekday()==0: return dt
    def last_monday(month):
        last_day = calendar.monthrange(year,month)[1]
        for d in range(last_day, last_day-7, -1):
            dt = date(year,month,d)
            if dt.weekday()==0: return dt
    hs = set()
    # New Year (observed)
    ny = date(year,1,1)
    if ny.weekday()==5: hs |= {ny, ny - timedelta(days=1)}
    elif ny.weekday()==6: hs |= {ny, ny + timedelta(days=1)}
    else: hs.add(ny)
    # Good Friday & Easter Monday
    easter = easter_date(year)
    hs.add(easter - timedelta(days=2))
    hs.add(easter + timedelta(days=1))
    # Early May bank holiday (first Monday May)
    hs.add(first_monday(5))
    # Spring bank (last Monday May)
    hs.add(last_monday(5))
    # Summer bank (last Monday August)
    hs.add(last_monday(8))
    # Christmas & Boxing Day (observed)
    xmas = date(year,12,25); box = date(year,12,26)
    for d in (xmas, box):
        if d.weekday()==5: hs |= {d, d - timedelta(days=1)}
        elif d.weekday()==6: hs |= {d, d + timedelta(days=1)}
        else: hs.add(d)
    return hs

def holidays_italy(year):
    # National holidays (approx.; includes Easter Monday)
    hs = {
        date(year,1,1),   # New Year
        date(year,1,6),   # Epiphany
        date(year,4,25),  # Liberation Day
        date(year,5,1),   # Labour Day
        date(year,6,2),   # Republic Day
        date(year,8,15),  # Assumption
        date(year,11,1),  # All Saints
        date(year,12,8),  # Immaculate Conception
        date(year,12,25), # Christmas
        date(year,12,26), # St. Stephen
    }
    hs.add(easter_date(year) + timedelta(days=1))  # Easter Monday
    return hs

def holidays_spain(year):
    # National holidays (approx.; includes Good Friday)
    hs = {
        date(year,1,1),   # Año Nuevo
        date(year,1,6),   # Epifanía
        date(year,8,15),  # Asunción
        date(year,10,12), # Fiesta Nacional
        date(year,11,1),  # Todos los Santos
        date(year,12,6),  # Constitución
        date(year,12,8),  # Inmaculada
        date(year,12,25), # Navidad
    }
    hs.add(easter_date(year) - timedelta(days=2))  # Good Friday
    return hs

def expand_holidays(country: str, years):
    hs = set()
    for y in years:
        if country == "United States":
            hs |= holidays_us(y)
        elif country == "Mexico":
            hs |= holidays_mexico(y)
        elif country == "United Kingdom":
            hs |= holidays_uk(y)
        elif country == "Italy":
            hs |= holidays_italy(y)
        elif country == "Spain":
            hs |= holidays_spain(y)
        else:
            hs |= holidays_us(y)
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
    st.header("Calendar")
    # No per-year control; just choose a standard holiday calendar.
    country = st.selectbox("Holiday Calendar", ["United States","Mexico","United Kingdom","Italy","Spain"], index=0)
    st.caption("Calendar utilizes standard public holidays for the selected country.")
    six_day_construction = st.checkbox("Use 6‑day workweek for construction activities", value=False)

    st.divider()
    st.header("Presets")
    preset = st.selectbox("Durations Preset", ["Typical", "Aggressive (-10%)", "Conservative (+15%)"])

    st.divider()
    st.header("Gate Dates")
    base_building_name = st.text_input("Base Building Name", value="Building")
    today_year = date.today().year
    ntp = st.date_input("Notice to Proceed", value=date(today_year, 1, 15))
    ldp = st.date_input("Land Disturbance Permit", value=date(today_year, 2, 1))
    bp  = st.date_input("Building Permit", value=date(today_year, 5, 1))
    perm_power = st.date_input("Permanent Power Delivery", value=date(today_year, 12, 1))
    temp_power_allowed = st.checkbox("Allow L3/L4 on Temporary Power", value=False)
    temp_power_date = st.date_input("Temporary Power Available", value=None, disabled=not temp_power_allowed)

    st.divider()
    st.header("Buildings")
    num_buildings = st.number_input("Number of Buildings", min_value=1, max_value=10, value=2, step=1)
    building_offset = st.number_input("Offset between buildings (days)", min_value=0, max_value=3650, value=90, step=5)

    # Per-building config editor: Name, Halls, MW — defaults prefilled
    default_rows = []
    for i in range(1, int(num_buildings)+1):
        default_rows.append({"Building Name": f"{base_building_name} {i}", "Halls": 4, "MW (total)": 24.0})
    st.caption("Edit buildings individually (name, # halls, total MW).")
    build_df = st.data_editor(pd.DataFrame(default_rows), num_rows="dynamic", use_container_width=True)

    st.divider()
    st.header("Durations (working days)")
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

    # Reset
    if st.button("Reset to Defaults"):
        st.session_state.clear()
        st.rerun()

# Determine a broad year range for holidays automatically (no UI)
max_year = 2040
min_year = min(ntp.year, ldp.year, bp.year)
years = list(range(min_year, max_year+1))
HOLIDAYS = expand_holidays(country, years)

# ======================= Scheduling per building =======================
WW_CONST = 6 if six_day_construction else 5
WW_ADMIN = 5

def schedule_building(build_idx:int, row):
    bname = str(row["Building Name"])
    halls_count = int(row["Halls"])
    total_mw = float(row["MW (total)"]) if pd.notna(row["MW (total)"]) else 0.0
    mw_per_hall = total_mw / halls_count if halls_count > 0 else 0

    offset = (build_idx-1) * int(building_offset)
    gates = {
        "ntp": ntp + timedelta(days=offset),
        "ldp": ldp + timedelta(days=offset),
        "bp": bp + timedelta(days=offset),
        "perm_power": perm_power + timedelta(days=offset),
        "temp_power": (temp_power_date + timedelta(days=offset)) if (temp_power_allowed and temp_power_date) else None,
    }

    civil_start = max(gates["ntp"], gates["ldp"])
    civil_finish = add_workdays(civil_start, site_work, HOLIDAYS, workdays_per_week=WW_CONST)
    cs_start = max(civil_finish, gates["bp"])
    cs_finish = add_workdays(cs_start, coreshell, HOLIDAYS, workdays_per_week=WW_CONST)
    core_shell_complete = cs_finish
    dryin_wd = max(1, int(round(coreshell * (dryin_pct/100.0))))
    dryin_date = add_workdays(cs_start, dryin_wd, HOLIDAYS, workdays_per_week=WW_CONST)

    hall1_earliest = core_shell_complete + timedelta(days=15)
    spacer = 90  # default per your preference; we still expose Fitout duration above
    cap_parallel = 10**6  # no explicit cap here; can add later if you want

    def commissioning_power_gate():
        return gates["temp_power"] if (temp_power_allowed and gates["temp_power"]) else gates["perm_power"]

    def schedule_one_hall(start_candidate):
        fitout_start = max(start_candidate, core_shell_complete)
        fitout_finish = add_workdays(fitout_start, fitout, HOLIDAYS, workdays_per_week=WW_CONST)
        pwr_gate_L34 = commissioning_power_gate()
        L3_start = max(fitout_finish, pwr_gate_L34)
        L3_finish = add_workdays(L3_start, L3d, HOLIDAYS, workdays_per_week=WW_CONST)
        L4_start = L3_finish
        L4_finish = add_workdays(L4_start, L4d, HOLIDAYS, workdays_per_week=WW_CONST)
        L5_start = max(L4_finish, gates["perm_power"])
        L5_finish = add_workdays(L5_start, L5d, HOLIDAYS, workdays_per_week=WW_CONST)
        return dict(FitoutStart=fitout_start, FitoutFinish=fitout_finish,
                    L3Start=L3_start, L3Finish=L3_finish,
                    L4Start=L4_start, L4Finish=L4_finish,
                    L5Start=L5_start, L5Finish=L5_finish, RFS=L5_finish)

    halls = []
    active = []
    for idx in range(1, halls_count+1):
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
        halls_count=halls_count,
        mw_per_hall=mw_per_hall,
        civil_start=civil_start, civil_finish=civil_finish,
        cs_start=cs_start, cs_finish=cs_finish,
        core_shell_complete=core_shell_complete,
        dryin_date=dryin_date, perm_power=gates["perm_power"],
        halls=halls
    )

# Build schedules
build_df = build_df.fillna({"Halls":4, "MW (total)":24.0})
buildings = []
for i in range(len(build_df)):
    buildings.append(schedule_building(i+1, build_df.iloc[i]))

# ======================= Procurement model (submittals + mfg + shipping) =======================
def modeled_equipment_rows_for_building(b):
    rows = []
    for item in RAW_EQUIPMENT:
        po = to_date(item.get("PO"))
        fab = to_date(item.get("FabStart"))
        ship = to_date(item.get("ExpectedShip"))
        delivered = to_date(item.get("Delivered"))

        submittals_wd = workdays_between(po, fab, ww=WW_ADMIN, holidays=HOLIDAYS) if po and fab else None
        if submittals_wd is None: submittals_wd = 20
        submittals_wd = max(15, min(submittals_wd, 45))

        mfg_wd = workdays_between(fab, ship, ww=WW_ADMIN, holidays=HOLIDAYS) if fab and ship else None
        ship_wd = workdays_between(ship, delivered, ww=WW_ADMIN, holidays=HOLIDAYS) if ship and delivered else 15

        arrival = None
        if po:
            arrival = add_workdays(po, submittals_wd, HOLIDAYS, workdays_per_week=WW_ADMIN)
            if mfg_wd: arrival = add_workdays(arrival, mfg_wd, HOLIDAYS, workdays_per_week=WW_ADMIN)
            if ship_wd: arrival = add_workdays(arrival, ship_wd, HOLIDAYS, workdays_per_week=WW_ADMIN)

        buf = int(item["buffer_wd_before_L3"])
        if item["scope"] == "house":
            anchor = b["halls"][0]["L3Start"]
            ideal = add_workdays(anchor, -buf, HOLIDAYS, workdays_per_week=WW_ADMIN)
            roj = clamp(ideal, b["dryin_date"], None)
            total_wd = (submittals_wd or 0) + (mfg_wd or 0) + (ship_wd or 0)
            release = add_workdays(roj, -total_wd, HOLIDAYS, workdays_per_week=WW_ADMIN) if roj else None
            rows.append({
                "Building Name": b["building_name"],
                "Equipment": item["Equipment"],
                "Location": "House",
                "Required Release/PO": release
                "Submittals (days)": submittals_wd,
                "Manufacturing (days)": mfg_wd,
                "Shipping (days)": ship_wd,
                "Site Acceptance": arrival,
                "ROJ": roj,

            })
        else:
            for i, h in enumerate(b["halls"], start=1):
                ideal = add_workdays(h["L3Start"], -buf, HOLIDAYS, workdays_per_week=WW_ADMIN)
                roj_h = clamp(ideal, h["FitoutStart"], h["FitoutFinish"])
                total_wd = (submittals_wd or 0) + (mfg_wd or 0) + (ship_wd or 0)
                release_h = add_workdays(roj_h, -total_wd, HOLIDAYS, workdays_per_week=WW_ADMIN) if roj_h else None
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
st.title("Mano RFS Calculator")

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

    st.subheader("Data Hall RFS (All Buildings)")
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
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(plot_bgcolor=MANO_OFFWHITE, paper_bgcolor=MANO_OFFWHITE, font_family="Raleway",
                      legend_title_text="Phase")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Equipment List")
    st.dataframe(EQUIP_DF, hide_index=True, use_container_width=True)
    st.download_button("Download Equipment (CSV)", EQUIP_DF.to_csv(index=False).encode("utf-8"), "equipment_roj.csv", "text/csv")

st.markdown('<p class="small-muted">Calendar uses the selected country’s standard public holidays • Civil waits for Notice to Proceed & Land Disturbance Permit • Vertical waits for Building Permit • L3/L4 may use Temporary Power • L5 waits for Permanent Power • House equipment ≥ Dry‑In; Hall equipment during Fitout.</p>', unsafe_allow_html=True)
