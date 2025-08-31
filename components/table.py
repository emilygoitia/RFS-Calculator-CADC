import streamlit as st

def render_styled_table(df, col_space=110):
  """Render a styled table in Streamlit."""
  html = df.to_html(index=False, classes="styled-table", col_space=col_space)
  st.markdown("""<div class="table-container">""" + html + "</div>", unsafe_allow_html=True)
