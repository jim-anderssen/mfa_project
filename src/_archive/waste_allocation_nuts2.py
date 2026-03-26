"""
allocation.py

Functions for allocating national waste generation to NUTS-2 regions
using SBS employment data as a proxy.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

from src.loaders.nuts2 import load_recycling_potential


# NACE code mapping: waste data aggregates -> SBS detailed codes
NACE_EXPANSION = {
    'C24_C25': ['C24', 'C25'],
    'C10-C12': ['C10', 'C11', 'C12'],
    'C13-C15': ['C13', 'C14', 'C15'],
    'C17_C18': ['C17', 'C18'],
    'C20-C22': ['C20', 'C21', 'C22'],
    'C26-C30': ['C26', 'C27', 'C28', 'C29', 'C30'],
    'C31-C33': ['C31', 'C32', 'C33'],
    'C31_C32': ['C31', 'C32'],
    'D': ['D35'],
    'E': ['E36', 'E37', 'E38', 'E39'],
    'E36_E37_E39': ['E36', 'E37', 'E39'],
    'G-U_X_G4677': ['G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],
}


def get_regional_shares(
    sbs_data: pd.DataFrame,
    country_code: str,
    nace_codes: List[str],
    value_col: str = 'proxy_value'
) -> pd.DataFrame:
    """
    Calculate economic proxy shares by NUTS-2 region for given NACE codes.

    Parameters
    ----------
    sbs_data : pd.DataFrame
        SBS data with proxy values (from load_sbs_proxy or load_sbs_employment)
    country_code : str
        ISO 2-letter country code
    nace_codes : list
        List of NACE codes to aggregate
    value_col : str
        Column to use for calculating shares. Default: 'proxy_value'
        For backward compatibility, also accepts 'employment'

    Returns
    -------
    pd.DataFrame
        Regional proxy values and share by geo code
    """
    # Handle backward compatibility - check which column exists
    if value_col not in sbs_data.columns:
        if 'employment' in sbs_data.columns:
            value_col = 'employment'
        elif 'proxy_value' in sbs_data.columns:
            value_col = 'proxy_value'
        else:
            raise ValueError(f"Neither '{value_col}' nor 'employment'/'proxy_value' found in data")

    regional = sbs_data[
        (sbs_data['country_code'] == country_code) &
        (sbs_data['nace_r2'].isin(nace_codes))
    ].groupby('geo')[value_col].sum().reset_index()

    regional = regional.rename(columns={value_col: 'proxy_value'})

    total = regional['proxy_value'].sum()
    if total > 0:
        regional['share'] = regional['proxy_value'] / total
    else:
        regional['share'] = 0

    return regional


def allocate_waste_to_regions(
    wasgen: pd.DataFrame,
    sbs_nuts2: pd.DataFrame,
    nuts2_names: Dict[str, str],
    nace_expansion: Optional[Dict[str, List[str]]] = None,
    proxy_type: str = 'labour_costs'
) -> pd.DataFrame:
    """
    Allocate national waste generation to NUTS-2 regions based on economic proxy shares.

    Parameters
    ----------
    wasgen : pd.DataFrame
        Filtered waste generation data with columns:
        country_code, nace_r2, waste, waste_description, nace_r2_activity, mean_wasgen
    sbs_nuts2 : pd.DataFrame
        SBS proxy data (from load_sbs_proxy or load_sbs_employment)
    nuts2_names : dict
        Mapping from NUTS-2 code to region name
    nace_expansion : dict, optional
        Mapping from aggregated NACE codes to detailed codes
    proxy_type : str
        Name of proxy type used (for metadata in output).
        Default: 'labour_costs'

    Returns
    -------
    pd.DataFrame
        Allocated waste by region × NACE × waste type with columns:
        nuts2_region, nuts2_name, country_code, nace_r2, nace_activity,
        waste, waste_description, allocated_waste_tonnes, proxy_value,
        allocation_share, proxy_type
    """
    if nace_expansion is None:
        nace_expansion = NACE_EXPANSION

    results = []
    missing_nace = set()

    for _, row in wasgen.iterrows():
        country_code = row['country_code']
        nace_code = row['nace_r2']
        waste_type = row['waste']
        waste_desc = row['waste_description']
        nace_activity = row['nace_r2_activity']
        total_waste = row['mean_wasgen']

        # Expand NACE codes if aggregated
        sbs_nace_list = nace_expansion.get(nace_code, [nace_code])

        # Get regional proxy shares
        regional_shares = get_regional_shares(sbs_nuts2, country_code, sbs_nace_list)

        if len(regional_shares) == 0 or regional_shares['share'].sum() == 0:
            missing_nace.add((country_code, nace_code))
            continue

        # Allocate waste to regions
        for _, reg in regional_shares.iterrows():
            allocated = total_waste * reg['share']
            if allocated > 0:
                nuts2_name = nuts2_names.get(reg['geo'], reg['geo'])
                results.append({
                    'nuts2_region': reg['geo'],
                    'nuts2_name': nuts2_name,
                    'country_code': country_code,
                    'nace_r2': nace_code,
                    'nace_activity': nace_activity,
                    'waste': waste_type,
                    'waste_description': waste_desc,
                    'allocated_waste_tonnes': allocated,
                    'proxy_value': reg['proxy_value'],
                    'allocation_share': reg['share'],
                    'proxy_type': proxy_type
                })

    regional_waste = pd.DataFrame(results)

    if missing_nace:
        print(f"Warning: {len(missing_nace)} NACE mappings not found in SBS data")

    return regional_waste


def add_economic_potential(
    regional_waste: pd.DataFrame,
    waste_value_map: Optional[Dict[str, float]] = None,
    default_value: float = 10.0
) -> pd.DataFrame:
    """
    Add economic potential columns based on recycling potential index.

    Parameters
    ----------
    regional_waste : pd.DataFrame
        Allocated waste data from allocate_waste_to_regions()
    waste_value_map : dict, optional
        Mapping from waste code to EUR/tonne value
    default_value : float
        Default value for unmapped waste types

    Returns
    -------
    pd.DataFrame
        Input data with added columns:
        recycling_potential_eur_t, economic_potential_eur
    """
    if waste_value_map is None:
        waste_value_map = load_recycling_potential()

    df = regional_waste.copy()
    df['recycling_potential_eur_t'] = df['waste'].map(waste_value_map).fillna(default_value)
    df['economic_potential_eur'] = df['allocated_waste_tonnes'] * df['recycling_potential_eur_t']

    return df


def aggregate_by_dimension(
    regional_waste: pd.DataFrame,
    groupby_cols: List[str],
    value_cols: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Aggregate regional waste data by specified dimensions.

    Parameters
    ----------
    regional_waste : pd.DataFrame
        Allocated waste data
    groupby_cols : list
        Columns to group by (e.g., ['nuts2_region', 'waste'])
    value_cols : list, optional
        Columns to sum. Defaults to tonnage and economic potential.

    Returns
    -------
    pd.DataFrame
        Aggregated data sorted by economic potential descending
    """
    if value_cols is None:
        value_cols = ['allocated_waste_tonnes', 'economic_potential_eur']

    agg_dict = {col: 'sum' for col in value_cols if col in regional_waste.columns}

    result = regional_waste.groupby(groupby_cols).agg(agg_dict).reset_index()
    return result.sort_values('economic_potential_eur', ascending=False)


