import pandas as pd
from utils import load_dataset

pd.options.display.max_rows = 999
pd.options.display.max_columns = 999
pd.set_option("display.max_colwidth", None)


env_wasgen = load_dataset("env_wasgen")  # per country
env_wastrt = load_dataset("env_wastrt")  # per country

env_wasgen[0]

env_wasship = pd.read_excel(
    "data/Waste_shipment_data_imports_exports_20250927.xlsx", header=8
)  # per country
env_wasfac = load_dataset("env_wasfac")  # per nuts2 region
env_wastrdmp = load_dataset(
    "env_wastrdmp"
)  # Trade in waste by type of material and partner
env_waselee = load_dataset("env_waselee")  # WEEE by management operations
env_waseleeos = load_dataset(
    "env_waseleeos"
)  # WEEE by management operations, open scope
env_wasflow = load_dataset("env_wasflow")
env_wasst = load_dataset("env_wasst")


env_ac_mfa = load_dataset("env_ac_mfa")  # Useful
env_ac_mfadpo = load_dataset(
    "env_ac_mfadpo"
)  # domestic processed output, i.e emissions
env_ac_mfain = load_dataset("env_ac_mfain")  # MFA, main indiciators
env_ac_mid = load_dataset("env_ac_mid")  # Material import dependency (Useful)
env_ac_cur = load_dataset("env_ac_cur")  # Circular material use rate by material

env_ac_rp = load_dataset("env_ac_rp")  # Resource productivity
env_trdrrm = load_dataset(
    "env_trdrrm"
)  # Trade in recyclable raw materials (Maybe useful)

env_ac_pefasu = load_dataset(
    "env_ac_pefasu"
)  # Energy supply and use by NACE rev2 (Maybe useful)
env_ac_pefa04 = load_dataset(
    "env_ac_pefa04"
)  # Main indicators of phys energy flow accounts by NACE rev 2
env_wat_ind = load_dataset("env_wat_ind")

env_ac_rmefd = load_dataset(
    "env_ac_rmefd"
)  # Material footprints detail by final use of products
env_ac_rmefd[2]["indic_env"]

sbs_r_nuts06_r2 = load_dataset(
    "sbs_r_nuts06_r2"
)  # SBS data by NUTS 2 region and NACE Rev. 2 (2008-2020) (Useful to find regions?)
sbs_r_nuts2021 = load_dataset(
    "sbs_r_nuts2021"
)  # Enterprises by NUTS 2 region and NACE Rev. 2 (Useful?)
sbs_turn_ind_r2 = load_dataset(
    "sbs_turn_ind_r2"
)  # Turnover statistics for industry (NACE Rev. 2, B-E) (2008-2018) (Useful to get turnover for NACE cat.)

dt_cpa_n46_r2 = load_dataset(
    "dt_cpa_n46_r2"
)  # Turnover by product type for wholesale trade (NACE Rev. 2, G46) (2013-2018)


sbs_turn_ind_r2[2]["indic_sb"]

ds_059359 = load_dataset("ds-059359")

sts_intvd_m = load_dataset("sts_intvd_m")
sts_intvd_m[0]

bd_hgnace_r = load_dataset(
    "bd_hgnace_r"
)  # Business demography and high growth enterprises by NACE Rev. 2 activity and NUTS 3 region
bd_salge1_nace_r = load_dataset(
    "bd_salge1_nace_r"
)  # Employer business demography by NACE Rev. 2 activity and NUTS 3 region

nama_10r_2gdp = load_dataset(
    "nama_10r_2gdp"
)  # Gross domestic product (GDP) at current market prices by NUTS 2 region (
nama_10r_2gdp[0]

# Maybe? Employed persons in technology and knowledge-intensive sectors by NACE Rev. 2 activity and NUTS 2 region (2008-2026) (htec_emp_reg2)
nama_10r_2gva = load_dataset("nama_10r_2gva")

naio_10_fcp_u3 = load_dataset(
    "naio_10_fcp_u3"
)  # EU inter-country use table at basic prices (2018-2021) (naio_10_fcp_u3)
naio_10_fcp_u3[1]
naio_10_fcp_u3[2]["prd_ava"]

naio_10_cp1700 = load_dataset("naio_10_cp1700")
naio_10_cp1700[0]
naio_10_cp1700[2]["prd_use"]
naio_10_cp1700[2]["prd_ava"]

