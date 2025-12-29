import pandas as pd


def calculate_economic_potential_from_shipment(shipment_df, save_filename: str):
    # Read recycling potential data
    recycling_potential_df = pd.read_csv(
        "../data/raw/EWC-recycling potential.csv", sep=";"
    )
    recycling_potential_df.rename(
        columns={"Category_Code": "Middle_Level_Code"}, inplace=True
    )

    # Merge recycling potential with shipment data
    economic_potential_shipment = pd.merge(
        shipment_df,
        recycling_potential_df[["Middle_Level_Code", "Recycling_Potential_Index"]],
        how="inner",
        on="Middle_Level_Code",
    )
    economic_potential_shipment["Uncertainty factor"] = 0.33

    # Calculate economic potential
    economic_potential_shipment["Economic_potential"] = (
        economic_potential_shipment["mean_ship"]
        * economic_potential_shipment["Recycling_Potential_Index"]
    ).round(-3)

    # Min range
    economic_potential_shipment["Min_economic_potential"] = (
        (
            economic_potential_shipment["mean_ship"]
            - economic_potential_shipment["std_ship"]
        )
        * economic_potential_shipment["Recycling_Potential_Index"]
        * (1 - economic_potential_shipment["Uncertainty factor"])
    ).round(-3)

    # Max range
    economic_potential_shipment["Max_economic_potential"] = (
        (
            economic_potential_shipment["mean_ship"]
            + economic_potential_shipment["std_ship"]
        )
        * economic_potential_shipment["Recycling_Potential_Index"]
        * (1 + economic_potential_shipment["Uncertainty factor"])
    ).round(-3)

    economic_potential_shipment[
        [
            "mean_ship",
            "std_ship",
            "Economic_potential",
            "Min_economic_potential",
            "Max_economic_potential",
        ]
    ] = economic_potential_shipment[
        [
            "mean_ship",
            "std_ship",
            "Economic_potential",
            "Min_economic_potential",
            "Max_economic_potential",
        ]
    ].round(-2)

    economic_potential_shipment.rename(
        columns={
            "mean_ship": "Mean yearly shipments [tonnes]",
            "std_ship": "Std. yearly shipments [tonnes]",
            "Recycling_Potential_Index": "Recycling_Potential_Index [€/tonnes]",
            "Economic_potential": "Economic_potential [€/year]",
            "Min_economic_potential": "Min_economic_potential [€/year]",
            "Max_economic_potential": "Max_economic_potential [€/year]",
        },
        inplace=True,
    )

    economic_potential_shipment.sort_values(
        by="Economic_potential [€/year]", ascending=False
    ).to_csv(f"../data/interim/{save_filename}.csv", index=False)
    return economic_potential_shipment.sort_values(
        by="Economic_potential [€/year]", ascending=False
    )
