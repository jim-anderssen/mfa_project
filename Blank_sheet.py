import pandas as pd
import numpy as np
import os
import eurostat
import src.integration.prodcom_linker as linker

from src.loaders import load_dataset, extend_eurostat_dataset
from src.utils import smart_format

%load_ext autoreload
%autoreload 2

pd.options.display.max_columns = 999
pd.options.display.max_rows = 150
pd.options.display.float_format = smart_format

print(os.getcwd())
wasgen = load_dataset("env_wasgen")

wasgen = extend_eurostat_dataset(wasgen, ["nace_r2", "waste", "geo"])
wasgen[(wasgen['hazard']=='HAZ_NHAZ')&(wasgen['nace_r2']=='C24_C25')&(wasgen['waste']=='TOTAL')&(wasgen['geo'].isin(['SE','FI','PL','DE','IT']))]
wasgen[(wasgen['hazard']=='HAZ_NHAZ')&(wasgen['nace_r2']=='C24_C25')&(wasgen['waste']=='W124')&(wasgen['geo'].isin(['SE','FI','PL','DE','IT']))]
wasgen[(wasgen['hazard']=='HAZ_NHAZ')&(wasgen['nace_r2']=='C24_C25')&(wasgen['waste']=='W061')&(wasgen['geo'].isin(['SE','FI','PL','DE','IT']))]
wasgen[(wasgen['hazard']=='HAZ_NHAZ')&(wasgen['nace_r2']=='C24_C25')&(wasgen['geo'].isin(['SE']))]
wasgen[(wasgen['hazard']=='HAZ_NHAZ')&(wasgen['nace_r2']=='C24_C25')&(wasgen['geo'].isin(['FI']))]


wastrt = load_dataset("env_wastrt")
wasfac = load_dataset("env_wasfac")

wastrt[0]
test = extend_eurostat_dataset(wastrt, ['waste','wst_oper','geo'])
test = extend_eurostat_dataset(wasfac, ['indic_env','wst_oper','geo'])
test['wst_oper_description'].unique()



wasgen[0]
wasgen[2]["waste"].rename(
    columns={"val": "waste", "descr": "waste_description"}, inplace=True
)
wasgen[2]["nace_r2"].rename(
    columns={"val": "nace_r2", "descr": "nace_r2_activity"}, inplace=True
)
wasgen[2]["geo"].rename(columns={"val": "geo", "descr": "country"}, inplace=True)
gen = pd.merge(wasgen[0], wasgen[2]["waste"], how="inner", on="waste")

gen = pd.merge(gen, wasgen[2]["nace_r2"], how="inner", on="nace_r2")

gen = pd.merge(gen, wasgen[2]["geo"], how="inner", on="geo")


col = gen.pop("waste_description")
gen.insert(gen.columns.get_loc("waste") + 1, "waste_description", col)

col2 = gen.pop("nace_r2_activity")
gen.insert(gen.columns.get_loc("nace_r2") + 1, "nace_r2_activity", col2)
gen

col3 = gen.pop("country")
gen.insert(gen.columns.get_loc("geo") + 1, "country", col3)
gen


gen.columns
year_cols_and_mean_std = [
    "2004",
    "2006",
    "2008",
    "2010",
    "2012",
    "2014",
    "2016",
    "2018",
    "2020",
    "2022",
    "mean_wasgen",
    "std_wasgen",
]

nace_waste = (
    gen.groupby(
        [
            "nace_r2",
            "nace_r2_activity",
            "waste",
            "waste_description",
        ]
    )[year_cols_and_mean_std]
    .sum()
    .reset_index()
    .sort_values(by="mean_wasgen", ascending=False)
    .round(-3)
)

nace_waste_country = (
    gen.groupby(
        [
            "country",
            "nace_r2",
            "nace_r2_activity",
            "waste",
            "waste_description",
        ]
    )[year_cols_and_mean_std]
    .sum()
    .reset_index()
    .sort_values(by="mean_wasgen", ascending=False)
    .round(-3)
)

