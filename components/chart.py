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

    df = gdf.reset_index(drop=True).copy()
    df["Description"] = df["Task"].astype(str)
    category_order = df["Description"].tolist()

    fig = px.timeline(
        df,
        x_start="Start",
        x_end="Finish",
        y="Description",
        color="Phase",
        color_discrete_map=color_map,
        title="",
        hover_name="Description",
        hover_data={
            "Description": False,
            "Start": True,
            "Finish": True,
            "Phase": True,
        },
    )
    fig.update_xaxes(showgrid=True, gridcolor="lightgray", linewidth=1, linecolor=colors.MANO_BLUE)
    fig.update_yaxes(
        showgrid=True,
        autorange="reversed",
        linewidth=1,
        linecolor=colors.MANO_BLUE,
        categoryorder="array",
        categoryarray=category_order[::-1],
    )
    fig.update_traces(width=0.6)
    fig.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor=colors.MANO_OFFWHITE,
        font_family="Raleway",
        legend_title_text="Phase",
    )

    if milestones is not None and not milestones.empty:
        milestone_df = milestones.copy()
        row_lookup = dict(zip(df["Task"], df["Description"]))
        milestone_df["RowLabel"] = milestone_df["Task"].map(row_lookup)
        milestone_df = milestone_df.dropna(subset=["RowLabel"])
        if milestone_df.empty:
            st.plotly_chart(fig, use_container_width=True)
            return

        fig.add_trace(
            go.Scatter(
                x=milestone_df["Date"],
                y=milestone_df["RowLabel"],
                mode="markers",
                marker=dict(
                    symbol="circle",
                    size=12,
                    color=colors.POWER_MILESTONE_COLOR,
                    line=dict(color="white", width=1),
                ),
                customdata=milestone_df[["Task"]],
                name="Power Available",
                hovertemplate="<b>%{customdata[0]}</b><br>Power Available: %{x|%b %d, %Y}<extra></extra>",
            )
        )

    st.plotly_chart(fig, use_container_width=True)
