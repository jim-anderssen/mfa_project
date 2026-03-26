"""
allocation.py

Functions for allocating national waste generation to NUTS-2 regions
using SBS employment data as a proxy.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

from .data_loader import load_recycling_potential


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
    nace_codes: List[str]
) -> pd.DataFrame:
    """
    Calculate employment shares by NUTS-2 region for given NACE codes.

    Parameters
    ----------
    sbs_data : pd.DataFrame
        SBS employment data filtered to NUTS-2 regions
    country_code : str
        ISO 2-letter country code
    nace_codes : list
        List of NACE codes to aggregate

    Returns
    -------
    pd.DataFrame
        Regional employment and share by geo code
    """
    regional = sbs_data[
        (sbs_data['country_code'] == country_code) &
        (sbs_data['nace_r2'].isin(nace_codes))
    ].groupby('geo')['employment'].sum().reset_index()

    total = regional['employment'].sum()
    if total > 0:
        regional['share'] = regional['employment'] / total
    else:
        regional['share'] = 0

    return regional


def allocate_waste_to_regions(
    wasgen: pd.DataFrame,
    sbs_nuts2: pd.DataFrame,
    nuts2_names: Dict[str, str],
    nace_expansion: Optional[Dict[str, List[str]]] = None
) -> pd.DataFrame:
    """
    Allocate national waste generation to NUTS-2 regions based on employment shares.

    Parameters
    ----------
    wasgen : pd.DataFrame
        Filtered waste generation data with columns:
        country_code, nace_r2, waste, waste_description, nace_r2_activity, mean_wasgen
    sbs_nuts2 : pd.DataFrame
        SBS employment data filtered to NUTS-2 regions
    nuts2_names : dict
        Mapping from NUTS-2 code to region name
    nace_expansion : dict, optional
        Mapping from aggregated NACE codes to detailed codes

    Returns
    -------
    pd.DataFrame
        Allocated waste by region × NACE × waste type
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

        # Get regional employment shares
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
                    'employment': reg['employment'],
                    'allocation_share': reg['share']
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