nace_waste_country["nace_r2"].unique()

countries_not_eu = nace_waste_country[
    ~nace_waste_country["country"].isin(
        [
            "European Union - 28 countries (2013-2020)",
            "European Union - 27 countries (from 2020)",
        ]
    )
]

countries_not_eu.to_csv(
    "data/interim/Generated_waste_per_nace_country.csv", sep=",", index=False
)

c24_25 = countries_not_eu[countries_not_eu["nace_r2"] == "C24_C25"]
c24_25.head(50).to_csv(
    "data/processed/Generated_waste_per_nace_C24_C25_country.csv", sep=",", index=False
)


# PRDOCOM trade data

# Map prodcom data (4-digits 2440 etc. )to IED activity codes?

prodcom = load_dataset('ds-059359')

prodcom = extend_eurostat_dataset(prodcom,['reporter','product','indicators'])
prodcom['product_description'].unique()
prodcom['product_description'].value_counts()
prodcom['indicators_description'].unique()
prodcom[2]['indicators']
prodcom[2]['product'][prodcom[2]['product']['val'].str.startswith('24')]['descr'].unique()
prodcom[0]['nace_group'] = prodcom[0]['product'].str[:4]

dk = prodcom[0][(prodcom[0]['reporter'].isin(['SE','DK']))&(prodcom[0]['indicators']=='PRODQNT')]
dk.groupby(['reporter','nace_group'])[dk.columns[4:34]].sum()


prodcom.to_csv('data/raw/prodcom.csv',index=False)
dk.dtypes


wasgen[(wasgen['nace_r2']=='C17_C18')&(wasgen['geo'].isin(['FI','SE']))&(wasgen['waste']=='W072')]#.groupby(['geo','waste'])['mean_wasgen'].sum()

wasgen[(wasgen['nace_r2']=='C24_C25')&(wasgen['geo'].isin(['FI','SE']))&(wasgen['waste']=='W124')].groupby(['geo','waste'])['mean_wasgen'].sum()

#
facility_clusters = pd.read_csv('data/processed/facility_clusters.csv')
facility_clusters_summary = pd.read_csv('data/processed/facility_cluster_summary.csv')
facility_waste = pd.read_csv('data/processed/facility_waste_allocated.csv')

# Combustion wastes
facility_waste[facility_waste['waste_type']=='W124'].sort_values('allocated_tonnes',ascending=False).head(20)

# SSAB waste profile
facility_waste[facility_waste['facility_name']=='SSAB EMEA AB i Luleå - Installation']
facility_waste[(facility_waste['nace']=='C17_C18')&(facility_waste['country']=='SE')]['facility_name'].unique()
facility_waste[facility_waste['facility_name'].str.contains('Skoghalls Bruk - Installation')]


facility_clusters[facility_clusters['cluster']==1].sort_values(by='total_tonnes',ascending=False).head(10)
facility_clusters[facility_clusters['cluster']==1]['facility_name'].unique()

facility_clusters_summary[['dominant_nace','nace_description']].drop_duplicates()

facility_waste[facility_waste['facility_name'].isin(facility_clusters[facility_clusters['cluster']==1]['facility_name'].unique())]

facility_clusters[facility_clusters['cluster']==1].groupby('geo_subgroup')['total_tonnes'].sum().sort_values(ascending=False)



# MFA
mfa = load_dataset('env_ac_mfa')
mfa[0]
mfa[['material','material_description']].drop_duplicates()
mfa = extend_eurostat_dataset(mfa,['indic_env','material','unit','geo'])
mfa.to_csv('data/raw/material_flow.csv',index=False)

mfain = load_dataset('env_ac_mfain')
mfain[0]


df = linker.get_prodcom_for_waste_analysis(['24.10', '24.42'], countries=['SE', 'DE'],start_year=2020,end_year=2023)
df

prodcom_mapped = linker.batch_map_prodcom_to_waste(                                              
      prodcom[0],                                                                 
      quantity_col='value',                                                            
      product_col='product'                                                            
  )  

