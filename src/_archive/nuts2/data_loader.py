"""
data_loader.py

Functions for loading waste generation, SBS employment, and NUTS2 reference data.
"""

from pathlib import Path
import pandas as pd
import eurostat

from ..io_file import INTERIM_DIR, RAW_DIR, PROCESSED_DIR


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


def load_waste_generation(filepath: str = None) -> pd.DataFrame:
    """
    Load and filter waste generation data (country × NACE × waste type).

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
