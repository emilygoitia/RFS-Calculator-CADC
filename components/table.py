import streamlit as st

def render_styled_table(df):
  """Render a styled table in Streamlit."""
  html = df.to_html(index=False, classes="styled-table")
  st.markdown("""<div class="table-container">""" + html + "</div>", unsafe_allow_html=True)