prodcom['indicators'].unique()
test6 = prodcom[(prodcom['reporter'].isin(['FI','SE']))&(prodcom['indicators']=='APRODQNT')&(prodcom['product'].str.startswith('24'))].fillna(0)
test6.groupby(['reporter'])[test6.columns[7:37]].sum()


def countries_waste_facility_capacity(df,countries:list):
    df = df[(df['geo'].str[:2].isin(countries))]
    df['country'] = df['geo'].str[:2]
    return df.groupby(['country','indic_env_description','wst_oper_description'])[df.columns[7:17]].sum()

def subtract_matrices(df,level:str, country1:str, country2:str):
    pivot = df.unstack(level).fillna(0)
    return (pivot.xs(country1,level=level,axis=1) - pivot.xs(country2,level=level,axis=1)).reset_index().round()



wasgen = extend_eurostat_dataset(load_dataset('env_wasgen'), ['hazard','nace_r2','waste','geo'])
test4 = wasgen[(wasgen['geo'].isin(['FI','SE']))&(wasgen['waste']=='PRIM')]
test4 = test4.groupby(['geo','nace_r2'])[test4.columns[9:19]].sum()



wasgen[wasgen['waste']=='W12A'].iloc[0,6]
wasgen[wasgen['waste']=='W126']
wasgen[['waste','waste_description']].drop_duplicates()
wasgen[(wasgen['nace_r2']=='C24_C25')&(wasgen['geo']=='SE')].groupby(['waste','waste_description'])[wasgen.columns[9:19]].sum().to_csv('data/interim/SE_C24_25_waste_matrix.csv')
wasgen[(wasgen['nace_r2']=='C24_C25')&(wasgen['geo']=='FI')].groupby(['waste','waste_description'])[wasgen.columns[9:19]].sum()

test5 = subtract_matrices(test4,'geo')



#fin_swe.columns[9:19]

wastrt = load_dataset('env_wastrt')
wastrt['wst_oper_description'].unique()
wastrt = extend_eurostat_dataset(wastrt,['wst_oper','waste','geo'])
fin_swe = wastrt[wastrt['geo'].isin(['FI','SE'])]
test = fin_swe.groupby(['geo','wst_oper_description'])[fin_swe.columns[9:19]].sum().reset_index()
(test[test['geo']=='FI'].iloc[:,2:].fillna(0))-(test[test['geo']=='SE'].iloc[:,2:].fillna(0))

wasfac = load_dataset('env_wasfac')
wasfac = extend_eurostat_dataset(wasfac,['indic_env','wst_oper','geo'])



test2 = countries_waste_facility_capacity(wasfac,['FI','SE'])
wasfac.columns[7:17]



test3 = subtract_matrices(test2)



transfers = pd.read_csv('data/raw/F3_2_Transfers_Facilities.csv')

transfers.groupby(['EPRTR_SectorName'])['Pollutant'].unique().sort_values(ascending=False)
transfers['reportingYear'].unique()

pivoted_transfers = transfers.pivot_table(index=['EPRTR_SectorName','facilityName','Pollutant'],
               columns='reportingYear',
               values='transfers',
               aggfunc='sum')


pivoted_transfers.groupby(['EPRTR_SectorName','Pollutant']).count().sum(axis=1)

# Global Iron and Steel Tracker
plants_file = pd.ExcelFile('data/raw/Global iron and steel tracker/Plant-level-data-Global-Iron-and-Steel-Tracker-December-2025-V1.xlsx')
plants_file.sheet_names
plants = pd.read_excel(plants_file,sheet_name='Plant data')




    
def load_InS_data():
    root = 'data/raw/Global iron and steel tracker'
    InS = {}
    for i,file in enumerate(sorted(os.listdir(root))):
        xls = (pd.ExcelFile(os.path.join(root,file)))
        InS[i] = {
            'name': file,
            'xls': xls,
            'files':[pd.read_excel(xls,sheet_name=i) for i in xls.sheet_names]
            }
    for i,file in enumerate(InS.values()):
        print(InS[i]['name'])
        print(InS[i]['xls'].sheet_names)
        print()
    return InS

