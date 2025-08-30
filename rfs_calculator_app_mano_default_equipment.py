# rfs_calculator_app_mano_updates_v2.py
import streamlit as st
import pandas as pd

from components.chart import render_gantt
from components.card import render_kpi_card
from components.table import render_styled_table
from components.slider import render_styled_slider

import data.equipment as equipment

import utils.building as building
import utils.css as styling
import utils.date as date_utils
import utils.colors as colors

st.set_page_config(page_title="Mano RFS Calculator", layout="wide")
styling.inject_custom_css()
st.logo("./assets/images/Mano_Logo_Main.webp")


# ======================= Sidebar (Inputs) =======================
with st.sidebar:
    st.markdown("""
    <style>
        /* Force Streamlit containers to be fluid */
        [data-testid="element-container"] {
          max-width: 100% !important;
          width: 100% !important;
        }
        [data-testid="stSlider"] {
          max-width: 100% !important;
          width: 100% !important;
        }
        [data-testid="stVerticalBlock"] {
            max-width: 100% !important;
            width: 100% !important;
        }
        [data-testid="stHorizontalBlock"] {
            max-width: 100% !important;
            margin-bottom: 1rem;
        }
        [data-testid="stMarkdownContainer"] {
                display: flex;
                flex-direction: column;
        }
    </style>
""", unsafe_allow_html=True)
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
    today_year = date_utils.date.today().year
    ntp = st.date_input("Notice to Proceed", value=date_utils.date(today_year, 1, 15))
    ldp = st.date_input("Land Disturbance Permit", value=date_utils.date(today_year, 2, 1))
    bp  = st.date_input("Building Permit", value=date_utils.date(today_year, 5, 1))
    perm_power = st.date_input("Permanent Power Delivery", value=date_utils.date(today_year, 12, 1))
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
    build_df = st.data_editor(pd.DataFrame(default_rows), hide_index=True, num_rows="fixed", use_container_width=True)

    st.divider()
    st.header("Durations (working days)")
    site_work = 60; coreshell = 160; fitout = 60; L3d = 40; L4d = 10; L5d = 3
    scale = {"Typical":1.0, "Aggressive (-10%)":0.9, "Conservative (+15%)":1.15}[preset]
    site_work = int(round(site_work*scale)); coreshell = int(round(coreshell*scale))
    fitout = int(round(fitout*scale)); L3d = int(round(L3d*scale)); L4d = int(round(L4d*scale)); L5d = max(1,int(round(L5d*scale)))

    # Sliders
    site_work = render_styled_slider("Site Work", 40, 180, site_work)
    coreshell = render_styled_slider("Core & Shell", 60, 300, coreshell)
    dryin_pct = render_styled_slider("Dry‑In point within Core & Shell (%)", 10, 90, 60, "Dry‑In is the earliest allowed set for house equipment.")
    fitout = render_styled_slider("Hall Fitout", 20, 200, fitout)
    L3d = render_styled_slider("Commissioning L3", 5, 90, L3d)
    L4d = render_styled_slider("Commissioning L4", 5, 60, L4d)
    L5d = render_styled_slider("Commissioning L5", 1, 30, L5d)

    # Reset
    if st.button("Reset to Defaults"):
        st.session_state.clear()
        st.rerun()

