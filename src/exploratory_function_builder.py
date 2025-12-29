import pandas as pd
import numpy as np
from utils.load_dataset import load_dataset
from utils.load_dataset import load_shipment_data_with_EWC_codes
from utils.calculate_economic_potential import calculate_economic_potential_from_shipment
from utils.queries import examine_potential_of_middle_level_shipment_data
from utils.queries import find_exported_waste_for_disposal

%load_ext autoreload
%autoreload 2

pd.options.display.max_columns = 999
pd.options.display.max_rows = 25


wasgen = load_dataset("env_wasgen")
wastrt = load_dataset("env_wastrt")

def smart_format(x):
    if pd.isna(x):
        return ""
    if abs(x) >= 1_000_000:
        return f"{x/1_000_000:,.2f}M"   # millions
    elif abs(x) >= 1_000:
        return f"{x:,.0f}"             # thousands
    elif abs(x) >= 1:
        return f"{x:,.2f}"             # normal numbers
    else:
        return f"{x:.2f}"              # small numbers like 0.33

pd.options.display.float_format = smart_format

    
wasship = pd.read_excel(
    "../data/raw/Waste_shipment_data_imports_exports_20250927.xlsx", header=8
)

wasship.dtypes

low_to_ewc = pd.read_csv("../data/raw/LoW_to_EWC.csv", sep=";")
low_codes = pd.read_csv("../data/raw/LoW_codes.csv",sep=';')

merged_low_ewc = pd.merge(low_to_ewc,
                          low_codes,
                          how='outer',
                          on='LoW_Code'
                          )
merged_low_ewc.to_csv("../data/interim/EWC_LoW_codes.csv",sep=';',index=False)



ewc_low = pd.read_csv("../data/interim/EWC_LoW_codes.csv",sep=';',dtype=str)
ewc_low.dtypes

wasship_ewc = load_shipment_data_with_EWC_codes()

# Possible Data transformations

# Generation = Treatment + Export - Import + delta Stock change (=residual)
# Residual = G - (T+E-I)
# Large positive residual - > Under reported treatment
# Large negative residual -> Double counting or misclassification

wasship_ewc_pivoted = wasship_ewc.pivot_table(
    index=[
        "Country reporting",
        "Import/export",
        "To or from country",
        "Disposal and recovery code",
        "Hazardousness",
        "Top_Level_Code",
        "Top_Level_Description",
        "Middle_Level_Code",
        "Middle_Level_Description",
        "Bottom_Level_Code",
        "Bottom_Level_Description",
        'LoW_Code',
        'LoW_Description'
    ],
    columns="Year",
    values="Quantity in tonnes",
    aggfunc="sum",
).reset_index()


wasship_ewc_pivoted.dtypes
year_cols = wasship_ewc_pivoted.select_dtypes(include='number').columns

wasship_ewc_pivoted["mean_ship"] = wasship_ewc_pivoted[year_cols].mean(axis=1)
wasship_ewc_pivoted["std_ship"] = wasship_ewc_pivoted[year_cols].std(axis=1)
wasship_ewc_pivoted["Years_of_shipment"] = wasship_ewc_pivoted[year_cols].notna().sum(axis=1)
wasship_ewc_pivoted['First_year_shipment'] = wasship_ewc_pivoted[year_cols].apply(
    lambda row: row[row.notna()].index.min(),axis=1
)
wasship_ewc_pivoted['Last_year_shipment'] = wasship_ewc_pivoted[year_cols].apply(
    lambda row: row[row.notna()].index.max(),axis=1
)


wasship_ewc_pivoted



wasship_ewc_pivoted.to_csv('../data/interim/wasship_pivoted.csv',sep=';',index=False)

EU_test = find_exported_waste_for_disposal(wasship_ewc_pivoted,[],25)
EU_economics = calculate_economic_potential_from_shipment(EU_test,[],20)
EU_examine = examine_potential_of_middle_level_shipment_data(wasship_ewc_pivoted,'Export',['Italy','Germany'],'12.1')

nordics_test = find_exported_waste_for_disposal(wasship_ewc_pivoted,['Finland','Sweden','Denmark','Norway'],20)
nordics_economics = calculate_economic_potential_from_shipment(nordics_test,'nordics_test')
nordics_test_examine = examine_potential_of_middle_level_shipment_data(wasship_ewc_pivoted,'Export',['Denmark','Sweden'],'06.2')
den_nor_effluent_sludge = examine_potential_of_middle_level_shipment_data(wasship_ewc_pivoted,'Export',['Denmark','Norway'],'03.2')

nordics_economics.to_csv('../data/interim/Nordic_shipment_economic_potential.csv',sep=';',index=False)


nordics_economics.to_csv('../data/processed/Nordic_shipment_economic_potential.csv',sep=';',index=False)
nordics_test_examine.to_csv('../data/processed/Swe_Den_Non-Ferrous_Exp_Waste_For_Disposal.csv',sep=';',index=False,)
den_nor_effluent_sludge.to_csv('../data/processed/Nor_Den_Effluent_Sludge_Exp_Waste_For_Disposal.csv',sep=';',index=False,)