def get_specific_InS_file_content(file:str, InS:dict):
    names = []
    for i in InS.values():
        print(i['name'])
        if i['name'] == file:
            print('yes')

InS.values()

InS = load_InS_data()
InS.values()

    
get_specific_InS_file_content('Plant-level-data-Global-Iron-and-Steel-Tracker-December-2025-V1.xlsx',InS)



retriever = pd.read_excel('data/raw/Sweden A and C retriever export 2025 08.xlsx')
len(retriever['Företagsnamn'].unique())
retriever[retriever['Företagsnamn']=='SSAB EMEA AB']
retriever[retriever['SNI kodlista 1'].astype(str).str[:2]=='17']
retriever['SNI kodlista 1'].dtype#.values[0:2]


### HOW is it calculating the env_Wasgen data, yearly or summed all years?? I think it's not doing it properly!!
gva_allocated = pd.read_csv('data/processed/gva_sweden_c24_c25_waste_allocated.csv')
gva_allocated[gva_allocated['waste_type']=='TOTAL'].sort_values(by='allocated_tonnes',ascending=False).head(20)

gva_allocated.rename(columns={'waste_type':'waste'},inplace=True)

test = pd.merge(gva_allocated[gva_allocated['company_name'].str.startswith('SSAB')],wasgen[['waste','waste_description']].drop_duplicates(),how='inner',on='waste')
test.insert(5,'waste_description',test.pop('waste_description'))

wasgen[(wasgen['hazard']=='HAZ_NHAZ')&(wasgen['geo']=='SE')&(wasgen['nace_r2']=='C24_C25')]#[]


from src.allocation import run_gva_allocation_pipeline, load_gva_allocator
from src.allocation.gva_based_allocator_2 import load_gva_allocator as l_gva_2
from src.allocation.gva_based_allocator_1 import load_gva_allocator as l_gva_1


gva_alloction = run_gva_allocation_pipeline('data/raw/Sweden A and C retriever export 2025 08.xlsx','data/interim/Generated_waste_per_nace_country.csv','data/processed/gva_allocation/gva_allocation_sweden_c24_c25.csv',['SE'],['C24','C25'])


c24 = load_gva_allocator('data/raw/Sweden A and C retriever export 2025 08.xlsx','SE',['24','25'])

c17_1 = l_gva_1('data/raw/Sweden A and C retriever export 2025 08.xlsx','SE',['17'])
c17 = load_gva_allocator('data/raw/Sweden A and C retriever export 2025 08.xlsx','SE',['17'])




test = c24.allocate_waste(load_dataset('env_wasgen')[0],['SE'])
c17_alloc = c17.allocate_waste(load_dataset('env_wasgen')[0],['SE'])



c17_1_alloc = c17_1.allocate_waste(load_dataset('env_wasgen')[0],['SE'])
c17_2_alloc = c17_2.allocate_waste(load_dataset('env_wasgen')[0],['SE'])
c17_1_alloc.sort_values(by='allocated_tonnes',ascending=False).head(20)
c17_2_alloc[c17_2_alloc['waste_type']=='TOTAL'].sort_values(by='allocated_tonnes',ascending=False).head(20)


test.rename(columns={'waste_type':'waste'},inplace=True)
ssab = pd.merge(test[test['company_name'].str.startswith('SSAB')],wasgen[['waste','waste_description']].drop_duplicates(),how='inner',on='waste')
ssab.insert(5,'waste_description',ssab.pop('waste_description'))
ssab[ssab['year']==2020].sort_values(by='allocated_tonnes',ascending=False)


test[test['waste']=='TOTAL'].sort_values(by='allocated_tonnes',ascending=False).head(20)

wasgen[(wasgen['waste']=='W124')&(wasgen['geo']=='SE')&(wasgen['nace_r2']=='C24_C25')]


