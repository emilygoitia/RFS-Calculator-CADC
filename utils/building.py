import utils.date as date_utils
import data.equipment as equipment

# ======================= Procurement model (submittals + mfg + shipping) =======================
def get_modeled_equipment_rows(b, ww, holidays):
    rows = []
    for item in equipment.RAW_EQUIPMENT:
        po = date_utils.to_date(item.get("PO"))
        fab = date_utils.to_date(item.get("FabStart"))
        ship = date_utils.to_date(item.get("ExpectedShip"))
        delivered = date_utils.to_date(item.get("Delivered"))

        submittals_wd = date_utils.workdays_between(po, fab, ww, holidays) if po and fab else None
        if submittals_wd is None: submittals_wd = 20
        submittals_wd = max(15, min(submittals_wd, 45))

        mfg_wd = date_utils.workdays_between(fab, ship, ww, holidays) if fab and ship else None
        ship_wd = date_utils.workdays_between(ship, delivered, ww, holidays) if ship and delivered else 15

        arrival = None
        if po:
            arrival = date_utils.add_workdays(po, submittals_wd, holidays, workdays_per_week=ww)
            if mfg_wd: arrival = date_utils.add_workdays(arrival, mfg_wd, holidays, workdays_per_week=ww)
            if ship_wd: arrival = date_utils.add_workdays(arrival, ship_wd, holidays, workdays_per_week=ww)

        buf = int(item["buffer_wd_before_L3"])
        if item["scope"] == "house":
            anchor = b["halls"][0]["L3Start"]
            ideal = date_utils.add_workdays(anchor, -buf, holidays, workdays_per_week=ww)
            roj = date_utils.clamp(ideal, b["dryin_date"], None)
            total_wd = (submittals_wd or 0) + (mfg_wd or 0) + (ship_wd or 0)
            release = date_utils.add_workdays(roj, -total_wd, holidays, workdays_per_week=ww) if roj else None
            rows.append({
                "Building Name": b["building_name"],
                "Equipment": item["Equipment"],
                "Location": "House",
                "Required Release/PO": release,
                "Submittals (days)": submittals_wd,
                "Manufacturing (days)": mfg_wd,
                "Shipping (days)": ship_wd,
                "Site Acceptance": arrival,
                "ROJ": roj,

            })
        else:
            for i, h in enumerate(b["halls"], start=1):
                ideal = date_utils.add_workdays(h["L3Start"], -buf, holidays, workdays_per_week=ww)
                roj_h = date_utils.clamp(ideal, h["FitupStart"], h["FitupFinish"])
                total_wd = (submittals_wd or 0) + (mfg_wd or 0) + (ship_wd or 0)
                release_h = date_utils.add_workdays(roj_h, -total_wd, holidays, workdays_per_week=ww) if roj_h else None
                rows.append({
                    "Building Name": b["building_name"],
                    "Equipment": f'{item["Equipment"]} (Hall {i})',
                    "Location": "Hall",
                    "Required Release/PO": release_h,
                    "Submittals (days)": submittals_wd,
                    "Manufacturing (days)": mfg_wd,
                    "Shipping (days)": ship_wd,
                    "Site Acceptance": arrival,
                    "ROJ": roj_h,
                    
                })
    return rows