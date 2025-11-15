import streamlit as st
import pandas as pd
from datetime import date, datetime


from grid_data import load_grid_data
from baseline import (
    build_ev_baseline,
    build_heatpump_baseline,
    build_household_baseline,
)



# ----------------------------------------------------
# Page Config
# ----------------------------------------------------
st.set_page_config(
    page_title="Axel Home Optimiser",
    layout="wide",
)


# ----------------------------------------------------
# Title + Intro
# ----------------------------------------------------
st.title("⚡ Axel Home Flex Optimiser")
st.markdown("""
This tool demonstrates how intelligently shifting home energy use  
(EVs, batteries, heat pumps) can reduce **costs**, **carbon**,  
and make the grid more efficient.
""")


# ----------------------------------------------------
# 1. Choose a day
# ----------------------------------------------------
st.header("📅 Choose a Day to Simulate")

selected_date = st.date_input(
    "Select a date",
    value=date.today(),
    min_value=date(2018, 1, 1),
    max_value=date(2030, 1, 1)
)

date_str = selected_date.strftime("%Y-%m-%d")


# ----------------------------------------------------
# Load grid data
# ----------------------------------------------------
with st.spinner("Fetching UK grid data..."):
    df = load_grid_data(date_str)

if df.empty:
    st.error("Could not load grid data for this date.")
    st.stop()


# ----------------------------------------------------
# 2. Grid Overview
# ----------------------------------------------------
st.header("🔌 Grid Overview for the Day")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Wind & Solar Share (%)")
    st.line_chart(df.set_index("timestamp")[["wind_share", "solar_share"]])

with col2:
    st.subheader("Carbon Intensity (gCO₂/kWh)")
    st.line_chart(df.set_index("timestamp")[["carbon_intensity"]])

with col3:
    st.subheader("Agile Price (p/kWh)")
    st.line_chart(df.set_index("timestamp")[["price"]])


# ----------------------------------------------------
# 3. Home Profile
# ----------------------------------------------------
st.header("🏠 Home Energy Profile")

# EV Settings -----------------------------------------------------
with st.expander("🚗 Electric Vehicle"):
    ev_arrival = st.time_input("EV arrival time", value=pd.to_datetime("18:00").time())
    ev_depart  = st.time_input("EV departure time", value=pd.to_datetime("07:00").time())
    ev_kwh     = st.number_input("Charge needed (kWh)", min_value=0.0, max_value=100.0, value=10.0)


# Heat Pump Settings ----------------------------------------------
with st.expander("🔥 Heat Pump"):
    hp_kwh = st.number_input("Daily heat demand (kWh)", min_value=0.0, max_value=40.0, value=8.0)
    hp_start = st.time_input("Heating allowed from", value=pd.to_datetime("06:00").time())
    hp_end   = st.time_input("Heating allowed until", value=pd.to_datetime("22:00").time())


# Battery Settings -------------------------------------------------
with st.expander("🔋 Home Battery"):
    batt_capacity = st.number_input("Battery capacity (kWh)", min_value=0.0, max_value=50.0, value=5.0)
    batt_power = st.number_input("Max charge/discharge (kW)", min_value=0.0, max_value=10.0, value=3.0)
    batt_eff = st.slider("Round-trip efficiency (%)", min_value=60, max_value=100, value=90)

# ----------------------------------------------------
# Build baseline load models (EV, heat pump, household)
# This must run after the widgets above so we can use their values
# ----------------------------------------------------
with st.spinner("Building baseline load models..."):
    # selected_date is a date object from the date_input
    date_obj = selected_date

    #normalise timezones
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    if df["timestamp"].dt.tz is not None:
        df["timestamp"] = df["timestamp"].dt.tz_convert(None)

    timestamps = df["timestamp"]

    # EV baseline
    ev_baseline = build_ev_baseline(
        date_obj,
        timestamps,
        ev_arrival,
        ev_kwh
    )

    # Heat pump baseline
    heatpump_baseline = build_heatpump_baseline(
        date_obj,
        timestamps,
        morning_window=(pd.to_datetime("06:00").time(), pd.to_datetime("09:00").time()),
        evening_window=(pd.to_datetime("17:00").time(), pd.to_datetime("21:00").time()),
    )

    # Household baseload
    house_baseline = build_household_baseline(date_obj, timestamps)

    # Merge all baseline components
    df = df.merge(ev_baseline, on="timestamp")
    df = df.merge(heatpump_baseline, on="timestamp")
    df = df.merge(house_baseline, on="timestamp")

    # Total baseline load
    df["baseline_kwh"] = (
        df["ev_kwh"] +
        df["hp_kwh"] +
        df["house_kwh"]
    )

# ----------------------------------------------------
# Baseline Load Profile (visualisation)
# ----------------------------------------------------
st.header("📊 Baseline Load Profile")

st.markdown("""
This chart shows the household's expected energy demand for the selected day  
**before Axel performs any optimisation**.
""")

baseline_cols = ["ev_kwh", "hp_kwh", "house_kwh", "baseline_kwh"]

st.line_chart(
    df.set_index("timestamp")[baseline_cols]
)



# ----------------------------------------------------
# 4. Optimisation Goal
# ----------------------------------------------------
st.header("🎯 Optimisation Goal")

opt_goal = st.radio(
    "What should Axel optimise for?",
    [
        "Cheapest energy",
        "Lowest carbon",
        "Balanced"
    ]
)


# ----------------------------------------------------
# 5. Run Button
# ----------------------------------------------------
run_opt = st.button("🚀 Run Optimisation")

if run_opt:
    st.success("Optimisation run! (placeholder)")
    st.info("Next step: plug in optimiser logic.")


    # Placeholder KPIs
    st.header("📈 Results Dashboard (Placeholder)")

    k1, k2, k3 = st.columns(3)
    k1.metric("£ Saved", "—")
    k2.metric("CO₂ Avoided", "—")
    k3.metric("% Shifted to Green Hours", "—")

    # Placeholder comparison chart
    st.subheader("Baseline vs Optimised Load Profile (placeholder)")
    st.line_chart(df.set_index("timestamp")[["carbon_intensity"]])  # temp


# ----------------------------------------------------
# End
# ----------------------------------------------------
st.markdown("---")
st.caption("Built for Axel — demonstrating the power of intelligent home flexibility.")