ewc_low = pd.read_csv('data/processed/lookuptables/EWC_LoW_codes.csv',sep=';')
ewc_low

from src.loaders.eprtr_emissions import load_all_emissions
emissions = load_all_emissions('data/raw')

ssab_air = emissions[(emissions['facility_name'].str.startswith('SSAB EMEA AB i Luleå',na=False))&(emissions['medium']=='AIR')]
ssab_air.pivot(columns='reporting_year',index = 'pollutant',values='release_kg')

grouped_emissions = emissions.groupby(['facility_name','eprtr_activity','pollutant','medium'])['release_kg'].sum().reset_index()
grouped_emissions[grouped_emissions['eprtr_activity'].str.startswith('2(b)')].groupby(['medium','pollutant'])['facility_name'].nunique().head(150)


co2_steel = grouped_emissions[grouped_emissions['eprtr_activity'].str.startswith('2(a)')]
len(co2_steel['facility_name'].unique())
len(co2_steel[co2_steel['pollutant'].str.contains('CO2')]['facility_name'].unique())


test_waste = pd.read_csv('data/processed/facility_waste_classified_all_20260202.csv')
test_waste[['facility_name','country','technology_regime','CO2','estimated_production_max_t','alloc_PRIM_tonnes']].sort_values(by='CO2',ascending=False).head(50)
test_waste.columns
test_waste['nace_2digit'].value_counts()

test_waste[test_waste['facility_name'].str.startswith('SSAB EMEA AB i Luleå',na=False)]
test_waste

steel_air = emissions[(emissions['medium']=='AIR')&(emissions['eprtr_activity']=='2(b)')]
steel_air

import matplotlib.pyplot as plt

plt.scatter(co2_zn['pollutant']=='Zinc and compounds (as Zn)', co2_zn['pollutant']=='Carbon dioxide')

  # Separate CO2 and Zn
co2 = co2_zn[co2_zn['pollutant'] == 'Carbon dioxide (CO2)'][['facility_id', 'reporting_year', 'release_kg']].rename(columns={'release_kg':
'co2'})
zn = co2_zn[co2_zn['pollutant'] == 'Zinc and compounds (as Zn)'][['facility_id', 'reporting_year', 'release_kg']].rename(columns={'release_kg':
'zn'})

# Merge to align by facility and year (keeps all individual yearly points)
scatter_data = co2.merge(zn, on=['facility_id', 'reporting_year'], how='inner')

# Create scatter plot
plt.figure(figsize=(10, 6))
plt.scatter(scatter_data['zn'], scatter_data['co2'], alpha=0.6)
plt.xlabel('Zinc and compounds (as Zn)')
plt.ylabel('Carbon dioxide (CO2)')
plt.title('CO2 vs Zinc emissions (all yearly values)')
plt.tight_layout()
plt.show()


import matplotlib.pyplot as plt                                                                                                    
import pandas as pd                                                                 
                                                                                                           
                                                                                                                                    
def plot_pollutants_vs_co2(emissions, eprtr_activity='2(b)', medium='AIR'):
    """                                                                                                                            
    Create scatter plots of all air pollutants against CO2 emissions.                                                            
    """
    # Filter data
    air_emissions = emissions[
        (emissions['medium'] == medium) &
        (emissions['eprtr_activity'] == eprtr_activity)
    ]

    # Get CO2 data
    co2 = air_emissions[air_emissions['pollutant'] == 'Carbon dioxide (CO2)'][
        ['facility_id', 'reporting_year', 'release_kg']
    ].rename(columns={'release_kg': 'CO2'})

    # Get all other pollutants
    other_pollutants = air_emissions[air_emissions['pollutant'] != 'Carbon dioxide (CO2)']['pollutant'].unique()

    # Create subplots
    n_cols = 3
    n_rows = (len(other_pollutants) + n_cols - 1) // n_cols
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows))
    axes = axes.flatten()

    # Plot each pollutant vs CO2
    for idx, pollutant in enumerate(other_pollutants):
        pollutant_data = air_emissions[air_emissions['pollutant'] == pollutant][
            ['facility_id', 'reporting_year', 'release_kg']
        ].rename(columns={'release_kg': pollutant})

        plot_data = pollutant_data.merge(co2, on=['facility_id', 'reporting_year'], how='inner')

        if len(plot_data) > 0:
            axes[idx].scatter(plot_data[pollutant], plot_data['CO2'], alpha=0.6)
            axes[idx].set_xlabel(pollutant)
            axes[idx].set_ylabel('CO2')
            axes[idx].set_title(f'CO2 vs {pollutant}')
        else:
            axes[idx].text(0.5, 0.5, 'No shared data', ha='center', va='center')

    # Hide unused subplots
    for idx in range(len(other_pollutants), len(axes)):
        axes[idx].set_visible(False)

    plt.tight_layout()
    return fig

