import utils.colors as colors

def render_kpi_card(building, label, key):
  return f"""<div class="kpi-card"><p>{building['building_name']}</p><h6>{label}</h6><h5 style="padding:0;color:{colors.MANO_BLUE}">{building[key]}</h5></div>"""