def create_pivot_matrix(
    regional_waste: pd.DataFrame,
    index_col: str,
    columns_col: str,
    values_col: str = 'allocated_waste_tonnes'
) -> pd.DataFrame:
    """
    Create a pivot table matrix from regional waste data.

    Parameters
    ----------
    regional_waste : pd.DataFrame
        Allocated waste data
    index_col : str
        Column for matrix rows (e.g., 'nuts2_region')
    columns_col : str
        Column for matrix columns (e.g., 'waste')
    values_col : str
        Column to aggregate

    Returns
    -------
    pd.DataFrame
        Pivot table with rows × columns
    """
    return regional_waste.pivot_table(
        index=index_col,
        columns=columns_col,
        values=values_col,
        aggfunc='sum'
    ).fillna(0)


def compare_proxy_methods(
    wasgen: pd.DataFrame,
    nuts2_names: Dict[str, str],
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Compare waste allocation results across different proxy methods.

    Parameters
    ----------
    wasgen : pd.DataFrame
        Waste generation data
    nuts2_names : dict
        NUTS-2 region names
    use_cache : bool
        Whether to use cached SBS data

    Returns
    -------
    pd.DataFrame
        Comparison table with allocations by each proxy method,
        indexed by nuts2_region
    """
    from src.loaders.nuts2 import load_sbs_proxy, ProxyType

    results = {}

    for proxy in ProxyType:
        try:
            sbs = load_sbs_proxy(proxy_type=proxy, use_cache=use_cache)
            allocated = allocate_waste_to_regions(
                wasgen, sbs, nuts2_names, proxy_type=proxy.value
            )

            # Aggregate by region for comparison
            regional_totals = (
                allocated.groupby('nuts2_region')['allocated_waste_tonnes']
                .sum()
                .rename(f'tonnes_{proxy.value}')
            )
            results[proxy.value] = regional_totals

        except ValueError as e:
            print(f"Skipping {proxy.value}: {e}")

    # Combine into comparison dataframe
    comparison = pd.DataFrame(results)

    # Calculate correlation between methods
    if len(comparison.columns) > 1:
        print("\nCorrelation between proxy methods:")
        print(comparison.corr().round(3))

    return comparison


def validate_proxy_coverage(
    sbs_data: pd.DataFrame,
    wasgen: pd.DataFrame,
    nace_expansion: Optional[Dict[str, List[str]]] = None
) -> pd.DataFrame:
    """
    Check SBS data coverage for waste generation NACE codes.

    Identifies gaps where national waste data exists but regional
    proxy data is missing.

    Parameters
    ----------
    sbs_data : pd.DataFrame
        SBS proxy data
    wasgen : pd.DataFrame
        Waste generation data
    nace_expansion : dict, optional
        NACE code mappings

    Returns
    -------
    pd.DataFrame
        Coverage report by country and NACE code
    """
    if nace_expansion is None:
        nace_expansion = NACE_EXPANSION

    coverage_report = []

    # Determine value column
    value_col = 'proxy_value' if 'proxy_value' in sbs_data.columns else 'employment'

    for country in wasgen['country_code'].unique():
        country_nace = wasgen[wasgen['country_code'] == country]['nace_r2'].unique()

        for nace in country_nace:
            expanded = nace_expansion.get(nace, [nace])

            # Check if any of the expanded codes exist in SBS
            sbs_match = sbs_data[
                (sbs_data['country_code'] == country) &
                (sbs_data['nace_r2'].isin(expanded)) &
                (sbs_data[value_col] > 0)
            ]

            coverage_report.append({
                'country_code': country,
                'nace_r2': nace,
                'expanded_codes': ', '.join(expanded),
                'sbs_regions_found': sbs_match['geo'].nunique(),
                'sbs_total_proxy': sbs_match[value_col].sum(),
                'has_coverage': len(sbs_match) > 0
            })

    return pd.DataFrame(coverage_report)