# Determine a broad year range for holidays automatically (no UI)
max_year = 2040
min_year = min(ntp.year, ldp.year, bp.year)
years = list(range(min_year, max_year+1))
HOLIDAYS = date_utils.expand_holidays(country, years)

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
        "ntp": ntp + date_utils.timedelta(days=offset),
        "ldp": ldp + date_utils.timedelta(days=offset),
        "bp": bp + date_utils.timedelta(days=offset),
        "perm_power": perm_power + date_utils.timedelta(days=offset),
        "temp_power": (temp_power_date + date_utils.timedelta(days=offset)) if (temp_power_allowed and temp_power_date) else None,
    }

    civil_start = max(gates["ntp"], gates["ldp"])
    civil_finish = date_utils.add_workdays(civil_start, site_work, HOLIDAYS, workdays_per_week=WW_CONST)
    cs_start = max(civil_finish, gates["bp"])
    cs_finish = date_utils.add_workdays(cs_start, coreshell, HOLIDAYS, workdays_per_week=WW_CONST)
    core_shell_complete = cs_finish
    dryin_wd = max(1, int(round(coreshell * (dryin_pct/100.0))))
    dryin_date = date_utils.add_workdays(cs_start, dryin_wd, HOLIDAYS, workdays_per_week=WW_CONST)

    hall1_earliest = core_shell_complete + date_utils.timedelta(days=15)
    spacer = 90  # default per your preference; we still expose Fitout duration above
    cap_parallel = 10**6  # no explicit cap here; can add later if you want

    def commissioning_power_gate():
        return gates["temp_power"] if (temp_power_allowed and gates["temp_power"]) else gates["perm_power"]

    def schedule_one_hall(start_candidate):
        fitout_start = max(start_candidate, core_shell_complete)
        fitout_finish = date_utils.add_workdays(fitout_start, fitout, HOLIDAYS, workdays_per_week=WW_CONST)
        pwr_gate_L34 = commissioning_power_gate()
        L3_start = max(fitout_finish, pwr_gate_L34)
        L3_finish = date_utils.add_workdays(L3_start, L3d, HOLIDAYS, workdays_per_week=WW_CONST)
        L4_start = L3_finish
        L4_finish = date_utils.add_workdays(L4_start, L4d, HOLIDAYS, workdays_per_week=WW_CONST)
        L5_start = max(L4_finish, gates["perm_power"])
        L5_finish = date_utils.add_workdays(L5_start, L5d, HOLIDAYS, workdays_per_week=WW_CONST)
        return dict(FitoutStart=fitout_start, FitoutFinish=fitout_finish,
                    L3Start=L3_start, L3Finish=L3_finish,
                    L4Start=L4_start, L4Finish=L4_finish,
                    L5Start=L5_start, L5Finish=L5_finish, RFS=L5_finish)

    halls = []
    active = []
    for idx in range(1, halls_count+1):
        candidate = hall1_earliest if idx == 1 else halls[-1]["FitoutStart"] + date_utils.timedelta(days=spacer)
        def in_progress(day): return [d for d in active if d > day]
        while len(in_progress(candidate)) >= cap_parallel:
            earliest_free = min(active)
            candidate = max(earliest_free + date_utils.timedelta(days=1), halls[-1]["FitoutStart"] + date_utils.timedelta(days=spacer) if idx>1 else candidate)
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

equip_rows = []
for b in buildings:
    equip_rows.extend(building.get_modeled_equipment_rows(b, WW_ADMIN, HOLIDAYS))
EQUIP_DF = pd.DataFrame(equip_rows)

# ======================= UI =======================
st.title("RFS Calculator")
tab1, tab2, tab3 = st.tabs(["Results", "Timeline", "Equipment List"])

with tab1:
    st.subheader("Key Milestones per Building")
    for b in buildings:
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(render_kpi_card(b, "Civil Start", 'civil_start'), unsafe_allow_html=True)
        c2.markdown(render_kpi_card(b, "Dry‑In", 'dryin_date'), unsafe_allow_html=True)
        c3.markdown(render_kpi_card(b, "Core & Shell Complete", 'core_shell_complete'), unsafe_allow_html=True)
        c4.markdown(render_kpi_card(b, "Permanent Power", 'perm_power'), unsafe_allow_html=True)
    st.divider()
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

    render_styled_table(rfs_df)
    
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
    render_gantt(gdf)

with tab3:
    st.subheader("Equipment List")
    st.dataframe(EQUIP_DF, hide_index=True, use_container_width=True)
    st.download_button("Download Equipment (CSV)", EQUIP_DF.to_csv(index=False).encode("utf-8"), "equipment_roj.csv", "text/csv")

st.markdown('<p class="small-muted">Calendar uses the selected country’s standard public holidays • Civil waits for Notice to Proceed & Land Disturbance Permit • Vertical waits for Building Permit • L3/L4 may use Temporary Power • L5 waits for Permanent Power • House equipment ≥ Dry‑In; Hall equipment during Fitout.</p>', unsafe_allow_html=True)
