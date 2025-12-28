import pandas as pd
import numpy as np
from utils import load_dataset
from utils.find_economic_potential import find_economic_potential_from_shipment

pd.options.display.max_columns = 999

wasgen = load_dataset("env_wasgen")
wastrt = load_dataset("env_wastrt")


wasship = pd.read_excel(
    "../data/raw/Waste_shipment_data_imports_exports_20250927.xlsx", header=8
)

low_to_ewc = pd.read_csv("../data/raw/LoW_to_EWC.csv", sep=";")

wasship.head()
wasship.rename(columns={"European List of Waste code": "LoW_Code"}, inplace=True)

low_to_ewc.head()
low_to_ewc["LoW_Code"] = low_to_ewc["LoW_Code"].str.replace(" ", "")

wasship_ewc = pd.merge(
    wasship,
    low_to_ewc[["LoW_Code", "Bottom_Level_Code", "Bottom_Level_Description"]],
    how="inner",
    on="LoW_Code",
)

wasship_ewc = pd.merge(wasship, low_to_ewc, how="inner", on="LoW_Code")


num_cols = wasship_ewc.select_dtypes(include=[np.number]).columns
wasship_ewc[num_cols] = wasship_ewc[num_cols].astype(float)
wasship_ewc = wasship_ewc.apply(pd.to_numeric, errors="coerce")
wasship_ewc["Quantity in kg per capita"] = pd.to_numeric(
    wasship_ewc["Quantity in kg per capita"], errors="coerce"
)
wasship_ewc.head().dtypes
export = wasship_ewc[wasship_ewc["Import/export"] == "Export"]
export_disposal = wasship_ewc[
    (wasship_ewc["Import/export"] == "Export")
    & (wasship_ewc["Disposal and recovery code"].str.startswith("D"))
]


export_disposal.groupby(
    ["Bottom_Level_Description", "Country reporting", "To or from country", "Notes"]
)["Quantity in tonnes"].mean().sort_values(ascending=False).reset_index().head(50)
export.groupby(["Bottom_Level_Description", "Country reporting", "To or from country"])[
    "Quantity in kg per capita"
].sum().sort_values(ascending=False).reset_index().head(50)

wasship_ewc["Middle_Level_Description"].unique()
metal_wastes = wasship_ewc[
    wasship_ewc["Middle_Level_Description"] == "Metal wastes non-ferrous"
]
metal_wastes.groupby(
    ["Middle_Level_Description", "Country reporting", "To or from country"]
)["Quantity in tonnes"].sum().sort_values(ascending=False).reset_index().head(50)

fin_swe_metal_waste = wasship_ewc[
    (wasship_ewc["Middle_Level_Description"] == "Metal wastes non-ferrous")
    & (
        (wasship_ewc["Country reporting"] == "Sweden")
        | (wasship_ewc["Country reporting"] == "Finland")
    )
    & (
        (wasship_ewc["To or from country"] == "Sweden")
        | (wasship_ewc["To or from country"] == "Finland")
    )
]

fin_swe_metal_waste.groupby(
    [
        "Bottom_Level_Description",
        "Country reporting",
        "To or from country",
        "Disposal and recovery code",
    ]
)["Quantity in tonnes"].mean().sort_values(ascending=False).reset_index().head(50)
fin_swe_metal_waste["Notes"].value_counts()

wasgen[0]


# Data transformations

# Generation = Treatment + Export - Import + delta Stock change (=residual)
# Residual = G - (T+E-I)
# Large positive residual - > Under reported treatment
# Large negative residual -> Double counting or misclassification

wasgen[0].head()
wasgen[2]["waste"]

# Example metal wastes ferrous
gen_nonfer = wasgen[0][wasgen[0]["waste"] == "W062"]
trt_nonfer = wastrt[0][wastrt[0]["waste"] == "W062"]

wasship_ewc.head()
wasship_ewc["Middle_Level_Description"].unique()
ship_fer = wasship_ewc[
    wasship_ewc["Middle_Level_Description"] == "Metal wastes ferrous"
]
ship_nonfer = wasship_ewc[
    wasship_ewc["Middle_Level_Description"] == "Metal wastes non-ferrous"
]

imp_nonfer = ship_nonfer[ship_nonfer["Import/export"] == "Import"]
exp_nonfer = ship_nonfer[ship_nonfer["Import/export"] == "Export"]

imp_fer = ship_fer[ship_fer["Import/export"] == "Import"]
exp_fer = ship_fer[ship_fer["Import/export"] == "Export"]


nonfer = ship_nonfer.pivot_table(
    index=[
        "Country reporting",
        "Import/export",
        "To or from country",
        "Disposal and recovery code",
    ],
    columns="Year",
    values="Quantity in tonnes",
    aggfunc="sum",
).reset_index()

fer = ship_fer.pivot_table(
    index=[
        "Country reporting",
        "Import/export",
        "To or from country",
        "Disposal and recovery code",
    ],
    columns="Year",
    values="Quantity in tonnes",
    aggfunc="sum",
).reset_index()

fer["mean_ship"] = fer.select_dtypes(include="number").mean(axis=1)
fer.sort_values(by="mean_ship", ascending=False).reset_index().head(20)

nonfer["mean_ship"] = nonfer.select_dtypes(include="number").mean(axis=1)
nonfer.sort_values(by="mean_ship", ascending=False).reset_index().head(20)

nonfer["Disposal and recovery code"].value_counts()

wasship_ewc_pivoted = wasship_ewc.pivot_table(
    index=[
        "Country reporting",
        "Import/export",
        "To or from country",
        "Disposal and recovery code",
        # "Hazardousness",
        "Middle_Level_Code",
        "Middle_Level_Description",
    ],
    columns="Year",
    values="Quantity in tonnes",
    aggfunc="sum",
).reset_index()

