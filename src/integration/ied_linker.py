"""
Utility to link IED installations to PRODCOM production data.

This module provides functions to:
1. Load and parse IED installation data
2. Map IED activities to NACE/PRODCOM codes
3. Allocate national PRODCOM production to facility locations
4. Aggregate by NUTS regions
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Import mapping - handle both package and direct execution
try:
    from src.mappings.ied_nace import (
        IED_TO_NACE,
        get_nace_for_ied,
        get_ied_description,
        is_prodcom_relevant,
        get_prodcom_byproduct_info,
    )
except ModuleNotFoundError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / 'mappings'))
    from ied_nace import (
        IED_TO_NACE,
        get_nace_for_ied,
        get_ied_description,
        is_prodcom_relevant,
        get_prodcom_byproduct_info,
    )


def load_ied_installations(filepath: str) -> pd.DataFrame:
    """
    Load IED installations from CSV file.

    Parameters
    ----------
    filepath : str
        Path to IED installations CSV file

    Returns
    -------
    pd.DataFrame
        Cleaned IED installations dataframe
    """
    df = pd.read_csv(filepath, encoding='utf-8-sig')

    # Standardize column names
    df.columns = df.columns.str.strip()

    # Parse IED activity code (handle formats like "2.5(a)", "6.6(b)")
    df['ied_code'] = df['IEDAnnexIMainActivity'].astype(str).str.strip()

    # Extract base IED code (e.g., "2.5" from "2.5(a)")
    df['ied_code_base'] = df['ied_code'].str.extract(r'^(\d+\.?\d*)')[0]

    # Add NACE codes
    df['nace_codes'] = df['ied_code'].apply(get_nace_for_ied)
    df['nace_primary'] = df['nace_codes'].apply(lambda x: x[0] if x else None)

    # Flag if PRODCOM relevant
    df['prodcom_relevant'] = df['ied_code'].apply(is_prodcom_relevant)

    # Ensure coordinates are numeric
    df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
    df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')

    return df


def assign_nuts_region(
    df: pd.DataFrame,
    nuts_gdf: Optional['gpd.GeoDataFrame'] = None,
    nuts_level: int = 2
) -> pd.DataFrame:
    """
    Assign NUTS region codes to installations based on coordinates.

    Parameters
    ----------
    df : pd.DataFrame
        IED installations with Longitude/Latitude columns
    nuts_gdf : GeoDataFrame, optional
        NUTS boundaries. If None, attempts to load from standard location.
    nuts_level : int
        NUTS level (0, 1, 2, or 3)

    Returns
    -------
    pd.DataFrame
        DataFrame with NUTS region column added
    """
    try:
        import geopandas as gpd
        from shapely.geometry import Point
    except ImportError:
        print("geopandas required for spatial assignment. Install with: pip install geopandas")
        return df

    # Create geometry from coordinates
    valid_coords = df['Longitude'].notna() & df['Latitude'].notna()

    geometry = [
        Point(lon, lat) if valid else None
        for lon, lat, valid in zip(df['Longitude'], df['Latitude'], valid_coords)
    ]

    gdf = gpd.GeoDataFrame(df.copy(), geometry=geometry, crs='EPSG:4326')

    if nuts_gdf is None:
        # Try to load NUTS boundaries
        try:
            import eurostat
            nuts_gdf = eurostat.get_eurostat_geospatial(
                resolution='10m',
                nuts_level=nuts_level,
                year=2021
            )
        except Exception as e:
            print(f"Could not load NUTS boundaries: {e}")
            return df

    # Spatial join
    gdf = gpd.sjoin(gdf, nuts_gdf[['NUTS_ID', 'geometry']], how='left', predicate='within')

    df[f'nuts{nuts_level}'] = gdf['NUTS_ID'].values

    return df


def count_facilities_by_nace_country(df: pd.DataFrame) -> pd.DataFrame:
    """
    Count IED facilities by NACE code and country.

    Parameters
    ----------
    df : pd.DataFrame
        IED installations dataframe

    Returns
    -------
    pd.DataFrame
        Facility counts by NACE code and country
    """
    # Filter to PRODCOM-relevant facilities
    relevant = df[df['prodcom_relevant']].copy()

    # Explode NACE codes (one facility can map to multiple NACE)
    exploded = relevant.explode('nace_codes')
    exploded = exploded[exploded['nace_codes'].notna()]

    # Count by country and NACE
    counts = exploded.groupby(['CountryName', 'nace_codes']).agg({
        'InstallationInspireId': 'count',
        'installationName': lambda x: list(x)[:5],  # Sample names
    }).reset_index()

    counts.columns = ['country', 'nace_code', 'facility_count', 'sample_facilities']

    return counts


def count_facilities_by_nace_nuts(df: pd.DataFrame, nuts_col: str = 'nuts2') -> pd.DataFrame:
    """
    Count IED facilities by NACE code and NUTS region.

    Parameters
    ----------
    df : pd.DataFrame
        IED installations dataframe with NUTS column
    nuts_col : str
        Name of NUTS region column

    Returns
    -------
    pd.DataFrame
        Facility counts by NACE code and NUTS region
    """
    if nuts_col not in df.columns:
        raise ValueError(f"Column {nuts_col} not found. Run assign_nuts_region first.")

    # Filter to PRODCOM-relevant facilities
    relevant = df[df['prodcom_relevant']].copy()

    # Explode NACE codes
    exploded = relevant.explode('nace_codes')
    exploded = exploded[exploded['nace_codes'].notna()]

    # Count by NUTS region and NACE
    counts = exploded.groupby([nuts_col, 'nace_codes']).agg({
        'InstallationInspireId': 'count',
        'Longitude': 'mean',
        'Latitude': 'mean',
    }).reset_index()

    counts.columns = [nuts_col, 'nace_code', 'facility_count', 'centroid_lon', 'centroid_lat']

    return counts


def allocate_prodcom_to_facilities(
    prodcom_df: pd.DataFrame,
    facility_counts: pd.DataFrame,
    value_col: str = 'value',
    nace_col: str = 'nace_code',
    region_col: str = 'country'
) -> pd.DataFrame:
    """
    Allocate PRODCOM production values to regions based on facility counts.

    Parameters
    ----------
    prodcom_df : pd.DataFrame
        PRODCOM production data with NACE codes and values
    facility_counts : pd.DataFrame
        Facility counts by region and NACE from count_facilities_by_nace_*
    value_col : str
        Column containing production values
    nace_col : str
        Column containing NACE codes
    region_col : str
        Column containing region identifiers

    Returns
    -------
    pd.DataFrame
        Production values allocated to regions
    """
    # Merge facility counts with PRODCOM data
    # First, get NACE 4-digit code from PRODCOM (first 4 chars)
    prodcom_df = prodcom_df.copy()
    prodcom_df['nace_4digit'] = prodcom_df[nace_col].str[:5]  # e.g., "24.10"

    # Calculate share of facilities per region within country
    total_by_nace_country = facility_counts.groupby(['country', nace_col])['facility_count'].transform('sum')
    facility_counts = facility_counts.copy()
    facility_counts['facility_share'] = facility_counts['facility_count'] / total_by_nace_country

    # Merge
    merged = prodcom_df.merge(
        facility_counts,
        left_on=['country', 'nace_4digit'],
        right_on=['country', nace_col],
        how='left'
    )

    # Allocate value
    merged['allocated_value'] = merged[value_col] * merged['facility_share']

    return merged


def create_linkage_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create summary of IED-NACE-PRODCOM linkages.

    Parameters
    ----------
    df : pd.DataFrame
        IED installations dataframe

    Returns
    -------
    pd.DataFrame
        Summary table of linkages
    """
    summary_rows = []

    for ied_code, mapping in IED_TO_NACE.items():
        nace_codes = mapping.get('nace', [])

        # Count facilities with this IED code
        count = len(df[df['ied_code'] == ied_code])

        summary_rows.append({
            'ied_code': ied_code,
            'ied_description': mapping.get('description', ''),
            'bat_ref': mapping.get('bat_ref', ''),
            'nace_codes': ', '.join(nace_codes),
            'prodcom_relevant': mapping.get('prodcom_relevant', False),
            'facility_count': count,
        })

    return pd.DataFrame(summary_rows)


# Example usage
if __name__ == '__main__':
    # Load sample data
    data_dir = Path(__file__).parent.parent.parent / 'data'
    ied_file = data_dir / 'raw' / 'F6_1_IED_Installations.csv'

    if ied_file.exists():
        print("Loading IED installations...")
        df = load_ied_installations(str(ied_file))

        print(f"\nLoaded {len(df)} installations")
        print(f"PRODCOM-relevant: {df['prodcom_relevant'].sum()}")

        print("\nFacility counts by country and NACE:")
        counts = count_facilities_by_nace_country(df)
        print(counts.head(20))

        print("\nLinkage summary:")
        summary = create_linkage_summary(df)
        print(summary[summary['facility_count'] > 0].to_string())
    else:
        print(f"IED file not found: {ied_file}")
