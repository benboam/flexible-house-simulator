import altair as alt

def make_product_plot(df):
    """
    Creates a premium product-style plot:
    - Renewable share (wind+solar) as smooth area
    - Agile price as line (secondary axis)
    - Shaded clean-hours regions
    """
    plot_df = df.copy()
    plot_df["renewable_share"] = plot_df["wind_share"] + plot_df["solar_share"]

    

    # Base chart with timestamp
    base = alt.Chart(plot_df).encode(
        x=alt.X(
            "timestamp:T",
            axis=alt.Axis(title="Time of Day", grid=True, labelAngle=-45)
        )
    )

    # Renewable area chart
    renew_area = base.mark_area(
        line={"color": "#2ECC71"},
        color=alt.Gradient(
            gradient="linear",
            stops=[
                {"offset": 0, "color": "#ABEBC6"},
                {"offset": 1, "color": "#2ECC71"}
            ],
            x1=0, x2=0, y1=1, y2=0
        ),
        opacity=0.8
    ).encode(
        y=alt.Y(
            "renewable_share:Q",
            axis=alt.Axis(title="Wind and Solar Generation share(%)", titleColor="#2ECC71")
        ),
        tooltip=[
            alt.Tooltip("timestamp:T", title="Time"),
            alt.Tooltip("wind_share:Q", title="Wind (%)", format=".1f"),
            alt.Tooltip("solar_share:Q", title="Solar (%)", format=".1f"),
            alt.Tooltip("renewable_share:Q", title="Total Renewables (%)", format=".1f"),
        ]
    )

    # Price line (secondary axis)
    price_line = base.mark_line(
        color="#3498DB",
        strokeWidth=2,
    ).encode(
        y=alt.Y(
            "price:Q",
            axis=alt.Axis(title="Price (p/kWh)", titleColor="#3498DB"),
            scale=alt.Scale(domain=[plot_df["price"].min(), plot_df["price"].max()])
        ),
        tooltip=[alt.Tooltip("price:Q", title="Price (p/kWh)", format=".2f")]
    )
    

    # Combine layers
    chart = alt.layer( renew_area, price_line).resolve_scale(
        y="independent"
    ).properties(
        width="container",
        height=350,
        title="Renewable Share vs Agile Price"
    )

    return chart


def plot_baseline(df):
    """
    Stacked area chart showing:
    - EV (flexible)
    - Heat pump (semi-flexible)
    - House baseload (fixed)
    """

    plot_df = df.copy()[["timestamp", "ev_kwh", "hp_kwh", "house_kwh"]]

    melted = plot_df.melt(
        id_vars="timestamp",
        value_vars=["ev_kwh", "hp_kwh", "house_kwh"],
        var_name="load_type",
        value_name="kwh"
    )

    color_scale = alt.Scale(
        domain=["house_kwh", "hp_kwh", "ev_kwh"],
        range=["#BDC3C7", "#F5B041", "#5DADE2"]  # grey, orange, blue
    )

    area = alt.Chart(melted).mark_area(
        interpolate="monotone",
        opacity=0.85
    ).encode(
        x=alt.X("timestamp:T", title="Time"),
        y=alt.Y("kwh:Q", title="Load (kWh per 30 min)"),
        color=alt.Color("load_type:N", scale=color_scale, title="Load Type"),
        tooltip=[
            alt.Tooltip("timestamp:T", title="Time"),
            alt.Tooltip("load_type:N", title="Type"),
            alt.Tooltip("kwh:Q", title="kWh", format=".2f")
        ]
    ).properties(
        width="container",
        height=350,
        title="Baseline Household Load Profile (Stacked)"
    )

    return area


import plotly.graph_objects as go

import pandas as pd
import numpy as np
import plotly.graph_objects as go

def plot_optimised(df):

    df = df.copy()
    df["baseline"] = df["baseline_kwh"]
    df["optim"] = df["optimised_kwh"]

    # Determine shading direction on each timestep
    df["label"] = np.where(df["optim"] > df["baseline"], 1, 0)

    # Split dataframe whenever shading direction changes
    df["group"] = df["label"].ne(df["label"].shift()).cumsum()
    groups = [g for _, g in df.groupby("group")]

    # Keep track of whether we've already added legend entries
    legend_green_shown = False
    legend_red_shown = False

    def fill_color(label):
        return (
            "rgba(120, 200, 150, 0.35)" if label == 1
            else "rgba(255, 120, 120, 0.35)"
        )

    fig = go.Figure()

    # ----------------------------------------------------
    # Add shaded segments without duplicate legend entries
    # ----------------------------------------------------
    for seg in groups:
        label = seg["label"].iloc[0]
        color = fill_color(label)

        # Control legend visibility
        if label == 1:
            showlegend = not legend_green_shown
            name = "Shifted to Green Hours"
            legend_green_shown = True
        else:
            showlegend = not legend_red_shown
            name = "Reduced Load"
            legend_red_shown = True

        # First invisible trace
        fig.add_trace(go.Scatter(
            x=seg["timestamp"],
            y=seg["baseline"] if label == 1 else seg["optim"],
            mode="lines",
            line=dict(color="rgba(0,0,0,0)"),
            hoverinfo="skip",
            showlegend=False
        ))

        # Second trace that fills to the first
        fig.add_trace(go.Scatter(
            x=seg["timestamp"],
            y=seg["optim"] if label == 1 else seg["baseline"],
            mode="lines",
            fill="tonexty",
            fillcolor=color,
            line=dict(color="rgba(0,0,0,0)"),
            name=name,
            showlegend=showlegend,
            hovertemplate="%{y:.2f} kWh<br>%{x}<extra></extra>",
        ))

    # ----------------------------------------------------
    # Add main load curves (always single legend)
    # ----------------------------------------------------
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["baseline"],
        mode="lines",
        name="Baseline Load",
        line=dict(color="#1f77b4", width=2)
    ))

    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["optim"],
        mode="lines",
        name="Optimised Load",
        line=dict(color="#333", width=2, dash="dot")
    ))

    fig.update_layout(
        template="plotly_white",
        title="Baseline vs Optimised Load (Shaded Differences)",
        yaxis_title="Load (kWh per 30 min)",
        xaxis_title="Time",
        hovermode="x unified",
        height=420,
        legend=dict(orientation="h", y=1.15)
    )

    return fig



