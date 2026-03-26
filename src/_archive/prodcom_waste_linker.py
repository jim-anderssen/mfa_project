"""
PRODCOM to Waste Stream Linker.

This module provides functions to:
1. Load PRODCOM production data from Eurostat Comext API
2. Map PRODCOM products to EWC-Stat waste categories
3. Estimate waste generation from production volumes
4. Track material flows from production to waste streams
5. Integrate with existing IED allocation and NUTS2 analysis

Integration:
- Uses IED-NACE-PRODCOM mappings from ied_nace_prodcom.py
- Extends EWC-Stat codes from ewc_stat_codes.py
- Compatible with NUTS2 allocation from nuts2/allocation.py
"""

import pandas as pd
import numpy as np
import requests
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Union
from dataclasses import dataclass, field
from io import StringIO

# Import mappings - handle both package and direct execution
try:
    from src.agents.mappings.prodcom_waste_mapping import (
        PRODCOM_TO_EWC,
        NACE_WASTE_GENERATION_FACTORS,
        get_ewc_for_prodcom,
        get_waste_factor_for_nace,
        get_prodcom_codes_for_nace,
        get_nace_from_prodcom,
        is_secondary_material,
    )
    from src.agents.mappings.ewc_stat_codes import (
        EWC_STAT_CODES,
        get_ewc_description,
    )
    from src.io_file import INTERIM_DIR, PROCESSED_DIR
except ModuleNotFoundError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / 'agents' / 'mappings'))
    from prodcom_waste_mapping import (
        PRODCOM_TO_EWC,
        NACE_WASTE_GENERATION_FACTORS,
        get_ewc_for_prodcom,
        get_waste_factor_for_nace,
        get_prodcom_codes_for_nace,
        get_nace_from_prodcom,
        is_secondary_material,
    )
    from ewc_stat_codes import EWC_STAT_CODES, get_ewc_description
    INTERIM_DIR = Path(__file__).parent.parent.parent / 'data' / 'interim'
    PROCESSED_DIR = Path(__file__).parent.parent.parent / 'data' / 'processed'


# ===== CONSTANTS =====

COMEXT_API_BASE = "https://ec.europa.eu/eurostat/api/comext/dissemination/sdmx/2.1"
PRODCOM_DATASET_ID = "DS-059358"  # Sold production, exports and imports

# PRODCOM indicator codes
PRODCOM_INDICATORS = {
    'PRODQNT': 'Production quantity (tonnes or units)',
    'PRODVAL': 'Production value (EUR)',
    'EXPQNT': 'Export quantity',
    'EXPVAL': 'Export value (EUR)',
    'IMPQNT': 'Import quantity',
    'IMPVAL': 'Import value (EUR)',
}

# EU27 country codes
EU27_COUNTRIES = [
    'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
    'DE', 'EL', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL',
    'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE'
]

# Nordics for focused analysis
NORDIC_COUNTRIES = ['SE', 'NO', 'FI', 'DK', 'IS']


# ===== DATA CLASSES =====

@dataclass
class MaterialFlow:
    """Represents a material flow from production to waste."""
    prodcom_code: str
    product_description: str
    production_quantity: float
    production_value: float
    country_code: str
    year: int
    ewc_primary: str
    waste_tonnes: float
    waste_factor: float
    byproducts: Dict[str, float] = field(default_factory=dict)
    mapping_quality: str = 'direct'
    nuts2_region: Optional[str] = None


# ===== DATA LOADING FUNCTIONS =====

