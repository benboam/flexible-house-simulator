import pandas as pd
from datetime import datetime

# --------------------------
# EV BASELINE
# --------------------------

def build_ev_baseline(date, timestamps, arrival_time, ev_kwh_needed, power_kw=7):
    df = pd.DataFrame({"timestamp": timestamps})
    df["ev_kwh"] = 0.0

    arrival_dt = datetime.combine(date, arrival_time)
    slot_kwh = power_kw * 0.5
    remaining = ev_kwh_needed

    for ts in df["timestamp"]:
        if ts >= arrival_dt and remaining > 0:
            charge = min(slot_kwh, remaining)
            df.loc[df["timestamp"] == ts, "ev_kwh"] = charge
            remaining -= charge

    return df


# --------------------------
# HOUSEHOLD BASELOAD
# --------------------------

def build_household_baseline(date, timestamps):
    df = pd.DataFrame({"timestamp": timestamps})
    df["house_kwh"] = 0.125  # 0.25kW always-on → 0.125 kWh/30min

    # Morning bump
    morning_range = pd.date_range(
        datetime.combine(date, datetime.min.time()).replace(hour=6),
        datetime.combine(date, datetime.min.time()).replace(hour=8),
        freq="30min",
        inclusive="left"
    )
    df.loc[df["timestamp"].isin(morning_range), "house_kwh"] += (0.5 / len(morning_range))

    # Evening bump
    evening_range = pd.date_range(
        datetime.combine(date, datetime.min.time()).replace(hour=17),
        datetime.combine(date, datetime.min.time()).replace(hour=21),
        freq="30min",
        inclusive="left"
    )
    df.loc[df["timestamp"].isin(evening_range), "house_kwh"] += (1.0 / len(evening_range))

    return df


# ---------------------------------------------------
#  HEAT PUMP BASELINE (SEASONAL + FLEXIBLE WINDOW)
# ---------------------------------------------------

def estimate_daily_heat_demand(date):
    """
    Approximate daily heat energy needed (kWh) based on month.
    Very rough but realistic enough for residential modelling.
    """
    month = date.month

    if month in [12, 1, 2]:          # Winter
        return 18     # kWh/day
    elif month in [3, 4, 11]:        # Shoulder cold
        return 12
    elif month in [5, 10]:           # Mild
        return 7
    elif month in [6, 7, 8]:         # Summer – mostly hot water only
        return 4
    else:
        return 6


def build_heatpump_baseline(date, timestamps, morning_window, evening_window, cop=3.0):
    """
    Builds half-hourly heat pump energy demand (kWh).
    
    - morning_window: (start_time, end_time)
    - evening_window: (start_time, end_time)
    - COP determines electrical load (thermal_kWh / COP)
    """

    daily_thermal_kwh = estimate_daily_heat_demand(date)
    df = pd.DataFrame({"timestamp": timestamps})
    df["hp_kwh"] = 0.0

    # Combine flex windows into one list
    windows = [morning_window, evening_window]

    # Count total number of valid half-hours
    valid_slots = []

    for (start_t, end_t) in windows:
        start = datetime.combine(date, start_t)
        end = datetime.combine(date, end_t)
        slots = df[(df["timestamp"] >= start) & (df["timestamp"] < end)]
        valid_slots.append(slots.index)

    # Flatten into a single list of indices
    valid_indices = [i for group in valid_slots for i in group]

    if len(valid_indices) == 0:
        return df

    # Convert thermal energy → electrical (divide by COP)
    total_elec_kwh = daily_thermal_kwh / cop
    slot_kwh = total_elec_kwh / len(valid_indices)

    df.loc[valid_indices, "hp_kwh"] = slot_kwh
    return df