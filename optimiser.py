import pandas as pd
import numpy as np
from datetime import datetime


def _norm(series: pd.Series) -> pd.Series:
    """Min-max normalisation to [0, 1]."""
    if series.max() == series.min():
        return pd.Series(0.5, index=series.index)
    return (series - series.min()) / (series.max() - series.min())


def compute_scores(df: pd.DataFrame, opt_goal: str) -> pd.Series:
    """
    Compute a 'goodness score' per half-hour depending on the optimisation goal.
    Higher score = more desirable time to run flexible loads.
    """
    price_n = _norm(df["price"])
    carbon_n = _norm(df["carbon_intensity"])

    if opt_goal == "Cheapest energy":
        score = -price_n
    elif opt_goal == "Lowest carbon":
        score = -carbon_n
    elif opt_goal == "Balanced":
        score = -0.5 * price_n - 0.5 * carbon_n
    else:
        score = -price_n  # default to cheapest

    return score


def optimise_ev(df: pd.DataFrame,
                date_obj,
                arrival_time,
                depart_time,
                ev_kwh_needed: float,
                opt_goal: str,
                charger_kw: float = 7.0) -> pd.Series:
    """
    Optimise EV charging by shifting it into the best half-hours between
    arrival and departure, according to the chosen goal.
    """
    ev_opt = pd.Series(0.0, index=df.index)
    scores = compute_scores(df, opt_goal)

    times = df["timestamp"].dt.time

    if depart_time > arrival_time:
        mask = (times >= arrival_time) & (times < depart_time)
    else:
        # Wrap around midnight: charge from arrival → end of day, and start of day → depart
        mask = (times >= arrival_time) | (times < depart_time)

    candidate_idx = df.index[mask]
    if len(candidate_idx) == 0 or ev_kwh_needed <= 0:
        return ev_opt

    slot_kwh = charger_kw * 0.5  # 30-minute slot
    remaining = ev_kwh_needed

    # Sort candidate slots by score (best first)
    scores_candidate = scores.loc[candidate_idx]
    sorted_idx = scores_candidate.sort_values(ascending=False).index

    for i in sorted_idx:
        if remaining <= 0:
            break
        charge = min(slot_kwh, remaining)
        ev_opt.iloc[i] = charge
        remaining -= charge

    return ev_opt


def optimise_heatpump(df: pd.DataFrame,
                      hp_total_kwh: float,
                      opt_goal: str,
                      max_hours: int = 16) -> pd.Series:
    """
    Optimise heat pump electricity by concentrating it into the best
    half-hours of the day (subject to a cap on how many hours it can run).
    Uses the total daily HP kWh from the baseline for energy balance.
    """
    hp_opt = pd.Series(0.0, index=df.index)

    if hp_total_kwh <= 0:
        return hp_opt

    scores = compute_scores(df, opt_goal)

    # Allow HP to run in any half-hour, but limit to at most max_hours of runtime
    all_idx = df.index
    max_slots = min(len(all_idx), max_hours * 2)  # 2 slots per hour

    # Pick best slots
    best_idx = scores.sort_values(ascending=False).index[:max_slots]

    per_slot_kwh = hp_total_kwh / len(best_idx)

    hp_opt.loc[best_idx] = per_slot_kwh

    return hp_opt