def fetch_prodcom_data(
    countries: Optional[List[str]] = None,
    products: Optional[List[str]] = None,
    nace_prefix: Optional[str] = None,
    indicators: Optional[List[str]] = None,
    start_year: int = 2018,
    end_year: int = 2023,
    timeout: int = 120
) -> pd.DataFrame:
    """
    Fetch PRODCOM data from Eurostat Comext API.

    Parameters
    ----------
    countries : list, optional
        ISO 2-letter country codes (e.g., ['DE', 'SE', 'FR']).
        Defaults to EU27.
    products : list, optional
        8-digit PRODCOM codes (e.g., ['24103530', '24421100']).
        If None, fetches all products (may be slow).
    nace_prefix : str, optional
        Filter products by NACE prefix (e.g., '2410' for steel).
        Applied after fetching if products is None.
    indicators : list, optional
        Indicator codes: PRODQNT, PRODVAL, etc.
        Defaults to ['PRODQNT'] (production quantity).
    start_year : int
        Start year for time series.
    end_year : int
        End year for time series.
    timeout : int
        Request timeout in seconds.

    Returns
    -------
    pd.DataFrame
        PRODCOM data with columns: reporter, product, indicators, time_period, value

    Raises
    ------
    requests.HTTPError
        If API request fails.
    """
    if indicators is None:
        indicators = ['PRODQNT']

    if countries is None:
        countries = EU27_COUNTRIES

    all_data = []

    for country in countries:
        # Build URL - use empty product dimension to get all products
        # Format: freq.reporter.product.indicators (product empty = all)
        if products:
            product_filter = '+'.join(products)
            filter_string = f"A.{country}.{product_filter}.{'+'.join(indicators)}"
        else:
            # Empty product dimension fetches all
            filter_string = f"A.{country}..{'+'.join(indicators)}"

        url = f"{COMEXT_API_BASE}/data/{PRODCOM_DATASET_ID}/{filter_string}"

        params = {
            'startPeriod': str(start_year),
            'endPeriod': str(end_year),
            'format': 'SDMX-CSV',
        }

        try:
            response = requests.get(url, params=params, timeout=timeout)
            if response.status_code == 200:
                df = pd.read_csv(StringIO(response.text))
                df.columns = df.columns.str.lower()
                all_data.append(df)
        except requests.exceptions.RequestException as e:
            print(f"API request failed for {country}: {e}")
            continue

    if not all_data:
        return pd.DataFrame()

    df = pd.concat(all_data, ignore_index=True)

    # Standardize column names
    column_mapping = {
        'reporter': 'reporter',
        'product': 'product',
        'indicators': 'indicators',
        'time_period': 'time_period',
        'obs_value': 'value',
    }
    df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

    # Filter by NACE prefix if specified
    if nace_prefix and 'product' in df.columns:
        df = df[df['product'].astype(str).str.startswith(nace_prefix)]

    # Add NACE code derived from PRODCOM
    if 'product' in df.columns:
        df['nace_code'] = df['product'].astype(str).apply(get_nace_from_prodcom)

    return df


def load_prodcom_cached(
    cache_path: Optional[Path] = None,
    refresh: bool = False,
    **kwargs
) -> pd.DataFrame:
    """
    Load PRODCOM data with local file caching.

    Parameters
    ----------
    cache_path : Path, optional
        Cache file location. Defaults to data/interim/prodcom_cache.csv.
    refresh : bool
        Force refresh from API even if cache exists.
    **kwargs
        Arguments passed to fetch_prodcom_data().

    Returns
    -------
    pd.DataFrame
        PRODCOM data.
    """
    if cache_path is None:
        cache_path = INTERIM_DIR / 'prodcom_cache.csv'
    else:
        cache_path = Path(cache_path)

    if cache_path.exists() and not refresh:
        print(f"Loading cached data from {cache_path}")
        return pd.read_csv(cache_path)

    print("Fetching data from Comext API...")
    df = fetch_prodcom_data(**kwargs)

    # Cache the result
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cache_path, index=False)
    print(f"Cached to {cache_path}")

    return df


def get_prodcom_for_waste_analysis(
    nace_codes: List[str],
    countries: Optional[List[str]] = None,
    start_year: int = 2018,
    end_year: int = 2023,
    cache: bool = True
) -> pd.DataFrame:
    """
    Convenience function to load PRODCOM data for specific NACE sectors.

    Automatically determines relevant PRODCOM codes based on
    NACE code prefixes from the mapping dictionary.

    Parameters
    ----------
    nace_codes : list
        NACE codes (e.g., ['24.10', '24.42', '23.51']).
    countries : list, optional
        Country filter. Defaults to EU27.
    start_year : int
        Start year.
    end_year : int
        End year.
    cache : bool
        Whether to use caching.

    Returns
    -------
    pd.DataFrame
        Filtered PRODCOM data with production quantities.
    """
    # Get all PRODCOM codes for the requested NACE codes
    products = []
    for nace in nace_codes:
        products.extend(get_prodcom_codes_for_nace(nace))

    if not products:
        print(f"Warning: No PRODCOM mappings found for NACE codes: {nace_codes}")
        print("Using NACE prefix matching as fallback...")
        # Use available mapped codes that start with requested NACE prefixes
        nace_prefixes = [n.replace('.', '')[:2] for n in nace_codes]
        products = [
            code for code in PRODCOM_TO_EWC.keys()
            if code[:2] in nace_prefixes
        ]

    if not products:
        raise ValueError(f"No PRODCOM codes found for NACE codes: {nace_codes}")

    # Generate cache filename based on parameters
    cache_key = '_'.join(sorted(nace_codes)).replace('.', '')
    cache_path = INTERIM_DIR / f'prodcom_{cache_key}_{start_year}_{end_year}.csv'

    if cache and cache_path.exists():
        return pd.read_csv(cache_path)

    df = fetch_prodcom_data(
        countries=countries,
        products=products,
        start_year=start_year,
        end_year=end_year
    )

    if cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(cache_path, index=False)

    return df


