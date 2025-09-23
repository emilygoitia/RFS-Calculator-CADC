# ======================= Client-specific OFCI equipment =======================
# Each entry captures the assumed lead time in working days. Buffers represent
# the desired cushion ahead of L3.
RAW_EQUIPMENT = [
    {
        "Equipment": "Generators",
        "scope": "house",
        "lead_time_wd": 320,
        "buffer_wd_before_L3": 30,
    },
    {
        "Equipment": "Utility Switchgear",
        "scope": "house",
        "lead_time_wd": 240,
        "buffer_wd_before_L3": 30,
    },
    {
        "Equipment": "UPS",
        "scope": "hall",
        "lead_time_wd": 270,
        "buffer_wd_before_L3": 20,
    },
    {
        "Equipment": "PDU",
        "scope": "hall",
        "lead_time_wd": 225,
        "buffer_wd_before_L3": 20,
    },
    {
        "Equipment": "CRAC",
        "scope": "hall",
        "lead_time_wd": 210,
        "buffer_wd_before_L3": 20,
    },
    {
        "Equipment": "BMS",
        "scope": "hall",
        "lead_time_wd": 180,
        "buffer_wd_before_L3": 25,
    },
]
