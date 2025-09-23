import math
from datetime import date, datetime

import utils.date as date_utils
import data.equipment as equipment


def _max_date(*dates):
    valid = [d for d in dates if d is not None]
    return max(valid) if valid else None

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


def get_modeled_equipment_rows(b, ww, holidays):
    rows = []
    first_hall = b["halls"][0] if b.get("halls") else None

    for item in equipment.RAW_EQUIPMENT:
        lead_wd = int(item.get("lead_time_wd") or 0)
        buffer_wd = int(item.get("buffer_wd_before_L3") or 0)
        if item["scope"] == "house":
            desired = None
            if first_hall and first_hall.get("L3Start"):
                ideal = first_hall["L3Start"]
                if buffer_wd:
                    ideal = date_utils.add_workdays(ideal, -buffer_wd, holidays, workdays_per_week=ww)
                desired = date_utils.clamp(ideal, b.get("dryin_date"), None)

            release_needed = date_utils.add_workdays(desired, -lead_wd, holidays, workdays_per_week=ww) if (desired and lead_wd) else None
            release_date = release_needed
            site_accept = date_utils.add_workdays(release_date, lead_wd, holidays, workdays_per_week=ww) if (release_date and lead_wd) else release_date

            roj = desired
            if site_accept and (roj is None or site_accept > roj):
                roj = site_accept
            if roj and b.get("dryin_date") and roj < b["dryin_date"]:
                roj = b["dryin_date"]

            rows.append({
                "Building Name": b["building_name"],
                "Equipment": item["Equipment"],
                "Location": "House",
                "Release Needed": release_needed,
                "Status": _equipment_status(release_needed),
                "Lead Time (weeks)": _lead_time_weeks(lead_wd),
                "Site Acceptance": site_accept,
                "ROJ Target": desired,
                "ROJ": roj,
            })
        else:
            for idx, hall in enumerate(b.get("halls", []), start=1):
                ideal = hall.get("L3Start")
                if ideal and buffer_wd:
                    ideal = date_utils.add_workdays(ideal, -buffer_wd, holidays, workdays_per_week=ww)
                desired = date_utils.clamp(ideal, hall.get("FitupStart"), hall.get("FitupFinish")) if ideal else None

                release_needed = date_utils.add_workdays(desired, -lead_wd, holidays, workdays_per_week=ww) if (desired and lead_wd) else None
                release_date = release_needed
                site_accept = date_utils.add_workdays(release_date, lead_wd, holidays, workdays_per_week=ww) if (release_date and lead_wd) else release_date

                roj = desired
                if roj and hall.get("FitupStart") and roj < hall["FitupStart"]:
                    roj = hall["FitupStart"]
                if site_accept and (roj is None or site_accept > roj):
                    roj = site_accept

                rows.append({
                    "Building Name": b["building_name"],
                    "Equipment": f'{item["Equipment"]} (Hall {idx})',
                    "Location": "Hall",
                    "Release Needed": release_needed,
                    "Status": _equipment_status(release_needed),
                    "Lead Time (weeks)": _lead_time_weeks(lead_wd),
                    "Site Acceptance": site_accept,
                    "ROJ Target": desired,
                    "ROJ": roj,
                })
    return rows