wasship_ewc_bottom_level = wasship_ewc.pivot_table(
    index=[
        "Country reporting",
        "Import/export",
        "To or from country",
        "Disposal and recovery code",
        # "Hazardousness",
        "Middle_Level_Code",
        "Middle_Level_Description",
        "Bottom_Level_Code",
        "Bottom_Level_Description",
    ],
    columns="Year",
    values="Quantity in tonnes",
    aggfunc="sum",
).reset_index()

wasship_ewc_pivoted["mean_ship"] = wasship_ewc_pivoted.select_dtypes(
    include="number"
).mean(axis=1)
wasship_ewc_pivoted["std_ship"] = wasship_ewc_pivoted.select_dtypes(
    include="number"
).std(axis=1)
wasship_ewc_bottom_level["mean_ship"] = wasship_ewc_bottom_level.select_dtypes(
    include="number"
).mean(axis=1)
wasship_ewc_bottom_level["std_ship"] = wasship_ewc_bottom_level.select_dtypes(
    include="number"
).std(axis=1)

ship_disp = wasship_ewc_pivoted[
    wasship_ewc_pivoted["Disposal and recovery code"].str.startswith("D")
]
ship_disp_exp = wasship_ewc_pivoted[
    (wasship_ewc_pivoted["Disposal and recovery code"].str.startswith("D"))
    & (wasship_ewc_pivoted["Import/export"] == "Export")
]

nordics_balt = [
    "Sweden",
    "Finland",
    "Denmark",
    "Norway",
    "Estonia",
    "Latvia",
    "Lithuania",
]
ship_disp_exp_nordics_balt = ship_disp_exp[
    (ship_disp_exp["Country reporting"].isin(nordics_balt))
    & (ship_disp_exp["To or from country"].isin(nordics_balt))
]
middle_level_recycling_potential = (
    ship_disp_exp_nordics_balt.groupby(
        [
            "Country reporting",
            "Import/export",
            "To or from country",
            "Middle_Level_Code",
            "Disposal and recovery code",
            "Middle_Level_Description",
        ]
    )[["mean_ship", "std_ship"]]
    .sum()
    .reset_index()
    .sort_values(by="mean_ship", ascending=False)
    .head(20)
)


den_nor = ["Denmark", "Norway"]
ship_den_nor = wasship_ewc_bottom_level[
    (wasship_ewc_bottom_level["Country reporting"].isin(den_nor))
    & (wasship_ewc_bottom_level["To or from country"].isin(den_nor))
]
ship_disp_den_nor_32 = ship_den_nor[
    (ship_den_nor["Disposal and recovery code"].str.startswith("D"))
    & (ship_den_nor["Middle_Level_Code"] == 3.2)
]
ship_den_nor["Middle_Level_Code"].unique()

ship_disp_den_nor_32[ship_disp_den_nor_32["Import/export"] == "Export"]


recycling_pot = pd.read_csv("../data/raw/EWC-recycling potential2.csv", sep=";")
recycling_pot.rename(columns={"Category_Code": "Middle_Level_Code"}, inplace=True)
recycling_pot.dtypes

middle_level_recycling_potential["Middle_Level_Code"] = (
    middle_level_recycling_potential["Middle_Level_Code"]
    .astype(str)
    .str.replace(r"^([1-9])\.", r"0\1.", regex=True)
)

middle_level_recycling_potential["Middle_Level_Code"] = (
    middle_level_recycling_potential["Middle_Level_Code"].astype(str)
)
middle_level_recycling_potential.dtypes


test = find_economic_potential_from_shipment(
    middle_level_recycling_potential, "Nordic_shipment_economic_potential"
)
test

recycling_potential_nordics = pd.merge(
    middle_level_recycling_potential,
    recycling_pot[["Middle_Level_Code", "Recycling_Potential_Index"]],
    how="inner",
    on="Middle_Level_Code",
)

recycling_potential_nordics["Economic_potential"] = (
    recycling_potential_nordics["mean_ship"]
    * recycling_potential_nordics["Recycling_Potential_Index"]
)
recycling_potential_nordics.rename(
    columns={
        "mean_ship": "Mean yearly shipments [tonnes]",
        "std_ship": "Std. yearly shipments [tonnes]",
        "Recycling_Potential_Index": "Recycling_Potential_Index [€/tonnes]",
        "Economic_potential": "Economic_potential [€/year]",
    },
    inplace=True,
)


recycling_potential_nordics["Economic_potential [€/year]"] = (
    recycling_potential_nordics["Economic_potential [€/year]"].round(-3)
)
recycling_potential_nordics["Uncertainty factor"] = 0.66
recycling_potential_nordics["Min_economic potential [€/year]"] = (
    (
        recycling_potential_nordics["Mean yearly shipments [tonnes]"]
        - recycling_potential_nordics["Std. yearly shipments [tonnes]"]
    )
    * recycling_potential_nordics["Recycling_Potential_Index [€/tonnes]"]
    * (1 - recycling_potential_nordics["Uncertainty factor"])
)
recycling_potential_nordics["Max_economic potential [€/year]"] = (
    (
        recycling_potential_nordics["Mean yearly shipments [tonnes]"]
        + recycling_potential_nordics["Std. yearly shipments [tonnes]"]
    )
    * recycling_potential_nordics["Recycling_Potential_Index [€/tonnes]"]
    * (1 - recycling_potential_nordics["Uncertainty factor"])
)

recycling_potential_nordics.sort_values(
    by="Economic_potential [€/year]", ascending=False
)
recycling_potential_nordics.sort_values(
    by="Economic_potential [€/year]", ascending=False
).to_csv("../data/interim/nordic_shipment_rceycling_potential_test.csv", index=False)