# ===== MAPPING FUNCTIONS =====

def map_prodcom_to_waste(
    prodcom_code: str,
    production_quantity: float
) -> Dict:
    """
    Map a single PRODCOM code to waste generation estimate.

    Parameters
    ----------
    prodcom_code : str
        8-digit PRODCOM code.
    production_quantity : float
        Production quantity in tonnes.

    Returns
    -------
    dict
        Waste estimate with keys:
        - ewc_primary: Primary EWC-Stat code
        - ewc_secondary: List of secondary waste codes
        - waste_tonnes: Estimated total waste
        - byproducts: Dict of byproduct quantities
        - factor_used: Waste generation factor applied
        - mapping_quality: 'direct', 'nace_fallback', or 'none'
    """
    result = {
        'ewc_primary': None,
        'ewc_secondary': [],
        'waste_tonnes': 0.0,
        'byproducts': {},
        'factor_used': 0.0,
        'mapping_quality': 'none',
    }

    # Try direct PRODCOM mapping
    mapping = get_ewc_for_prodcom(prodcom_code)

    if mapping:
        result['ewc_primary'] = mapping.get('ewc_primary')
        result['ewc_secondary'] = mapping.get('ewc_secondary', [])
        result['factor_used'] = mapping.get('waste_factor', 0.0)
        result['mapping_quality'] = 'direct'

        # Calculate waste
        result['waste_tonnes'] = production_quantity * result['factor_used']

        # Calculate byproducts if available
        byproduct_factors = mapping.get('byproduct_factors', {})
        for byproduct, factor in byproduct_factors.items():
            result['byproducts'][byproduct] = production_quantity * factor

    else:
        # Fallback to NACE-level mapping
        nace_code = get_nace_from_prodcom(prodcom_code)
        factor = get_waste_factor_for_nace(nace_code, 'total')

        if factor > 0:
            result['factor_used'] = factor
            result['waste_tonnes'] = production_quantity * factor
            result['mapping_quality'] = 'nace_fallback'

            # Infer EWC code from NACE typical wastes
            from src.agents.mappings.ewc_stat_codes import NACE_TYPICAL_WASTES
            nace_section = f"C{nace_code.split('.')[0]}"
            typical_wastes = NACE_TYPICAL_WASTES.get(nace_section, [])
            if typical_wastes:
                result['ewc_primary'] = typical_wastes[0]
                result['ewc_secondary'] = typical_wastes[1:]

    return result


def batch_map_prodcom_to_waste(
    prodcom_df: pd.DataFrame,
    quantity_col: str = 'value',
    product_col: str = 'product'
) -> pd.DataFrame:
    """
    Map PRODCOM DataFrame to waste estimates.

    Parameters
    ----------
    prodcom_df : pd.DataFrame
        PRODCOM data with product column and quantity column.
    quantity_col : str
        Column containing production quantity.
    product_col : str
        Column containing PRODCOM codes.

    Returns
    -------
    pd.DataFrame
        Input data extended with waste mapping columns:
        - ewc_primary, ewc_secondary
        - waste_tonnes, byproduct_tonnes
        - waste_factor, mapping_quality
    """
    df = prodcom_df.copy()

    # Initialize new columns
    df['ewc_primary'] = None
    df['ewc_secondary'] = None
    df['waste_tonnes'] = 0.0
    df['waste_factor'] = 0.0
    df['mapping_quality'] = 'none'
    df['byproduct_tonnes'] = 0.0

    # Apply mapping to each row
    for idx, row in df.iterrows():
        prodcom_code = str(row[product_col])
        quantity = row[quantity_col] if pd.notna(row[quantity_col]) else 0.0

        mapping = map_prodcom_to_waste(prodcom_code, quantity)

        df.at[idx, 'ewc_primary'] = mapping['ewc_primary']
        df.at[idx, 'ewc_secondary'] = str(mapping['ewc_secondary']) if mapping['ewc_secondary'] else None
        df.at[idx, 'waste_tonnes'] = mapping['waste_tonnes']
        df.at[idx, 'waste_factor'] = mapping['factor_used']
        df.at[idx, 'mapping_quality'] = mapping['mapping_quality']
        df.at[idx, 'byproduct_tonnes'] = sum(mapping['byproducts'].values())

    return df


