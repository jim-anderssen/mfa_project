"""
data_loader.py

Functions for loading waste generation, SBS employment, and NUTS2 reference data.
"""

from enum import Enum
from pathlib import Path
from typing import Literal, Optional
import pandas as pd
import eurostat

from .io import INTERIM_DIR, RAW_DIR, PROCESSED_DIR


class ProxyType(Enum):
    """Economic proxy types for regional waste allocation."""
    EMPLOYMENT = 'employment'
    WAGES = 'wages'
    LABOUR_COSTS = 'labour_costs'


# Indicator codes in sbs_r_nuts2021 dataset
# Full names: EMP_LOC_NR = Persons employed in local units - number
#             LC_EMP_LOC_TEUR = Labour costs per person employed - thousand EUR
#             WAGE_LOC_MEUR = Wages and salaries - million EUR
SBS_INDICATORS_2021 = {
    'employment': 'EMP_LOC_NR',
    'labour_costs_per_person': 'LC_EMP_LOC_TEUR',
    'wages': 'WAGE_LOC_MEUR',
}


# Country code mapping (ISO 2-letter)
COUNTRY_MAP = {
    'Germany': 'DE', 'France': 'FR', 'Italy': 'IT', 'Spain': 'ES',
    'Poland': 'PL', 'Netherlands': 'NL', 'Belgium': 'BE', 'Sweden': 'SE',
    'Austria': 'AT', 'Czechia': 'CZ', 'Portugal': 'PT', 'Greece': 'EL',
    'Hungary': 'HU', 'Denmark': 'DK', 'Finland': 'FI', 'Slovakia': 'SK',
    'Ireland': 'IE', 'Croatia': 'HR', 'Lithuania': 'LT', 'Slovenia': 'SI',
    'Latvia': 'LV', 'Estonia': 'EE', 'Cyprus': 'CY', 'Luxembourg': 'LU',
    'Malta': 'MT', 'Bulgaria': 'BG', 'Romania': 'RO', 'United Kingdom': 'UK',
    'Norway': 'NO', 'Iceland': 'IS', 'Türkiye': 'TR', 'Serbia': 'RS',
    'North Macedonia': 'MK', 'Montenegro': 'ME', 'Albania': 'AL',
    'Bosnia and Herzegovina': 'BA', 'Kosovo*': 'XK', 'Liechtenstein': 'LI'
}

# Waste types to exclude (totals and aggregates)
EXCLUDE_WASTES = ['TOTAL', 'PRIM', 'SEC', 'TOT_X_MIN', 'W12-13']
EXCLUDE_NACE = ['TOTAL_HH', 'EP_HH', 'HH']

# Aggregate NACE codes to exclude when detailed subsectors are available.
# These aggregates would cause double-counting if included alongside their subsectors.
# - 'C' (manufacturing) aggregates C10-C12, C13-C15, C16, C17_C18, C19, C20-C22, C23, C24_C25, C26-C30, C31-C33
# - 'E' (water/waste) aggregates E36_E37_E39, E38
AGGREGATE_NACE = {'C', 'E'}


def load_waste_generation(filepath: str = None) -> pd.DataFrame:
    """
    Load and filter waste generation data (country × NACE × waste type).

    Excludes aggregate NACE codes (like 'C' for all manufacturing) to prevent
    double-counting with detailed subsectors (C10-C12, C16, C24_C25, etc.).

    Parameters
    ----------
    filepath : str, optional
        Path to CSV file. Defaults to interim/Generated_waste_per_nace_country.csv

    Returns
    -------
    pd.DataFrame
        Filtered waste generation data with country_code added
    """
    if filepath is None:
        filepath = INTERIM_DIR / 'Generated_waste_per_nace_country.csv'

    wasgen = pd.read_csv(filepath)
    wasgen['country_code'] = wasgen['country'].map(COUNTRY_MAP)

    # Filter to sector-specific waste
    wasgen_filtered = wasgen[
        (~wasgen['waste'].isin(EXCLUDE_WASTES)) &
        (~wasgen['waste'].str.contains('X_', na=False)) &
        (~wasgen['nace_r2'].isin(EXCLUDE_NACE)) &
        (wasgen['mean_wasgen'] > 0) &
        (wasgen['country_code'].notna())
    ].copy()

    # Check for countries that have aggregate NACE but no detailed subsectors
    # before filtering out aggregates (to warn about potential data loss)
    aggregate_subsectors = {
        'C': {'C10-C12', 'C13-C15', 'C16', 'C17_C18', 'C19',
              'C20-C22', 'C23', 'C24_C25', 'C26-C30', 'C31-C33'},
        'E': {'E36_E37_E39', 'E38'},
    }

    for agg_code, subsectors in aggregate_subsectors.items():
        countries_with_agg = set(wasgen_filtered[wasgen_filtered['nace_r2'] == agg_code]['country_code'])
        countries_with_subsectors = set(wasgen_filtered[
            wasgen_filtered['nace_r2'].isin(subsectors)
        ]['country_code'])
        countries_missing = countries_with_agg - countries_with_subsectors

        if countries_missing:
            print(f"Warning: {len(countries_missing)} countries have aggregate NACE '{agg_code}' "
                  f"but no detailed subsectors: {sorted(countries_missing)}")

    # Remove aggregate NACE codes to prevent double-counting with detailed subsectors
    # Example: 'C' (all manufacturing) would duplicate C16 + C17_C18 + C24_C25 + ...
    wasgen_filtered = wasgen_filtered[~wasgen_filtered['nace_r2'].isin(AGGREGATE_NACE)]

    return wasgen_filtered


