from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st


def _coerce_date(value):
  if pd.isna(value):
    return None
  if isinstance(value, date) and not isinstance(value, datetime):
    return value
  if isinstance(value, (pd.Timestamp, datetime)):
    return value.date()
  return None


def render_styled_table(df, col_space=110, highlight_release_within_days=None):
  """Render a styled table in Streamlit."""
  display_df = df.copy()

  status_icon_map = {
    "Overdue": "🔴",
    "At Risk": "🟡",
    "On Track": "🟢",
  }
  status_color_map = {
    "Overdue": "#d62828",
    "At Risk": "#f4a261",
    "On Track": "#2a9d8f",
  }

  if "Status" in display_df.columns:
    display_df["Status"] = display_df["Status"].map(
      lambda s: f"{status_icon_map.get(s, '')} {s}".strip()
      if isinstance(s, str) and s
      else s
    )

  styler = (
    display_df.style
      .hide(axis="index")
      .set_table_attributes('class="styled-table"')
      .set_table_styles([
        {"selector": "th", "props": [("min-width", f"{col_space}px"), ("white-space", "nowrap")]},
        {"selector": "td", "props": [("min-width", f"{col_space}px"), ("white-space", "nowrap")]},
      ])
  )

  if highlight_release_within_days is not None and not display_df.empty:
    today = date.today()
    window_end = today + timedelta(days=highlight_release_within_days)

    def highlight_release(row):
      release_dates = [
        _coerce_date(row.get("Release Plan")),
        _coerce_date(row.get("Release Needed")),
      ]
      release_dates = [d for d in release_dates if d is not None]
      if not release_dates:
        return [""] * len(row)
      earliest_release = min(release_dates)
      if earliest_release < today:
        return ["background-color: #f8d7da"] * len(row)
      if earliest_release <= window_end:
        return ["background-color: #fff3cd"] * len(row)
      return [""] * len(row)

    styler = styler.apply(highlight_release, axis=1)

  if "Status" in display_df.columns:
    def style_status(val):
      if isinstance(val, str):
        if val.startswith("🔴"):
          return f"color: {status_color_map['Overdue']}; font-weight: 600;"
        if val.startswith("🟡"):
          return f"color: {status_color_map['At Risk']}; font-weight: 600;"
        if val.startswith("🟢"):
          return f"color: {status_color_map['On Track']}; font-weight: 600;"
      return ""

    styler = styler.applymap(style_status, subset=["Status"])

  html = styler.to_html()
  st.markdown("""<div class="table-container">""" + html + "</div>", unsafe_allow_html=True)
