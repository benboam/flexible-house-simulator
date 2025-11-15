import requests
import pandas as pd

# --------------------------
# 1. Carbon Intensity
# --------------------------


def fetch_carbon_intensity(date_str):
    """Fetch half-hourly carbon intensity for a given day."""
    url = f"https://api.carbonintensity.org.uk/intensity/date/{date_str}"
    r = requests.get(url)
    data = r.json()["data"]

    rows = []
    for entry in data:
        rows.append(
            {
                "timestamp": pd.to_datetime(entry["from"]),
                "carbon_intensity": entry["intensity"]["actual"]
                or entry["intensity"]["forecast"],
                "carbon_index": entry["intensity"]["index"],
            }
        )
    return pd.DataFrame(rows)


# --------------------------
# 2. Generation Mix (half-hourly)
# --------------------------


def fetch_generation_mix(date_str):
    """Fetch half-hourly generation mix (wind, solar, etc) for a given day."""
    start = f"{date_str}T00:00Z"
    end = f"{date_str}T23:59Z"
    url = f"https://api.carbonintensity.org.uk/generation/{start}/{end}"
    r = requests.get(url)
    data = r.json()["data"]

    rows = []
    for entry in data:
        mix = entry["generationmix"]
        timestamp = pd.to_datetime(entry["from"])
        wind = next(x["perc"] for x in mix if x["fuel"] == "wind")
        solar = next(x["perc"] for x in mix if x["fuel"] == "solar")
        rows.append({"timestamp": timestamp, "wind_share": wind, "solar_share": solar})
    return pd.DataFrame(rows)


# --------------------------
# 3. Price Data
# --------------------------


def fetch_prices(date_str):
    """
    Fetch half-hourly Agile Flex prices for a given day using Octopus Energy API.
    Returns a DataFrame with columns:
        timestamp, price
    """
    base_url = (
        "https://api.octopus.energy/v1/products/AGILE-24-10-01/"
        "electricity-tariffs/E-1R-AGILE-24-10-01-C/standard-unit-rates/"
    )

    period_from = f"{date_str}T00:00Z"
    period_to = f"{date_str}T23:59Z"

    url = f"{base_url}?period_from={period_from}&period_to={period_to}"

    rows = []

    print("DEBUG: starting fetch_prices for", date_str)
    while url:
        print("DEBUG: GET", url)
        r = requests.get(url)
        print("DEBUG: status_code", r.status_code)
        try:
            data = r.json()
        except Exception as e:
            print("DEBUG: json() failed:", e)
            print("DEBUG: response text (truncated):", r.text[:400])
            return pd.DataFrame(columns=["timestamp", "price"])

        if r.status_code != 200:
            print(f"DEBUG: Agile price fetch failed: {r.status_code}")
            print("DEBUG: response body:", data)
            return pd.DataFrame(columns=["timestamp", "price"])

        results = data.get("results", [])
        print("DEBUG: results count on page =", len(results))

        for entry in results:
            valid_from = pd.to_datetime(entry.get("valid_from"))
            price = entry.get("value_inc_vat", entry.get("value_exc_vat"))
            rows.append({"timestamp": valid_from, "price": price})

        url = data.get("next", None)

    if len(rows) == 0:
        print("DEBUG: no price rows found; returning empty DataFrame")
        return pd.DataFrame(columns=["timestamp", "price"])

    df = pd.DataFrame(rows)
    df = df.sort_values("timestamp").reset_index(drop=True)

    return df


def load_grid_data(date_str):
    Carb_int = fetch_carbon_intensity(date_str)
    gen_mix = fetch_generation_mix(date_str)
    prices = fetch_prices(date_str)

    df = Carb_int.merge(gen_mix, on="timestamp", how="left")
    df = df.merge(prices, on="timestamp", how="left")

    return df


if __name__ == "__main__":
    day = "2025-11-11"
    df = load_grid_data(day)

    print(df.head())
