import pandas as pd
import numpy as np


def find_exported_waste_for_disposal(df, countries: list, amount_to_show: int):
    if countries == []:
        countries = df["Country reporting"].unique()
    mask = (
        (df["Import/export"] == "Export")
        & (df["Country reporting"].isin(countries))
        & (df["To or from country"].isin(countries))
        & (df["Disposal and recovery code"].str.startswith("D"))
    )
    masked_df = df[mask]
    return (
        masked_df.groupby(
            [
                "Country reporting",
                "Import/export",
                "To or from country",
                "Middle_Level_Code",
                "Disposal and recovery code",
                "Middle_Level_Description",
            ]
        )
        .agg(
            mean_ship=("mean_ship", "sum"),
            std_ship=("std_ship", "sum"),
            Years_of_shipment=("Years_of_shipment", "max"),
        )
        .reset_index()
        .sort_values(by="mean_ship", ascending=False)
        .head(amount_to_show)
    )


def examine_potential_of_middle_level_shipment_data(
    df, transport: str, countries: list, middle_level_code: str
):
    mask = (
        (df["Import/export"] == transport)
        & (df["Country reporting"].isin(countries))
        & (df["To or from country"].isin(countries))
        & (df["Middle_Level_Code"] == middle_level_code)
    )
    return df[mask]