# ===== MATERIAL FLOW TRACKING =====

def track_material_flows(
    prodcom_df: pd.DataFrame,
    include_byproducts: bool = True
) -> pd.DataFrame:
    """
    Track complete material flows from production to waste.

    Creates a comprehensive flow table linking production
    volumes to waste generation estimates.

    Parameters
    ----------
    prodcom_df : pd.DataFrame
        PRODCOM data with mapped waste estimates (from batch_map_prodcom_to_waste).
    include_byproducts : bool
        Include detailed byproduct breakdown.

    Returns
    -------
    pd.DataFrame
        Material flow table with columns:
        - Source: reporter, time_period, nace_code, product, product_desc
        - Production: production_tonnes (value column)
        - Waste: ewc_primary, waste_tonnes
        - Factors: waste_factor, mapping_quality
    """
    # Ensure waste mapping is done
    if 'ewc_primary' not in prodcom_df.columns:
        prodcom_df = batch_map_prodcom_to_waste(prodcom_df)

    df = prodcom_df.copy()

    # Add product descriptions from mapping
    df['product_description'] = df['product'].apply(
        lambda x: PRODCOM_TO_EWC.get(x, {}).get('description', 'Unknown')
    )

    # Add EWC descriptions
    df['ewc_description'] = df['ewc_primary'].apply(
        lambda x: get_ewc_description(x) if x else 'Unmapped'
    )

    # Add material type
    df['material_type'] = df['product'].apply(
        lambda x: PRODCOM_TO_EWC.get(x, {}).get('material_type', 'unknown')
    )

    # Flag secondary materials
    df['is_secondary_material'] = df['product'].apply(is_secondary_material)

    # Select and order columns
    columns = [
        'reporter', 'time_period', 'nace_code', 'product', 'product_description',
        'value', 'ewc_primary', 'ewc_description', 'waste_tonnes',
        'waste_factor', 'mapping_quality', 'material_type', 'is_secondary_material'
    ]

    available_cols = [c for c in columns if c in df.columns]

    return df[available_cols]