# Usage
plot_pollutants_vs_co2(emissions)
plt.show()

F4_1 = pd.read_csv('data/raw/eprtr_2025/F4_1_WasteTransfers_National.csv')
F4 = pd.read_csv('data/raw/eprtr_2025/F4_2_WasteTransfers_Facilities.csv')
F4[F4['facilityName'].str.contains('SSAB EMEA AB i Luleå',na=False)]
F4[F4['facilityName'].str.contains('SSAB EMEA AB Oxelösund',na=False)]
F4[F4['facilityName'].str.contains('SSAB EMEA AB',na=False)]['facilityName'].unique()
F4[(F4['facilityName'].str.contains('SSAB EMEA AB'))&(F4['wasteClassification']=='HW')].pivot_table(
    columns='reportingYear',index=['facilityName','wasteTreatment','wasteClassification'],values='wasteTransfers')
F4['wasteClassification']

F4[F4['facilityName'].str.contains('Outokumpu Stainless AB, Avesta',na=False)].pivot_table(
    columns='reportingYear',index=['facilityName','wasteTreatment','wasteClassification'],values='wasteTransfers')
F4[F4['facilityName'].str.contains('Outokumpu Stainless AB, Degerfors',na=False)].pivot_table(
    columns='reportingYear',index=['facilityName','wasteTreatment','wasteClassification'],values='wasteTransfers')





F4_1[(F4_1['countryName']=='Sweden')&(F4_1['reportingYear']==2022)]['wasteTransfers'].sum()
wasgen[(wasgen['geo']=='SE')&(wasgen['waste']=='TOTAL')&(wasgen['hazard']=='HAZ_NHAZ')]['2022'].sum()
wasgen


F6 = pd.read_csv("data/raw/F6_1_IED_Installations.csv")
F6[['IEDAnnexIMainActivity','IEDMainActivityName']].drop_duplicates().sort_values(by='IEDAnnexIMainActivity')
F6[(F6['CountryName']=='Finland')&(F6['IEDAnnexIMainActivity']=='1.3')]
F6[(F6['CountryName']=='Finland')&(F6['City_of_Facility']=='Tornio')]['installationName'].unique()


emissions[(emissions['facility_name'].str.contains('SSAB EMEA AB i Luleå',na=False))&(emissions['medium']=='AIR')].pivot_table(
    columns='reporting_year',index='pollutant',values='release_kg')[2022].reset_index().sort_values(by=2022,ascending=False)

env_trdrrm = load_dataset(
    "env_trdrrm"
)  # Trade in recyclable raw materials (Maybe useful)

from src.analysis.one_off import compare_eprtr_wasgen

compare_eprtr_wasgen.compare()


multi_country_eprtr_wasgen_comparison = pd.read_csv('data/processed/eprtr_wasgen_comparison/multi_C24_C25.csv')
multi_country_eprtr_wasgen_comparison[multi_country_eprtr_wasgen_comparison['country']=='SE']
multi_country_eprtr_wasgen_comparison[multi_country_eprtr_wasgen_comparison['country']=='FI']