def load_sbs_employment(use_cache: bool = True) -> pd.DataFrame:
    """
    Load SBS NUTS-2 employment data from Eurostat.

    Parameters
    ----------
    use_cache : bool
        If True, try to load from local cache first

    Returns
    -------
    pd.DataFrame
        SBS data with employment values and derived columns
    """
    cache_path = INTERIM_DIR / 'sbs_nuts2_raw.csv'

    if use_cache and cache_path.exists():
        sbs = pd.read_csv(cache_path)
    else:
        sbs = eurostat.get_data_df('sbs_r_nuts06_r2', flags=False)
        sbs.to_csv(cache_path, index=False)

    # Fix geo column name if needed
    geo_col = [c for c in sbs.columns if 'geo' in c.lower()][0]
    if geo_col != 'geo':
        sbs = sbs.rename(columns={geo_col: 'geo'})

    # Add derived columns
    sbs['country_code'] = sbs['geo'].str[:2]
    sbs['is_nuts2'] = sbs['geo'].str.len() == 4

    # Get employment values (most recent year with data)
    year_cols = [c for c in sbs.columns if str(c).isdigit()]
    sbs['employment'] = sbs[year_cols].bfill(axis=1).iloc[:, 0]

    return sbs


def load_nuts2_names() -> dict:
    """
    Load NUTS2 region names from Eurostat.

    Returns
    -------
    dict
        Mapping from NUTS2 code to region name
    """
    geo_labels_df = eurostat.get_dic('sbs_r_nuts06_r2', 'geo', frmt='df')

    # Filter to NUTS2 codes (4 characters, starting with letters)
    geo_labels_df = geo_labels_df[
        (geo_labels_df['val'].str.len() == 4) &
        (geo_labels_df['val'].str[:2].str.isalpha())
    ]

    return dict(zip(geo_labels_df['val'], geo_labels_df['descr']))


def load_recycling_potential(filepath: str = None) -> dict:
    """
    Load recycling potential index by waste type.

    Returns dictionary mapping waste codes to EUR/tonne values.
    """
    # Default values based on waste type characteristics
    waste_value_map = {
        'W061': 1000,   # Ferrous metals
        'W062': 1000,   # Non-ferrous metals
        'W063': 500,    # Mixed metals
        'W06': 800,     # All metallic wastes
        'W071': 1000,   # Glass
        'W072': 1000,   # Paper/cardboard
        'W073': 100,    # Rubber
        'W074': 100,    # Plastics
        'W075': 100,    # Wood
        'W076': 10,     # Textiles
        'W077': 1,      # PCB wastes
        'W08A': 300,    # WEEE
        'W081': 500,    # Discarded vehicles
        'W091': 10,     # Animal food waste
        'W092': 100,    # Green waste
        'W093': 10,     # Slurry/manure
        'W101': 10,     # Mixed municipal
        'W102': 10,     # Mixed/undifferentiated
        'W103': 10,     # Sorting residues
        'W10': 10,      # Mixed wastes total
        'W11': 10,      # Sludges
        'W121': 100,    # Construction mineral
        'W124': 10,     # Combustion wastes
        'W126': 100,    # Soils
        'W127': 10,     # Dredging spoils
        'W12A': 50,     # Mineral wastes
        'W12B': 50,     # Other mineral
        'W128_13': 50,  # Mineral treatment
        'W13': 50,      # Solidified wastes
        'W01-05': 50,   # Chemical/medical
        'W011': 100,    # Spent solvents
        'W012': 10,     # Acid/alkaline
        'W013': 100,    # Used oils
        'W02A': 10,     # Chemical wastes
        'W032': 10,     # Industrial sludges
        'W033': 10,     # Sludges from treatment
        'W05': 1,       # Health care
        'W06_07A': 500, # Recyclables
    }
    return waste_value_map


