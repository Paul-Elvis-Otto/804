import os
import urllib.request

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

# CSVs are saved to "./data/raw/"
RAW_DATA_DIR = "./data/raw/"

ERS_POVERTY_2023 = "https://www.ers.usda.gov/media/5496/poverty-estimates-for-the-united-states-states-and-counties-2023.csv?v=66371"
ERS_UNEMP_MHI = "https://www.ers.usda.gov/media/5497/unemployment-and-median-household-income-for-the-united-states-states-and-counties-2000-23.csv?v=17146"
ERS_POP_2020_23 = "https://www.ers.usda.gov/media/5499/population-estimates-for-the-united-states-states-and-counties-2020-23.csv?v=15028"
ERS_EDU_1970_2023 = "https://www.ers.usda.gov/media/5495/educational-attainment-for-adults-age-25-and-older-for-the-united-states-states-and-counties-1970-2023.csv?v=54172"

CSV_FILES = {
    "poverty.csv": ERS_POVERTY_2023,
    "unemp.csv": ERS_UNEMP_MHI,
    "pop.csv": ERS_POP_2020_23,
    "edu.csv": ERS_EDU_1970_2023,
}


def ensure_csvs():
    """Download CSVs if they don't exist in RAW_DATA_DIR."""
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    for filename, url in CSV_FILES.items():
        filepath = os.path.join(RAW_DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Downloading {filename}...")
            urllib.request.urlretrieve(url, filepath)
            print(f"Saved to {filepath}")


def filter_states(df, fips_col):
    d = df.copy()
    d[fips_col] = pd.to_numeric(d[fips_col], errors="coerce")
    # ERS convention: state FIPS end with 000 (e.g., NC=37000). Exclude US=0.
    return d[(d[fips_col] != 0) & (d[fips_col] % 1000 == 0)]


def closest_states(df, features, target_abbr="NC", topn=7):
    sub = df[["abbr", "state"] + features].dropna().copy()
    X = sub[features].astype(float).values

    Xz = StandardScaler().fit_transform(X)

    target_row = sub.index[sub["abbr"] == target_abbr][0]
    target_vec = Xz[list(sub.index).index(target_row)]
    dists = np.linalg.norm(Xz - target_vec, axis=1)

    out = sub.copy()
    out["distance"] = dists
    out = out[out["abbr"] != target_abbr].sort_values("distance").head(topn)
    return out[["abbr", "state", "distance"] + features]


def main():
    ensure_csvs()

    poverty = pd.read_csv(os.path.join(RAW_DATA_DIR, "poverty.csv"))
    unemp = pd.read_csv(os.path.join(RAW_DATA_DIR, "unemp.csv"))
    pop = pd.read_csv(os.path.join(RAW_DATA_DIR, "pop.csv"), encoding="latin1")
    edu = pd.read_csv(os.path.join(RAW_DATA_DIR, "edu.csv"), encoding="latin1")

    poverty_s = filter_states(poverty, "FIPS_Code")
    unemp_s = filter_states(unemp, "FIPS_Code")
    pop_s = filter_states(pop.rename(columns={"FIPStxt": "FIPS_Code"}), "FIPS_Code")
    edu_s = filter_states(
        edu.rename(columns={"FIPS Code": "FIPS_Code", "Area name": "Area_Name"}),
        "FIPS_Code",
    )

    # --- Economics: poverty + income ---
    poverty_vars = ["PCTPOVALL_2023", "PCTPOV017_2023"]
    poverty_w = (
        poverty_s[poverty_s["Attribute"].isin(poverty_vars)]
        .pivot_table(
            index=["Stabr", "Area_Name"],
            columns="Attribute",
            values="Value",
            aggfunc="first",
        )
        .reset_index()
        .rename(columns={"Stabr": "abbr", "Area_Name": "state"})
    )

    unemp_vars = [
        "Unemployment_rate_2023",
        "Civilian_labor_force_2023",
        "Employed_2023",
        "Unemployed_2023",
        "Median_Household_Income_2022",
    ]
    unemp_w = (
        unemp_s[unemp_s["Attribute"].isin(unemp_vars)]
        .pivot_table(
            index=["State", "Area_Name"],
            columns="Attribute",
            values="Value",
            aggfunc="first",
        )
        .reset_index()
        .rename(columns={"State": "abbr", "Area_Name": "state"})
    )

    pop_vars = ["POP_ESTIMATE_2020", "POP_ESTIMATE_2023"]
    pop_w = (
        pop_s[pop_s["Attribute"].isin(pop_vars)]
        .pivot_table(
            index=["State", "Area_Name"],
            columns="Attribute",
            values="Value",
            aggfunc="first",
        )
        .reset_index()
        .rename(columns={"State": "abbr", "Area_Name": "state"})
    )
    pop_w["pop_growth_2020_2023_pct"] = (
        pop_w["POP_ESTIMATE_2023"] / pop_w["POP_ESTIMATE_2020"] - 1.0
    ) * 100

    edu_vars = [
        "Percent of adults who are not high school graduates, 2019-23",
        "Percent of adults who are high school graduates (or equivalent), 2019-23",
        "Percent of adults completing some college or associate degree, 2019-23",
        "Percent of adults with a bachelor's degree or higher, 2019-23",
    ]
    edu_w = (
        edu_s[edu_s["Attribute"].isin(edu_vars)]
        .pivot_table(
            index=["State", "Area_Name"],
            columns="Attribute",
            values="Value",
            aggfunc="first",
        )
        .reset_index()
        .rename(columns={"State": "abbr", "Area_Name": "state"})
    )

    df = (
        poverty_w.merge(unemp_w, on=["abbr", "state"], how="inner")
        .merge(pop_w, on=["abbr", "state"], how="inner")
        .merge(edu_w, on=["abbr", "state"], how="inner")
    )

    # exclude Puerto Rico if present
    df = df[df["abbr"] != "PR"].copy()

    # derived labor market intensity measures
    df["employed_per_1000"] = df["Employed_2023"] / df["POP_ESTIMATE_2023"] * 1000
    df["labor_force_per_1000"] = (
        df["Civilian_labor_force_2023"] / df["POP_ESTIMATE_2023"] * 1000
    )

    econ_features = ["Median_Household_Income_2022", "PCTPOVALL_2023", "PCTPOV017_2023"]
    edu_features = edu_vars
    labor_features = [
        "Unemployment_rate_2023",
        "employed_per_1000",
        "labor_force_per_1000",
    ]
    demo_features = ["POP_ESTIMATE_2023", "pop_growth_2020_2023_pct"]

    print("\nEconomics:\n", closest_states(df, econ_features))
    print("\nEducation:\n", closest_states(df, edu_features))
    print("\nLabour market:\n", closest_states(df, labor_features))
    print("\nDemographics (population-only):\n", closest_states(df, demo_features))


if __name__ == "__main__":
    main()
