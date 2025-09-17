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
  styler = (
    df.style
      .hide(axis="index")
      .set_table_attributes('class="styled-table"')
      .set_table_styles([
        {"selector": "th", "props": [("min-width", f"{col_space}px"), ("white-space", "nowrap")]},
        {"selector": "td", "props": [("min-width", f"{col_space}px"), ("white-space", "nowrap")]},
      ])
  )

  if highlight_release_within_days is not None and not df.empty:
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
      if today <= earliest_release <= window_end:
        return ["background-color: #fff3cd"] * len(row)
      return [""] * len(row)

    styler = styler.apply(highlight_release, axis=1)

  html = styler.to_html()
  st.markdown("""<div class="table-container">""" + html + "</div>", unsafe_allow_html=True)