naio_10_cp1750 = load_dataset("naio_10_cp1750")
naio_10_cp1750[0]
naio_10_cp1750[2]["ind_use"]

sbs_r_nuts2021[2]["indic_sbs"]
sbs_r_nuts2021[0][sbs_r_nuts2021[0]["geo"].str.startswith("SE")]
sbs_r_nuts2021[0]["indic_sbs"].unique()

sbs_r_nuts2021[2]["geo"][
    sbs_r_nuts2021[2]["geo"]["val"].str.startswith("SE")
]  # [sbs_r_nuts2021[0]['geo'].str.startswith('SE')]

sbs_r_nuts06_r2[0]
sbs_r_nuts06_r2[0]["indic_sb"].unique()
sbs_r_nuts06_r2[2]["indic_sb"]

bd_hgnace_r[0]
bd_hgnace_r[2]["indic_sbs"]

sbs_turn_ind_r2[2]["indic_sb"]
sbs_turn_ind_r2[0]["geo"].unique()

dt_cpa_n46_r2[2]["cpa08"]
dt_cpa_n46_r2[0]["geo"].unique()

ds_059359[2]["product"]
ds_059359[0].query("product=='38322910'")

bd_salge1_nace_r[2]["indic_sbs"]

env_wat_ind[2][
    "wat_proc"
]  # Water use in the manufacturing industry by activity and supply category, (Maybe useful)

env_waselee[2]["wst_oper"]
env_waseleeos[2]["waste"]
env_wasflow[0]["stk_flow"]

env_ac_mfa[2]["material"]
env_ac_mfa[0]["material"].unique()

env_ac_mid[0]
env_ac_mid[2]["unit"]

env_wasfac[0]  # ['geo']
env_wasgen[0]


env_wastrt[2]["wst_oper"]
env_wastrt[0].groupby(["waste"])[
    ["2004", "2006", "2008", "2010", "2012", "2014", "2016", "2018", "2020", "2022"]
].mean().mean(axis=1)
env_wastrt[0]["wst_oper"].unique()

env_wasgen_mean = env_wasgen[0].select_dtypes(include="number").mean(axis=1)

env_wastrt[2]["wst_oper"]
env_wasgen[0].groupby(["waste"])[
    ["2004", "2006", "2008", "2010", "2012", "2014", "2016", "2018", "2020", "2022"]
].mean().mean(axis=1)

env_wastrt[0]
test = pd.read_csv("../data/raw/LoW_to_EWC.csv")


# Data transformations

# Generation = Treatment + Export - Import + delta Stock change (=residual)
# Residual = G - (T+E-I)
# Large positive residual - > Under reported treatment
# Large negative residual -> Double counting or misclassification

# Generation - Treatment
gen_minus_trt = (
    env_wasgen[0].groupby(["waste", "geo\\TIME_PERIOD"])["mean_wasgen"].sum()
    - env_wastrt[0].groupby(["waste", "geo\\TIME_PERIOD"])["mean_wastrt"].sum()
)
gen_minus_trt.sort_values(ascending=False).dropna().reset_index()

# Generation - Treatment - Exports + Imports

# Disposal Pressure indicator (DPI) = Disposal/Generation
dpi = (
    env_wastrt[0].groupby(["waste", "geo"])["mean_wastrt"].sum()
    / env_wasgen[0].groupby(["waste", "geo"])["mean_wasgen"].sum()
)
dpi.sort_values(ascending=False).reset_index().head(20)
env_wasgen[2]["geo"]
env_wasgen[2]["waste"]


# Waste exports per waste class (EWC-Stat 4) and NACE2
# Economic activity per NACE2 and NUTS2 region (Structural business statistics)
# Allocate waste to the NUTS2 region based on economic/employment/energy/production activity

# Find companies in highest producing NUTS2 region (Economic turnover, energy use etc.).
# (Maybe) Specify amount of R facilties in NUTS2 region
# Classify detailed waste (LoW or more) per EWC-Stat 4 waste in specific NUTS2 region.

# Find countries/regions with high material import dependency for specific product to place on market (Finding market).

# Forecast+ waste generation in 5 years

### Query of waste containing PCB
# env_wasgen[0].query("waste=='W077'").groupby(['nace_r2','geo'])['mean_wasgen'].sum().sort_values(ascending=False).reset_index().head(100)
env_wasgen[0]["waste"].unique()
