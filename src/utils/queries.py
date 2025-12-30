import pandas as pd
import numpy as np


# Finding amount of exported waste by grouping of Middle Level Code
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
        .apply(
            lambda g: pd.Series(
                {
                    "mean_ship": g["mean_ship"].sum(),
                    "std_ship": np.sqrt(
                        np.sum((g["std_ship"] ** 2) / g["Years_of_shipment"])
                    ),
                    "Years_of_shipment": g[
                        "Years_of_shipment"
                    ].max(),  # or sum, depending on meaning
                }
            )
        )
        .reset_index()
        .sort_values(by="mean_ship", ascending=False)
        .head(amount_to_show)
    )


# Unravels the Middle level Code into Bottom Level Code data, either grouped or raw
def examine_potential_of_middle_level_shipment_data(
    df,
    transport: str,
    countries: list,
    middle_level_code: str,
    disposal_only: bool,
    grouped_data: bool,
):
    mask = (
        (df["Import/export"] == transport)
        & (df["Country reporting"].isin(countries))
        & (df["To or from country"].isin(countries))
        & (df["Middle_Level_Code"] == middle_level_code)
        & (df["Disposal and recovery code"].str.startswith("D"))
    )
    if grouped_data:
        return (
            df[mask]
            .groupby(
                [
                    "Country reporting",
                    "Import/export",
                    "To or from country",
                    "Disposal and recovery code",
                    "Middle_Level_Code",
                    "Middle_Level_Description",
                    "Bottom_Level_Code",
                    "Bottom_Level_Description",
                    "LoW_Code",
                    "LoW_Description",
                ]
            )
            .apply(
                lambda g: pd.Series(
                    {
                        "mean_ship": g["mean_ship"].sum(),
                        "std_ship": np.sqrt(
                            np.sum((g["std_ship"] ** 2) / g["Years_of_shipment"])
                        ),
                        "Years_of_shipment": g[
                            "Years_of_shipment"
                        ].max(),  # or sum, depending on meaning
                    }
                )
            )
        )
    else:
        return df[mask]
