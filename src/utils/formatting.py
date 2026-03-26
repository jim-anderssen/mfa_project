import pandas as pd


def smart_format(x):
    if pd.isna(x):
        return ""
    if abs(x) >= 1_000_000:
        return f"{x / 1_000_000:,.2f}M"  # millions
    elif abs(x) >= 1_000:
        return f"{x:,.0f}"  # thousands
    elif abs(x) >= 1:
        return f"{x:,.2f}"  # normal numbers
    else:
        return f"{x:.2f}"  # small numbers like 0.33
