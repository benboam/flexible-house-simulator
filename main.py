import streamlit as st
import pandas as pd
from datetime import date, datetime


from grid_data import load_grid_data
from baseline import (
    build_ev_baseline,
    build_heatpump_baseline,
    build_household_baseline,
)
from optimiser import optimise_ev, optimise_heatpump

from plot_helper import make_product_plot, plot_baseline,plot_optimised





# ----------------------------------------------------
# Formatting helpers (money, CO₂, etc.)
# ----------------------------------------------------
def fmt_money(x: float) -> str:
    """Format numbers as £ with thousands separators."""
    return f"£{x:,.2f}"


def fmt_co2(x_kg: float) -> str:
    """Format kg into kg or tonnes depending on size."""
    if x_kg >= 1000:
        return f"{x_kg/1000:,.1f} t"
    return f"{x_kg:,.1f} kg"


# ----------------------------------------------------
# Session state for optimisation results
# ----------------------------------------------------
if "optimised" not in st.session_state:
    st.session_state.optimised = False

if "results" not in st.session_state:
    st.session_state.results = None


# ----------------------------------------------------
# Page Config + Global Styling (Soft UI)
# ----------------------------------------------------
st.set_page_config(
    page_title="Axle Home Optimiser",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Soft UI CSS
st.markdown(
    """
<style>
    body {
        background-color: #f4f5fb;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }
    .main .block-container {
        background-color: #ffffff;
        border-radius: 18px;
        box-shadow: 0 10px 40px rgba(15, 23, 42, 0.08);
    }
    h1, h2, h3, h4 {
        font-family: -apple-system, system-ui, BlinkMacSystemFont, "SF Pro Text", sans-serif;
    }
    .stButton>button {
        border-radius: 999px;
        padding: 0.6rem 1.4rem;
        border: none;
        font-weight: 600;
        font-size: 0.95rem;
        background: linear-gradient(135deg, #4ade80, #22c55e);
        color: #ffffff;
        box-shadow: 0 8px 20px rgba(34, 197, 94, 0.35);
    }
    .stButton>button:hover {
        filter: brightness(1.05);
    }
    .soft-card {
        background-color: #f8fafc;
        border-radius: 16px;
        padding: 1rem 1.2rem;
        border: 1px solid rgba(148, 163, 184, 0.25);
        margin-bottom: 1.2rem;
    }
    .soft-card h3 {
        margin-top: 0;
        margin-bottom: 0.5rem;
    }
    .soft-metric .metric-label {
        font-size: 0.8rem;
        color: #64748b;
    }
    .soft-metric .metric-value {
        font-weight: 600;
        font-size: 1.2rem;
        color: #0f172a;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ----------------------------------------------------
# Clean soft-card metric styling
# ----------------------------------------------------
st.markdown("""
<style>
.soft-card {
    background: rgba(245, 248, 250, 0.9);
    padding: 1.2rem 1.4rem;
    border-radius: 14px;
    border: 1px solid rgba(200, 200, 200, 0.35);
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    margin-bottom: 1.2rem;
}

.metric-label {
    font-size: 0.9rem;
    color: #4A4A4A;
    margin-bottom: 0.35rem;
}

.metric-value {
    font-size: 1.7rem;
    font-weight: 600;
    color: #1a1a1a;
}
</style>
""", unsafe_allow_html=True)


def soft_metric(label, value):
    """Return a fully self-contained metric card."""
    return f"""
    <div class="soft-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """


# ----------------------------------------------------
# Title + Intro
# ----------------------------------------------------



st.title("⚡ What You Could Unlock With Axle Energy")

st.markdown("""
With **Axle under the hood**, your customers get effortless smart charging & heating.  
Your business gets better economics, margin protection, and access to energy markets.

With Axle, you can offer customers:

- **Lower bills** without requiring behaviour change  
- EV charging or heating that is **“ready when needed”** — never at the wrong time  
- **Automatic optimisation** across wholesale, balancing & flexibility markets  
- **Transparent rewards** for supporting the grid  
- **Full control & safety** (they can override at any time)

This interface simulates what your customer experience could look like —  
and the **savings and hedging value** your business can unlock behind the scenes.   
""")



st.divider()


# ----------------------------------------------------
# 1. Choose a day
# ----------------------------------------------------
st.subheader("📅 Choose a Day to Simulate")

selected_date = st.date_input(
    "Select a date",
    value=date.today(),
    min_value=date(2018, 1, 1),
    max_value=date.today(),
    help="Pick any date with UK Carbon Intensity + Agile price data available.",
)
date_str = selected_date.strftime("%Y-%m-%d")

st.divider()


# ----------------------------------------------------
# Load grid data
# ----------------------------------------------------
with st.spinner("Fetching UK grid & price data for this day..."):
    df = load_grid_data(date_str)

if df.empty:
    st.error("Could not load grid data for this date.")
    st.stop()


# ----------------------------------------------------
# 2. Grid Overview (Tabs)
# ----------------------------------------------------
st.subheader("🌱 How Axle Helps You Offer Competitive Pricing — Safely")

st.markdown("""
Your customers expect **simple, low-cost, reliable charging**.  
Your business needs to avoid **exposure to peak wholesale prices** and high-carbon hours.

This chart shows, for the selected day:

- Where **prices spike** (your wholesale risk exposure)  
- When **clean, cheap energy** is available   

""")

st.altair_chart(make_product_plot(df), use_container_width=True)


# ----------------------------------------------------
# 3. Home Profile (Friendly cards)
# ----------------------------------------------------
st.subheader("🏠 Your Customers Set Simple Preferences. Axle Handles Everything Else.")

st.markdown("""
Your customer tells you things like:

- “I need my EV ready by 7am.”  
- “Heat my home between 6–10pm.”  
- “Use my battery to save me money.”

Axle turns these preferences into actionable, safe, real-time flexibility —  
so your brand delivers a great experience **without any new engineering burden**.
""")



profile_cols = st.columns(3)

# EV Settings -----------------------------------------------------
with profile_cols[0]:
    with st.expander("🚗 Electric Vehicle", expanded=True):
        ev_arrival = st.time_input("EV arrival time", value=pd.to_datetime("18:00").time())
        ev_depart = st.time_input("EV departure time", value=pd.to_datetime("07:00").time())
        ev_kwh = st.number_input(
            "Charge needed by departure (kWh)",
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=1.0,
        )
        st.caption("Assumes a 7 kW home charger, no V2G in the baseline.")

# Heat Pump Settings ----------------------------------------------
with profile_cols[1]:
    with st.expander("🔥 Heat Pump", expanded=True):
        hp_kwh = st.number_input(
            "Daily heat demand (kWh, thermal)",
            min_value=0.0,
            max_value=40.0,
            value=8.0,
            step=1.0,
        )
        hp_start = st.time_input("Heating allowed from", value=pd.to_datetime("06:00").time())
        hp_end = st.time_input("Heating allowed until", value=pd.to_datetime("22:00").time())
        st.caption("We spread heating across comfort windows within this range.")

# Battery Settings -------------------------------------------------
with profile_cols[2]:
    with st.expander("🔋 Home Battery (not yet optimised)", expanded=False):
        batt_capacity = st.number_input(
            "Battery capacity (kWh)", min_value=0.0, max_value=50.0, value=5.0, step=1.0
        )
        batt_power = st.number_input(
            "Max charge/discharge (kW)", min_value=0.0, max_value=10.0, value=3.0, step=0.5
        )
        batt_eff = st.slider(
            "Round-trip efficiency (%)", min_value=60, max_value=100, value=90, step=1
        )
        st.caption("Battery is included in the profile but not yet actively optimised.")


# ----------------------------------------------------
# Build baseline load models (EV, heat pump, household)
# ----------------------------------------------------
with st.spinner("Building baseline load models..."):
    date_obj = selected_date

    # Normalise timestamps to naive datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    if df["timestamp"].dt.tz is not None:
        df["timestamp"] = df["timestamp"].dt.tz_convert(None)

    timestamps = df["timestamp"]

    # EV baseline
    ev_baseline = build_ev_baseline(
        date_obj,
        timestamps,
        ev_arrival,
        ev_kwh,
    )

    # Heat pump baseline (internal seasonal model)
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
    df["baseline_kwh"] = df["ev_kwh"] + df["hp_kwh"] + df["house_kwh"]


# ----------------------------------------------------
# Baseline Load Profile (visualisation)
# ----------------------------------------------------
st.subheader("📊 Baseline Load Profile")

st.markdown("""
This chart shows your customer’s **current unoptimised behaviour**:

- EV charges as soon as it plugs in  
- Heating follows fixed comfort windows  
- No awareness of wholesale prices or carbon intensity  

Axle builds flexible capacity from these everyday patterns —  
*while keeping comfort, readiness, and user control intact.*
""")


#baseline_cols = ["ev_kwh", "hp_kwh", "house_kwh", "baseline_kwh"]
st.altair_chart(plot_baseline(df), use_container_width=True)


st.divider()


# ----------------------------------------------------
# 4. Optimisation Goal
# ----------------------------------------------------
st.subheader("🎯 Choose the Strategy That Aligns With Your Product")

st.markdown("""
Different products prioritise different outcomes:

- **Cheapest cost** → reduces exposure to peak wholesale prices  
- **Lowest carbon** → enables green tariffs with real impact  
- **Balanced** → ideal for broad customer bases  

Axle can optimise for any of these, depending on the proposition you want to offer.
""")


opt_goal = st.radio(
    "What outcome should your product prioritise for customers?",
    ["Cheapest energy", "Lowest carbon", "Balanced"],
    horizontal=True,
)


# ----------------------------------------------------
# 5. Run Button – compute optimisation & store results
# ----------------------------------------------------
run_clicked = st.button("🚀 Run Optimisation", use_container_width=True)

if run_clicked:
    # -----------------------------
    # Run optimisation
    # -----------------------------
    hp_total_kwh = df["hp_kwh"].sum()

    ev_opt = optimise_ev(
        df,
        selected_date,
        ev_arrival,
        ev_depart,
        ev_kwh,
        opt_goal,
        charger_kw=7.0,
    )

    hp_opt = optimise_heatpump(
        df,
        hp_total_kwh=hp_total_kwh,
        opt_goal=opt_goal,
        max_hours=16,
    )

    df["ev_kwh_opt"] = ev_opt
    df["hp_kwh_opt"] = hp_opt
    df["optimised_kwh"] = df["ev_kwh_opt"] + df["hp_kwh_opt"] + df["house_kwh"]

    # -----------------------------
    # KPIs: cost & carbon
    # -----------------------------
    # Price is p/kWh – convert to £
    baseline_cost = (df["baseline_kwh"] * df["price"]).sum() / 100.0
    optimised_cost = (df["optimised_kwh"] * df["price"]).sum() / 100.0
    cost_saved = baseline_cost - optimised_cost

    # Carbon intensity is gCO₂/kWh – convert to kg
    baseline_co2_kg = (df["baseline_kwh"] * df["carbon_intensity"]).sum() / 1000.0
    optimised_co2_kg = (df["optimised_kwh"] * df["carbon_intensity"]).sum() / 1000.0
    co2_saved_kg = baseline_co2_kg - optimised_co2_kg

    # Share of load in "green hours"
    if "carbon_index" in df.columns:
        green_mask = df["carbon_index"].str.lower().isin(["low", "very low"])
    else:
        # Fallback: treat the cleanest 30% periods as "green"
        threshold = df["carbon_intensity"].quantile(0.3)
        green_mask = df["carbon_intensity"] <= threshold

    baseline_green_kwh = df.loc[green_mask, "baseline_kwh"].sum()
    optimised_green_kwh = df.loc[green_mask, "optimised_kwh"].sum()

    baseline_total = df["baseline_kwh"].sum()
    optimised_total = df["optimised_kwh"].sum()

    baseline_green_pct = (
        100 * baseline_green_kwh / baseline_total if baseline_total > 0 else 0
    )
    optimised_green_pct = (
        100 * optimised_green_kwh / optimised_total if optimised_total > 0 else 0
    )

    # Save results in session_state
    st.session_state.optimised = True
    st.session_state.results = {
        "df": df.copy(),
        "cost_saved": cost_saved,
        "co2_saved_kg": co2_saved_kg,
        "optimised_green_pct": optimised_green_pct,
        "baseline_green_pct": baseline_green_pct,
    }


# ----------------------------------------------------
# 6. Results Dashboard (shown whenever results exist)
# ----------------------------------------------------
if st.session_state.optimised and st.session_state.results is not None:
    res = st.session_state.results
    df = res["df"]
    cost_saved = res["cost_saved"]
    co2_saved_kg = res["co2_saved_kg"]
    optimised_green_pct = res["optimised_green_pct"]
    baseline_green_pct = res["baseline_green_pct"]

    st.success("Optimisation complete — this is the value your customers (and you) unlock with Axle.")



    st.subheader("📈 What You Can Offer Customers — And What You Gain Behind the Scenes")

    st.markdown("""
    ### The customer gets:
    - The **same comfort and convenience**
    - **Lower bills**  
    - Completely **effortless flexibility**

    ### Your business gets:
    - **Hedge protection** against volatile peaks  
    - **Increased margin** on flexible customers  
    - Access to **wholesale, capacity, DSO & ESO markets**  
    - A **differentiated, stickier proposition** that keeps customers for longer  
    """)


    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(
            soft_metric("£ Saved (per day)", fmt_money(cost_saved)),
            unsafe_allow_html=True,
        )

    with k2:
        st.markdown(
            soft_metric("CO₂ Avoided (per day)", fmt_co2(co2_saved_kg)),
            unsafe_allow_html=True,
        )

    with k3:
        delta_pp = optimised_green_pct - baseline_green_pct
        value = f"{optimised_green_pct:0.1f}% <span style='font-size:0.85rem; color:#16a34a;'>({delta_pp:+0.1f} pp)</span>"
        st.markdown(
            soft_metric("Load in Green Hours", value),
            unsafe_allow_html=True,
        )

    st.markdown("### Baseline vs Optimised Load Profile")
    st.caption("Your customer gets the same comfort and readiness — you avoid peak exposure and unlock new value.")
    fig = plot_optimised(df)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # -----------------------------
    # Scaling Slider
    # -----------------------------
    st.subheader("🏘️ Portfolio Impact — What This Looks Like at Scale")

    st.markdown("""
    Scale today’s optimisation from **one customer** to your **full consumer base**.

    This shows your portfolio-level upside:

    - Total **wholesale risk avoided**  
    - Total **CO₂ avoided**  

    This reveals the **strategic and commercial value** of flexibility at scale —  
    not just per household.
    """)


    n_homes = st.slider(
        "How many homes should this optimisation represent?",
        min_value=1000,
        max_value=1000000,
        value=1000,
        step=1000,
    )

    scaled_cost = cost_saved * n_homes
    scaled_co2  = co2_saved_kg * n_homes

    colA, colB = st.columns(2)

    with colA:
        st.markdown(
            soft_metric(
                "Total £ Savings (per day)",
                fmt_money(scaled_cost)
            ),
            unsafe_allow_html=True
        )

    with colB:
        st.markdown(
            soft_metric(
                "Total CO₂ Avoided (per day)",
                fmt_co2(scaled_co2)
            ),
            unsafe_allow_html=True
        )

# ----------------------------------------------------
# Footer
# ----------------------------------------------------
st.divider()
st.caption("""
This demo illustrates how Axle enables partners to offer cheaper, cleaner,
automated energy experiences — while improving portfolio economics and accessing new value streams.
""")
