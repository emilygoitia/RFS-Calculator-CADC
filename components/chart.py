import streamlit as st
import utils.colors as colors

# ---- Plotly guard (clear message if missing on Cloud) ----
try:
    import plotly.express as px
    import plotly.graph_objects as go
except ModuleNotFoundError:
    st.error("Plotly isn’t installed. Add `plotly==6.3.0` to requirements.txt and Restart the app.")
    st.stop()


def render_gantt(gdf, milestones=None):
    color_map = {
        "Site Work": colors.SITE_WORK_COLOR,
        "Shell": colors.MANO_BLUE,
        "MEP Yard": colors.MANO_GREY,
        "Fitup": colors.FITOUT_COLOR,
        "L3": colors.L3_COLOR,
        "L4": colors.L4_COLOR,
        "L5": colors.L5_COLOR,
    }

    fig = px.timeline(
        gdf,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Phase",
        color_discrete_map=color_map,
        title="",
    )
    fig.update_xaxes(showgrid=True, gridcolor="lightgray", linewidth=1, linecolor=colors.MANO_BLUE)
    fig.update_yaxes(showgrid=True, autorange="reversed", linewidth=1, linecolor=colors.MANO_BLUE)
    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor=colors.MANO_OFFWHITE,
        font_family="Raleway",
        legend_title_text="Phase",
    )

    if milestones is not None and not milestones.empty:
        fig.add_trace(
            go.Scatter(
                x=milestones["Date"],
                y=milestones["Task"],
                mode="markers",
                marker=dict(
                    symbol="circle",
                    size=12,
                    color=colors.POWER_MILESTONE_COLOR,
                    line=dict(color="white", width=1),
                ),
                name="Power Available",
                hovertemplate="<b>%{y}</b><br>Power Available: %{x|%b %d, %Y}<extra></extra>",
            )
        )

    st.plotly_chart(fig, use_container_width=True)
