import streamlit as st

def render_styled_slider(label, min_value, max_value, default_value, help=None):
    with st.container():
        st.write("<div class='styled-slider' />", unsafe_allow_html=True)
        slider = st.slider(label, min_value, max_value, default_value, help=help)
        return slider
