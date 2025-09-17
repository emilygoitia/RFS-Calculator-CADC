# ======================= Client-specific OFCI equipment =======================
# Each entry captures the assumed lead time in working days along with the
# release "back off" (how many working days away from the anchor milestone the
# PO should be placed).  Buffers represent the desired cushion ahead of L3.
RAW_EQUIPMENT = [
    {
        "Equipment": "Generators",
        "scope": "house",
        "lead_time_wd": 320,
        "buffer_wd_before_L3": 30,
        "release_anchor": "ntp",
        "release_offset_wd": 150,
    },
    {
        "Equipment": "Utility Switchgear",
        "scope": "house",
        "lead_time_wd": 240,
        "buffer_wd_before_L3": 30,
        "release_anchor": "ntp",
        "release_offset_wd": 200,
    },
    {
        "Equipment": "UPS",
        "scope": "hall",
        "lead_time_wd": 270,
        "buffer_wd_before_L3": 20,
        "release_anchor": "bp",
        "release_offset_wd": 105,
    },
    {
        "Equipment": "PDU",
        "scope": "hall",
        "lead_time_wd": 225,
        "buffer_wd_before_L3": 20,
        "release_anchor": "fitup_start",
        "release_offset_wd": -60,
    },
    {
        "Equipment": "CRAC",
        "scope": "hall",
        "lead_time_wd": 210,
        "buffer_wd_before_L3": 20,
        "release_anchor": "fitup_start",
        "release_offset_wd": -60,
    },
    {
        "Equipment": "BMS",
        "scope": "hall",
        "lead_time_wd": 180,
        "buffer_wd_before_L3": 25,
        "release_anchor": "fitup_start",
        "release_offset_wd": -90,
    },
]
