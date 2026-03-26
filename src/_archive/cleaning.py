import pandas as pd


def extract_tonnes_row(df, unit: str):
    """Separate Tonnes-rows from eurostat dataset"""
    if f"{unit}" in df["unit"].unique():
        return df[df["unit"] == "T"]
    else:
        return df


def calculate_mean_std_and_length(df, datacode: str):
    """Calculates mean, std.dev and length of timeseries from dataset"""
    try:
        df = extract_tonnes_row(df)
    except Exception as e:
        print(f"Exception: {e}")
        pass
    try:
        year_cols = df.select_dtypes(include="number").columns
        df[f"mean_{datacode[4:]}"] = df[year_cols].mean(axis=1)
        df[f"std_{datacode[4:]}"] = df[year_cols].std(axis=1)
        df["Number_of_years"] = df[year_cols].notna().sum(axis=1)
    except Exception as e:
        print(f"Exception: {e}")
    return df