def create_sankey_data(
    flows_df: pd.DataFrame,
    aggregation: str = 'nace'
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare data for Sankey diagram visualization.

    Parameters
    ----------
    flows_df : pd.DataFrame
        Material flow data from track_material_flows().
    aggregation : str
        Aggregation level: 'nace', 'ewc', or 'product'.

    Returns
    -------
    tuple
        (nodes_df, links_df) for Sankey visualization.
    """
    if aggregation == 'nace':
        group_col = 'nace_code'
    elif aggregation == 'ewc':
        group_col = 'ewc_primary'
    else:
        group_col = 'product'

    # Aggregate flows
    agg = flows_df.groupby([group_col, 'ewc_primary']).agg({
        'value': 'sum',
        'waste_tonnes': 'sum',
    }).reset_index()

    # Create nodes
    source_nodes = agg[group_col].unique()
    target_nodes = agg['ewc_primary'].dropna().unique()

    nodes = []
    for i, node in enumerate(source_nodes):
        nodes.append({'id': i, 'name': node, 'type': 'production'})
    for i, node in enumerate(target_nodes):
        nodes.append({'id': len(source_nodes) + i, 'name': node, 'type': 'waste'})

    nodes_df = pd.DataFrame(nodes)

    # Create links
    links = []
    node_id_map = {row['name']: row['id'] for _, row in nodes_df.iterrows()}

    for _, row in agg.iterrows():
        if pd.notna(row['ewc_primary']):
            links.append({
                'source': node_id_map[row[group_col]],
                'target': node_id_map[row['ewc_primary']],
                'value': row['waste_tonnes'],
            })

    links_df = pd.DataFrame(links)

    return nodes_df, links_df


# ===== WASTE ESTIMATION =====

def estimate_waste_generation(
    prodcom_df: pd.DataFrame,
    groupby: List[str] = ['reporter', 'nace_code', 'ewc_primary']
) -> pd.DataFrame:
    """
    Estimate waste generation from PRODCOM production data.

    Aggregates waste estimates by specified dimensions.

    Parameters
    ----------
    prodcom_df : pd.DataFrame
        PRODCOM data with waste mappings.
    groupby : list
        Columns to aggregate by.

    Returns
    -------
    pd.DataFrame
        Aggregated waste estimates with columns:
        - Groupby columns
        - total_production_tonnes
        - total_waste_tonnes
        - products_count
        - coverage_pct (% products with mapping)
    """
    # Ensure waste mapping is done
    if 'ewc_primary' not in prodcom_df.columns:
        prodcom_df = batch_map_prodcom_to_waste(prodcom_df)

    df = prodcom_df.copy()

    # Filter to valid groupby columns
    valid_groupby = [c for c in groupby if c in df.columns]

    if not valid_groupby:
        raise ValueError(f"None of the groupby columns found: {groupby}")

    # Aggregate
    agg = df.groupby(valid_groupby).agg({
        'value': 'sum',
        'waste_tonnes': 'sum',
        'product': 'nunique',
        'mapping_quality': lambda x: (x != 'none').sum() / len(x) * 100,
    }).reset_index()

    agg.columns = valid_groupby + [
        'total_production_tonnes',
        'total_waste_tonnes',
        'products_count',
        'coverage_pct',
    ]

    return agg


def estimate_waste_by_country_nace(
    prodcom_df: pd.DataFrame,
    year: Optional[int] = None
) -> pd.DataFrame:
    """
    Estimate waste generation by country and NACE sector.

    Convenience wrapper for common aggregation pattern.

    Parameters
    ----------
    prodcom_df : pd.DataFrame
        PRODCOM data with waste mappings.
    year : int, optional
        Filter to specific year.

    Returns
    -------
    pd.DataFrame
        Country x NACE waste estimates.
    """
    df = prodcom_df.copy()

    if year is not None and 'time_period' in df.columns:
        df = df[df['time_period'] == year]

    return estimate_waste_generation(df, groupby=['reporter', 'nace_code', 'ewc_primary'])


def compare_with_eurostat_wasgen(
    estimated_waste: pd.DataFrame,
    eurostat_wasgen: pd.DataFrame,
    country_col: str = 'reporter',
    waste_col: str = 'total_waste_tonnes'
) -> pd.DataFrame:
    """
    Compare PRODCOM-based estimates with Eurostat waste statistics.

    Validates estimates against official env_wasgen data.

    Parameters
    ----------
    estimated_waste : pd.DataFrame
        Waste estimates from estimate_waste_generation().
    eurostat_wasgen : pd.DataFrame
        Official waste generation data (from load_dataset('env_wasgen')).
    country_col : str
        Column containing country codes.
    waste_col : str
        Column containing estimated waste.

    Returns
    -------
    pd.DataFrame
        Comparison table with:
        - estimated_tonnes, reported_tonnes
        - difference_tonnes, difference_pct
        - coverage_flag
    """
    # Aggregate estimates by country
    est_by_country = estimated_waste.groupby(country_col)[waste_col].sum().reset_index()
    est_by_country.columns = ['country', 'estimated_tonnes']

    # Get reported waste by country (assumes eurostat_wasgen is prepared)
    if 'geo' in eurostat_wasgen.columns:
        rep_by_country = eurostat_wasgen.groupby('geo').agg({
            'mean_wasgen': 'sum'
        }).reset_index()
        rep_by_country.columns = ['country', 'reported_tonnes']
    else:
        print("Warning: Cannot compare - eurostat_wasgen format not recognized")
        return est_by_country

    # Merge
    comparison = est_by_country.merge(rep_by_country, on='country', how='outer')

    # Calculate differences
    comparison['difference_tonnes'] = comparison['estimated_tonnes'] - comparison['reported_tonnes']
    comparison['difference_pct'] = (
        comparison['difference_tonnes'] / comparison['reported_tonnes'] * 100
    ).round(1)

    comparison['coverage_flag'] = comparison.apply(
        lambda row: 'both' if pd.notna(row['estimated_tonnes']) and pd.notna(row['reported_tonnes'])
        else ('estimated_only' if pd.notna(row['estimated_tonnes']) else 'reported_only'),
        axis=1
    )

    return comparison


# ===== INTEGRATION WITH EXISTING CODE =====

def allocate_waste_using_ied_facilities(
    waste_estimates: pd.DataFrame,
    ied_filepath: str,
    nuts_level: int = 2
) -> pd.DataFrame:
    """
    Allocate waste estimates to regions using IED facility locations.

    Combines PRODCOM waste estimates with IED facility allocation.

    Parameters
    ----------
    waste_estimates : pd.DataFrame
        Country-level waste estimates.
    ied_filepath : str
        Path to IED installations CSV.
    nuts_level : int
        NUTS level for allocation (0, 1, 2, or 3).

    Returns
    -------
    pd.DataFrame
        Regional waste allocation.
    """
    from src.utils.ied_prodcom_linker import (
        load_ied_installations,
        count_facilities_by_nace_country,
        count_facilities_by_nace_nuts,
        assign_nuts_region,
    )

    # Load IED installations
    ied_df = load_ied_installations(ied_filepath)

    if nuts_level == 0:
        # Country-level allocation
        facility_counts = count_facilities_by_nace_country(ied_df)

        # Calculate facility share within each country
        total_by_country = facility_counts.groupby('country')['facility_count'].transform('sum')
        facility_counts['facility_share'] = facility_counts['facility_count'] / total_by_country

        # Merge with waste estimates
        allocated = waste_estimates.merge(
            facility_counts[['country', 'nace_code', 'facility_share', 'facility_count']],
            left_on=['reporter', 'nace_code'],
            right_on=['country', 'nace_code'],
            how='left'
        )

    else:
        # Regional allocation
        ied_df = assign_nuts_region(ied_df, nuts_level=nuts_level)
        facility_counts = count_facilities_by_nace_nuts(ied_df, f'nuts{nuts_level}')

        # Calculate facility share within each country
        facility_counts['country'] = facility_counts[f'nuts{nuts_level}'].str[:2]
        total_by_country_nace = facility_counts.groupby(
            ['country', 'nace_code']
        )['facility_count'].transform('sum')
        facility_counts['facility_share'] = facility_counts['facility_count'] / total_by_country_nace

        # Merge with waste estimates
        allocated = waste_estimates.merge(
            facility_counts,
            left_on=['reporter', 'nace_code'],
            right_on=['country', 'nace_code'],
            how='left'
        )

    # Allocate waste using facility share
    if 'total_waste_tonnes' in allocated.columns:
        allocated['allocated_waste_tonnes'] = (
            allocated['total_waste_tonnes'] * allocated['facility_share']
        )

    return allocated


def link_prodcom_to_existing_waste_data(
    prodcom_flows: pd.DataFrame,
    ewc_low_mapping_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Link PRODCOM flows to existing waste classification data.

    Creates complete linkage from:
    PRODCOM -> NACE -> EWC-Stat -> LoW codes

    Parameters
    ----------
    prodcom_flows : pd.DataFrame
        Material flows from track_material_flows().
    ewc_low_mapping_path : str, optional
        Path to EWC_LoW_codes.csv. Defaults to data/interim/EWC_LoW_codes.csv.

    Returns
    -------
    pd.DataFrame
        Complete linkage table.
    """
    if ewc_low_mapping_path is None:
        ewc_low_mapping_path = INTERIM_DIR / 'EWC_LoW_codes.csv'

    # Load EWC-LoW mapping
    try:
        ewc_low = pd.read_csv(ewc_low_mapping_path, sep=';')
    except FileNotFoundError:
        print(f"Warning: EWC-LoW mapping not found at {ewc_low_mapping_path}")
        return prodcom_flows

    # Extract the top-level EWC code (e.g., "06" from "W061")
    prodcom_flows = prodcom_flows.copy()
    prodcom_flows['ewc_top_level'] = prodcom_flows['ewc_primary'].str.extract(r'W(\d{2})')[0]

    # Merge with LoW codes
    linkage = prodcom_flows.merge(
        ewc_low[['Top_Level_Code', 'Middle_Level_Code', 'LoW_Code', 'LoW_Description']].drop_duplicates(),
        left_on='ewc_top_level',
        right_on='Top_Level_Code',
        how='left'
    )

    return linkage


# ===== ANALYSIS FUNCTIONS =====

def get_production_waste_ratio(
    flows_df: pd.DataFrame,
    groupby: str = 'nace_code'
) -> pd.DataFrame:
    """
    Calculate waste-to-production ratios.

    Parameters
    ----------
    flows_df : pd.DataFrame
        Material flow data.
    groupby : str
        Aggregation dimension.

    Returns
    -------
    pd.DataFrame
        Ratios by groupby dimension.
    """
    agg = flows_df.groupby(groupby).agg({
        'value': 'sum',
        'waste_tonnes': 'sum',
    }).reset_index()

    agg['waste_ratio'] = agg['waste_tonnes'] / agg['value']
    agg['waste_pct'] = agg['waste_ratio'] * 100

    return agg.sort_values('waste_tonnes', ascending=False)


def identify_high_waste_products(
    flows_df: pd.DataFrame,
    threshold_tonnes: float = 10000,
    threshold_ratio: float = 0.20
) -> pd.DataFrame:
    """
    Identify products with high waste generation.

    Parameters
    ----------
    flows_df : pd.DataFrame
        Material flow data.
    threshold_tonnes : float
        Minimum waste volume.
    threshold_ratio : float
        Minimum waste-to-production ratio.

    Returns
    -------
    pd.DataFrame
        High-waste products sorted by waste volume.
    """
    df = flows_df.copy()

    # Calculate ratio per product
    df['waste_ratio'] = df['waste_tonnes'] / df['value'].replace(0, np.nan)

    # Filter by thresholds
    high_waste = df[
        (df['waste_tonnes'] >= threshold_tonnes) |
        (df['waste_ratio'] >= threshold_ratio)
    ]

    return high_waste.sort_values('waste_tonnes', ascending=False)


def summarize_secondary_materials_flow(
    flows_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Summarize flows of secondary raw materials (NACE 38.32).

    Tracks materials recovery products that represent
    waste-to-resource transitions.

    Parameters
    ----------
    flows_df : pd.DataFrame
        Material flow data.

    Returns
    -------
    pd.DataFrame
        Secondary materials summary.
    """
    secondary = flows_df[flows_df['is_secondary_material'] == True].copy()

    if secondary.empty:
        print("No secondary materials found in flows data.")
        return pd.DataFrame()

    # Aggregate by material type and country
    summary = secondary.groupby(['reporter', 'material_type', 'ewc_primary']).agg({
        'value': 'sum',
        'product': 'nunique',
    }).reset_index()

    summary.columns = ['country', 'material_type', 'ewc_code', 'tonnes', 'product_count']

    return summary.sort_values('tonnes', ascending=False)


# ===== EXAMPLE USAGE =====

if __name__ == '__main__':
    print("PRODCOM-Waste Linker Module")
    print("=" * 50)

    # Show available PRODCOM mappings
    print(f"\nMapped PRODCOM codes: {len(PRODCOM_TO_EWC)}")

    # Show codes by NACE
    for nace in ['24.10', '24.42', '23.51', '20.16', '17.11']:
        codes = get_prodcom_codes_for_nace(nace)
        print(f"  NACE {nace}: {len(codes)} codes")

    # Example: Map a single product
    print("\nExample mapping:")
    result = map_prodcom_to_waste('24101130', 1000000)  # 1M tonnes pig iron
    print(f"  Product: 24101130 (Pig iron)")
    print(f"  Production: 1,000,000 tonnes")
    print(f"  Primary waste: {result['ewc_primary']} ({get_ewc_description(result['ewc_primary'])})")
    print(f"  Waste factor: {result['factor_used']}")
    print(f"  Estimated waste: {result['waste_tonnes']:,.0f} tonnes")
    print(f"  Byproducts: {result['byproducts']}")

    print("\nTo fetch real data, use:")
    print("  df = get_prodcom_for_waste_analysis(['24.10', '24.42'], countries=['SE', 'DE'])")