def get_sbs_nuts2_employment(sbs: pd.DataFrame, indicator: str = 'V16110') -> pd.DataFrame:
    """
    Filter SBS data to employment indicator and NUTS-2 regions.

    Parameters
    ----------
    sbs : pd.DataFrame
        Full SBS data from load_sbs_employment()
    indicator : str
        SBS indicator code (V16110 = Number of persons employed)

    Returns
    -------
    pd.DataFrame
        Filtered to NUTS-2 regions with positive employment
    """
    return sbs[
        (sbs['indic_sb'] == indicator) &
        (sbs['is_nuts2']) &
        (sbs['employment'] > 0)
    ].copy()


def load_sbs_nuts2021(use_cache: bool = True) -> pd.DataFrame:
    """
    Load SBS NUTS-2 data from Eurostat (NUTS 2021 version).

    This dataset includes:
    - Persons employed in local units
    - Labour costs per person employed (thousand EUR)
    - Wages and salaries (million EUR)

    Parameters
    ----------
    use_cache : bool
        If True, try to load from local cache first

    Returns
    -------
    pd.DataFrame
        SBS data with all indicators
    """
    cache_path = INTERIM_DIR / 'sbs_nuts2021_raw.csv'

    if use_cache and cache_path.exists():
        return pd.read_csv(cache_path)

    # Fetch from Eurostat
    sbs = eurostat.get_data_df('sbs_r_nuts2021', flags=False)

    # Fix geo column name if needed
    geo_col = [c for c in sbs.columns if 'geo' in c.lower()][0]
    if geo_col != 'geo':
        sbs = sbs.rename(columns={geo_col: 'geo'})

    # Cache raw data
    sbs.to_csv(cache_path, index=False)

    return sbs


def compute_sbs_proxy(
    sbs_raw: pd.DataFrame,
    proxy_type: ProxyType = ProxyType.LABOUR_COSTS,
    year: Optional[int] = None
) -> pd.DataFrame:
    """
    Compute economic proxy values from SBS data.

    Parameters
    ----------
    sbs_raw : pd.DataFrame
        Raw SBS data from load_sbs_nuts2021()
    proxy_type : ProxyType
        Type of proxy to compute:
        - EMPLOYMENT: persons employed (headcount)
        - WAGES: wages and salaries (EUR)
        - LABOUR_COSTS: labour_costs_per_person × persons_employed (EUR)
    year : int, optional
        Specific year to use. If None, uses most recent available data.

    Returns
    -------
    pd.DataFrame
        Processed data with columns: geo, nace_r2, country_code, is_nuts2, proxy_value
    """
    df = sbs_raw.copy()

    # Identify year columns (numeric column names)
    year_cols = [c for c in df.columns if str(c).isdigit()]

    # Get value for specified year or most recent
    if year is not None and str(year) in year_cols:
        value_col = str(year)
        df['_value'] = df[value_col]
    else:
        # Use most recent year with data (backfill approach)
        df['_value'] = df[year_cols].bfill(axis=1).iloc[:, 0]

    # Get indicator column name (varies by dataset version)
    if 'indic_sbs' in df.columns:
        indic_col = 'indic_sbs'
    elif 'indic_sb' in df.columns:
        indic_col = 'indic_sb'
    else:
        indic_col = 'indicators'

    if proxy_type == ProxyType.EMPLOYMENT:
        indicator_name = SBS_INDICATORS_2021['employment']
        df_filtered = df[df[indic_col] == indicator_name].copy()
        df_filtered['proxy_value'] = df_filtered['_value']

    elif proxy_type == ProxyType.WAGES:
        indicator_name = SBS_INDICATORS_2021['wages']
        df_filtered = df[df[indic_col] == indicator_name].copy()
        # Convert million EUR to EUR
        df_filtered['proxy_value'] = df_filtered['_value'] * 1_000_000

    elif proxy_type == ProxyType.LABOUR_COSTS:
        # Need to merge employment and cost per person
        emp_indicator = SBS_INDICATORS_2021['employment']
        cost_indicator = SBS_INDICATORS_2021['labour_costs_per_person']

        df_emp = df[df[indic_col] == emp_indicator][
            ['geo', 'nace_r2', '_value']
        ].rename(columns={'_value': 'employment'})

        df_cost = df[df[indic_col] == cost_indicator][
            ['geo', 'nace_r2', '_value']
        ].rename(columns={'_value': 'cost_per_person'})

        # Merge and calculate total labour costs
        df_filtered = df_emp.merge(df_cost, on=['geo', 'nace_r2'], how='inner')

        # Log missing data warnings
        emp_regions = set(df_emp['geo'].unique())
        cost_regions = set(df_cost['geo'].unique())
        missing_costs = emp_regions - cost_regions
        if missing_costs:
            print(f"Warning: {len(missing_costs)} regions have employment but no labour cost data")

        # cost_per_person is in thousands EUR, so multiply to get EUR
        df_filtered['proxy_value'] = (
            df_filtered['employment'] * df_filtered['cost_per_person'] * 1000
        )

    # Add derived columns
    df_filtered['country_code'] = df_filtered['geo'].str[:2]
    df_filtered['is_nuts2'] = df_filtered['geo'].str.len() == 4

    # Drop rows with NaN or zero proxy values
    df_filtered = df_filtered.dropna(subset=['proxy_value'])
    df_filtered = df_filtered[df_filtered['proxy_value'] > 0]

    return df_filtered[['geo', 'nace_r2', 'country_code', 'is_nuts2', 'proxy_value']].copy()


