import math
from datetime import date, datetime

import utils.date as date_utils
import data.equipment as equipment


def _max_date(*dates):
    valid = [d for d in dates if d is not None]
    return max(valid) if valid else None


def _min_date(*dates):
    valid = [d for d in dates if d is not None]
    return min(valid) if valid else None


def _resolve_anchor_date(anchor, building, hall):
    if not anchor:
        return None
    anchor = anchor.lower()
    gates = building.get("gates", {}) if isinstance(building.get("gates"), dict) else {}

    if anchor == "ntp":
        return gates.get("ntp")
    if anchor == "ldp":
        return gates.get("ldp")
    if anchor == "bp":
        return gates.get("bp")
    if anchor in ("perm_power", "permanent_power"):
        return building.get("perm_power")
    if anchor == "dryin":
        return building.get("dryin_date")
    if anchor == "shell_start":
        return building.get("shell_start")
    if anchor == "shell_finish":
        return building.get("shell_finish")
    if anchor == "civil_start":
        return building.get("civil_start")
    if anchor == "mep_start":
        return building.get("mep_start")
    if anchor == "mep_finish":
        return building.get("mep_finish")
    if anchor in ("fitup_start", "hall_fit_start"):
        if hall:
            return hall.get("FitupStart")
        return building.get("halls", [{}])[0].get("FitupStart") if building.get("halls") else None
    if anchor in ("fitup_finish", "hall_fit_finish"):
        if hall:
            return hall.get("FitupFinish")
        return building.get("halls", [{}])[0].get("FitupFinish") if building.get("halls") else None
    if anchor in ("l3_start", "hall_l3_start"):
        if hall:
            return hall.get("L3Start")
        return building.get("halls", [{}])[0].get("L3Start") if building.get("halls") else None
    if anchor == "power_gate" and hall:
        return hall.get("PowerGate")
    if anchor == "power_delivery" and hall:
        return hall.get("PowerDeliveryDate")
    return None


def _add_offset(base, offset, holidays, ww):
    if base is None:
        return None
    if offset in (None, 0):
        return base
    return date_utils.add_workdays(base, int(offset), holidays, workdays_per_week=ww)


# ======================= Procurement model (lead time + back off) =======================
def _lead_time_weeks(lead_wd):
    if lead_wd <= 0:
        return 0
    return math.ceil(lead_wd / 5)


def _equipment_status(release_needed):
    if release_needed is None:
        return "On Track"

    if isinstance(release_needed, datetime):
        release_needed = release_needed.date()

    today = date.today()
    if release_needed < today:
        return "Overdue"
    if (release_needed - today).days <= 30:
        return "At Risk"
    return "On Track"


def _roj_status(site_accept, roj_target, roj):
    if not site_accept:
        return ""

    target = roj_target or roj
    if not target:
        return ""

    delta_days = (site_accept - target).days
    if delta_days <= 0:
        return "🟢"
    if delta_days <= 30:
        return "🟡"
    return "🔴"


def get_modeled_equipment_rows(b, ww, holidays):
    rows = []
    first_hall = b["halls"][0] if b.get("halls") else None

    for item in equipment.RAW_EQUIPMENT:
        lead_wd = int(item.get("lead_time_wd") or 0)
        buffer_wd = int(item.get("buffer_wd_before_L3") or 0)
        offset_wd = item.get("release_offset_wd")
        anchor_key = item.get("release_anchor")
        if item["scope"] == "house":
            anchor_date = _resolve_anchor_date(anchor_key, b, None)
            release_plan = _add_offset(anchor_date, offset_wd, holidays, ww)

            desired = None
            if first_hall and first_hall.get("L3Start"):
                ideal = first_hall["L3Start"]
                if buffer_wd:
                    ideal = date_utils.add_workdays(ideal, -buffer_wd, holidays, workdays_per_week=ww)
                desired = date_utils.clamp(ideal, b.get("dryin_date"), None)

            release_needed = date_utils.add_workdays(desired, -lead_wd, holidays, workdays_per_week=ww) if (desired and lead_wd) else None
            release_used = _min_date(release_plan, release_needed) if (release_plan or release_needed) else release_plan or release_needed
            site_accept = date_utils.add_workdays(release_used, lead_wd, holidays, workdays_per_week=ww) if (release_used and lead_wd) else release_used

            roj = desired
            if site_accept and (roj is None or site_accept > roj):
                roj = site_accept
            if roj and b.get("dryin_date") and roj < b["dryin_date"]:
                roj = b["dryin_date"]

            rows.append({
                "Building Name": b["building_name"],
                "Equipment": item["Equipment"],
                "Location": "House",
                "Release Plan": release_plan,
                "Release Needed": release_needed,
                "Status": _equipment_status(release_needed),
                "Lead Time (weeks)": _lead_time_weeks(lead_wd),
                "Site Acceptance": site_accept,
                "ROJ Target": desired,
                "ROJ": roj,
                "ROJ Status": _roj_status(site_accept, desired, roj),
            })
        else:
            for idx, hall in enumerate(b.get("halls", []), start=1):
                anchor_date = _resolve_anchor_date(anchor_key, b, hall)
                release_plan = _add_offset(anchor_date, offset_wd, holidays, ww)

                ideal = hall.get("L3Start")
                if ideal and buffer_wd:
                    ideal = date_utils.add_workdays(ideal, -buffer_wd, holidays, workdays_per_week=ww)
                desired = date_utils.clamp(ideal, hall.get("FitupStart"), hall.get("FitupFinish")) if ideal else None

                release_needed = date_utils.add_workdays(desired, -lead_wd, holidays, workdays_per_week=ww) if (desired and lead_wd) else None
                release_used = _min_date(release_plan, release_needed) if (release_plan or release_needed) else release_plan or release_needed
                site_accept = date_utils.add_workdays(release_used, lead_wd, holidays, workdays_per_week=ww) if (release_used and lead_wd) else release_used

                roj = desired
                if roj and hall.get("FitupStart") and roj < hall["FitupStart"]:
                    roj = hall["FitupStart"]
                if site_accept and (roj is None or site_accept > roj):
                    roj = site_accept

                rows.append({
                    "Building Name": b["building_name"],
                    "Equipment": f'{item["Equipment"]} (Hall {idx})',
                    "Location": "Hall",
                    "Release Plan": release_plan,
                    "Release Needed": release_needed,
                    "Status": _equipment_status(release_needed),
                    "Lead Time (weeks)": _lead_time_weeks(lead_wd),
                    "Site Acceptance": site_accept,
                    "ROJ Target": desired,
                    "ROJ": roj,
                    "ROJ Status": _roj_status(site_accept, desired, roj),
                })
    return rows
