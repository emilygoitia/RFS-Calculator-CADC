import streamlit as st
import utils.colors as colors

def inject_custom_css():
  BRAND_CSS = f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Raleway:wght@300;400;500;600;700&display=swap');
      :root {{
        --mano-blue: {colors.MANO_BLUE};
        --mano-offwhite: {colors.MANO_OFFWHITE};
        --mano-grey: {colors.MANO_GREY};
        --border-radius: 8px;
      }}
      html, body, [class*="css"]  {{ font-family: 'Raleway', sans-serif; }}
      .stApp {{ background: var(--mano-offwhite); }}
      * {{ font-family: 'Raleway' !important; }}

      h1, h2, h3, h4, h5, h6 {{ 
        color: var(--mano-grey); 
        font-weight: 600;
      }}
      section[data-testid="stSidebar"] > div {{
        background: white;
        border-right: 2px solid var(--mano-blue); }}

      .stButton>button, .stDownloadButton>button {{
        background: var(--mano-blue);
        color: white;
        border: 1px solid transparent;
        border-radius: 12px;
        padding: .5rem 1rem;
        transition: background 0.3s, color 0.3s;
      }}
      .stButton>button:hover, .stDownloadButton>button:hover {{
        background: var(--mano-offwhite);
        color: var(--mano-blue);
        border-color: var(--mano-blue);
        border-radius: 12px;
        padding: .5rem 1rem;
      }}

      .dataframe tbody tr:nth-child(even) {{ background: #fff; }}

      .small-muted {{
        color: #5c6b73;
        font-size: 0.875rem;
      }}

      .table-container {{
        max-height: 400px;
        overflow-y: auto;
        margin-bottom: 1rem;
        border-radius: var(--border-radius);
        border-bottom: 1px solid #bbb;
        box-sizing: content-box;
        scrollbar-width: thin;
        scrollbar-color: rgba(0,0,0,0.5) transparent;
      }}

      .table-container::-webkit-scrollbar {{
        width: 6px;
      }}
      .table-container::-webkit-scrollbar-track {{
        background: transparent;
      }}

      .styled-table {{
        font-family: 'Raleway', sans-serif;
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border: 0;
        margin-bottom: 0 !important;
      }}
      .styled-table thead th {{
        position: sticky;
        top: 0;
        z-index: 1;
      }}
      .styled-table td {{
        border: 0;
      }}
      .styled-table tr th, .styled-table tr td {{
        border-right: 1px solid #bbb;
        border-bottom: 1px solid #bbb;
      }}
      .styled-table tr:last-child td {{
        border-bottom: 0;
      }}
      .styled-table tr th:first-child, .styled-table tr td:first-child {{
        border-left: 1px solid #bbb;
      }}
      .styled-table tr th {{
        text-align: left;
        border-top: solid 1px #bbb;
      }}
      .styled-table tr {{ text-align: left !important; font-size: 0.875rem; }}
      .styled-table th {{ background: var(--mano-blue); color: var(--mano-offwhite); font-weight: 600; font-size: 0.875rem; }}
      .styled-table tr:first-child th:first-child {{border-top-left-radius: var(--border-radius);}}
      .styled-table tr:first-child th:last-child {{border-top-right-radius: var(--border-radius);}}
      .styled-table tr:last-child td:first-child {{border-bottom-left-radius: var(--border-radius);}}
      .styled-table tr:last-child td:last-child {{border-bottom-right-radius: var(--border-radius);}}

      div[data-testid='stVerticalBlockBorderWrapper']:has(>div>div>div>div>div[data-testid="stMarkdownContainer"]>.styled-slider){{
        padding: 10px;
        border-radius: 0.5rem;
      }}
      div[data-testid='stVerticalBlockBorderWrapper']:has(>div>div>div>div>div[data-testid="stMarkdownContainer"]>.styled-slider):nth-child(even){{ 
        background-color: var(--mano-offwhite);
      }}
      div[data-testid='stVerticalBlockBorderWrapper']:has(>div>div>div>div>div[data-testid="stMarkdownContainer"]>.styled-slider) [data-testid="stVerticalBlock"] {{
        gap: 0;
      }}

      .kpi-card {{
        background: white;
        padding: 12px;
        border-radius: 16px;
        border-left: 6px solid var(--mano-blue);
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
      }}
      .kpi-card p {{
        margin: 0;
        font-weight: 500;
        font-size: 0.675rem;
        color: var(--mano-grey);
      }}
    </style>
    """
  st.markdown(BRAND_CSS, unsafe_allow_html=True)