def load_sbs_proxy(
    proxy_type: ProxyType = ProxyType.LABOUR_COSTS,
    dataset: Literal['sbs_r_nuts06_r2', 'sbs_r_nuts2021'] = 'sbs_r_nuts2021',
    use_cache: bool = True,
    nuts2_only: bool = True,
    year: Optional[int] = None
) -> pd.DataFrame:
    """
    Load SBS data and compute regional proxy values.

    This is the main entry point for getting proxy data for waste allocation.

    Parameters
    ----------
    proxy_type : ProxyType
        Economic proxy to use: EMPLOYMENT, WAGES, or LABOUR_COSTS
        Default: LABOUR_COSTS (recommended for capital-intensive industries)
    dataset : str
        Eurostat dataset code. Use 'sbs_r_nuts2021' for labour costs support.
    use_cache : bool
        Whether to use cached data
    nuts2_only : bool
        If True, filter to NUTS-2 level regions only
    year : int, optional
        Specific year to use

    Returns
    -------
    pd.DataFrame
        SBS data with proxy_value column ready for allocation

    Raises
    ------
    ValueError
        If proxy_type requires indicators not available in selected dataset
    """
    # Validate proxy type vs dataset
    if proxy_type in (ProxyType.LABOUR_COSTS, ProxyType.WAGES) and dataset == 'sbs_r_nuts06_r2':
        raise ValueError(
            f"{proxy_type.value} proxy requires 'sbs_r_nuts2021' dataset. "
            "The older 'sbs_r_nuts06_r2' dataset does not include these indicators."
        )

    # Load appropriate dataset
    if dataset == 'sbs_r_nuts2021':
        sbs_raw = load_sbs_nuts2021(use_cache=use_cache)
        sbs_proxy = compute_sbs_proxy(sbs_raw, proxy_type=proxy_type, year=year)
    else:
        # Use legacy loader and convert to same format
        sbs_raw = load_sbs_employment(use_cache=use_cache)
        sbs_filtered = get_sbs_nuts2_employment(sbs_raw)
        sbs_proxy = sbs_filtered[['geo', 'nace_r2', 'country_code', 'is_nuts2']].copy()
        sbs_proxy['proxy_value'] = sbs_filtered['employment']

    # Filter to NUTS-2 if requested
    if nuts2_only:
        sbs_proxy = sbs_proxy[
            (sbs_proxy['is_nuts2']) &
            (sbs_proxy['proxy_value'] > 0)
        ].copy()

    return sbs_proxy
