"""
E-PRTR emissions loader for all release media (Air, Water, Transfers).

Loads actual reported emissions from E-PRTR raw files and combines them
into a unified format for technology identification via tensor decomposition.

Data sources:
- F1_4_Air_Releases_Facilities.csv - Air emissions
- F2_4_Water_Releases_Facilities.csv - Water releases
- F3_2_Transfers_Facilities.csv - Waste transfers
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple


def load_air_releases(raw_dir: Path) -> pd.DataFrame:
    """Load air pollutant releases from E-PRTR."""
    path = raw_dir / 'F1_4_Air_Releases_Facilities.csv'
    if not path.exists():
        raise FileNotFoundError(f"Air releases file not found: {path}")

    df = pd.read_csv(path)

    # Standardize columns
    df = df.rename(columns={
        'FacilityInspireId': 'facility_id',
        'facilityName': 'facility_name',
        'countryName': 'country',
        'reportingYear': 'reporting_year',
        'EPRTRAnnexIMainActivity': 'eprtr_activity',
        'Pollutant': 'pollutant',
        'Releases': 'release_kg',
        'Latitude': 'lat',
        'Longitude': 'lon',
        'city': 'city'
    })

    df['medium'] = 'AIR'

    return df[['facility_id', 'facility_name', 'country', 'city', 'lat', 'lon',
               'eprtr_activity', 'reporting_year', 'pollutant', 'release_kg', 'medium']]


def load_water_releases(raw_dir: Path) -> pd.DataFrame:
    """Load water pollutant releases from E-PRTR."""
    path = raw_dir / 'F2_4_Water_Releases_Facilities.csv'
    if not path.exists():
        raise FileNotFoundError(f"Water releases file not found: {path}")

    df = pd.read_csv(path)

    df = df.rename(columns={
        'FacilityInspireId': 'facility_id',
        'facilityName': 'facility_name',
        'countryName': 'country',
        'reportingYear': 'reporting_year',
        'EPRTRAnnexIMainActivity': 'eprtr_activity',
        'Pollutant': 'pollutant',
        'Releases': 'release_kg',
        'Latitude': 'lat',
        'Longitude': 'lon',
        'city': 'city'
    })

    df['medium'] = 'WATER'

    return df[['facility_id', 'facility_name', 'country', 'city', 'lat', 'lon',
               'eprtr_activity', 'reporting_year', 'pollutant', 'release_kg', 'medium']]


def load_transfers(raw_dir: Path) -> pd.DataFrame:
    """Load off-site waste transfers from E-PRTR."""
    path = raw_dir / 'F3_2_Transfers_Facilities.csv'
    if not path.exists():
        raise FileNotFoundError(f"Transfers file not found: {path}")

    df = pd.read_csv(path)

    df = df.rename(columns={
        'FacilityInspireId': 'facility_id',
        'facilityName': 'facility_name',
        'countryName': 'country',
        'reportingYear': 'reporting_year',
        'EPRTRAnnexIMainActivity': 'eprtr_activity',
        'Pollutant': 'pollutant',
        'transfers': 'release_kg',
        'Latitude': 'lat',
        'Longitude': 'lon',
        'city': 'city'
    })

    df['medium'] = 'TRANSFER'

    return df[['facility_id', 'facility_name', 'country', 'city', 'lat', 'lon',
               'eprtr_activity', 'reporting_year', 'pollutant', 'release_kg', 'medium']]


def load_all_emissions(
    raw_dir: Path,
    countries: Optional[List[str]] = None,
    years: Optional[List[int]] = None
) -> pd.DataFrame:
    """
    Load all emission sources (Air, Water, Transfers) into unified dataframe.

    Parameters
    ----------
    raw_dir : Path
        Path to data/raw directory containing E-PRTR files
    countries : list, optional
        Filter to specific countries (full names, e.g. 'Sweden')
    years : list, optional
        Filter to specific reporting years

    Returns
    -------
    pd.DataFrame
        Unified emissions with columns:
        facility_id, facility_name, country, city, lat, lon,
        eprtr_activity, reporting_year, pollutant, release_kg, medium,
        co2_excludes_biomass (bool: True if originally "CO2 excluding biomass")
    """
    raw_dir = Path(raw_dir)

    dfs = []

    # Load each source
    try:
        air_df = load_air_releases(raw_dir)
        dfs.append(air_df)
        print(f"Loaded {len(air_df):,} air release records")
    except FileNotFoundError as e:
        print(f"Warning: {e}")

    try:
        water_df = load_water_releases(raw_dir)
        dfs.append(water_df)
        print(f"Loaded {len(water_df):,} water release records")
    except FileNotFoundError as e:
        print(f"Warning: {e}")

    try:
        transfer_df = load_transfers(raw_dir)
        dfs.append(transfer_df)
        print(f"Loaded {len(transfer_df):,} transfer records")
    except FileNotFoundError as e:
        print(f"Warning: {e}")

    if not dfs:
        raise FileNotFoundError("No E-PRTR emission files found")

    # Combine all sources
    combined = pd.concat(dfs, ignore_index=True)

    # Filter by country if specified
    if countries:
        combined = combined[combined['country'].isin(countries)]

    # Filter by year if specified
    if years:
        combined = combined[combined['reporting_year'].isin(years)]

    print(f"Total: {len(combined):,} emission records from {combined['facility_id'].nunique():,} facilities")

    return combined


def get_ied_from_eprtr_activity(eprtr_activity: str) -> str:
    """Convert EPRTR activity code to IED activity code.

    Uses lookup table derived from F6_1_IED_Installations.csv.
    """
    from src.mappings.eprtr_ied import eprtr_to_ied
    return eprtr_to_ied(eprtr_activity)


def build_facility_pollutant_matrix(
    emissions_df: pd.DataFrame,
    ied_filter: Optional[str] = None,
    aggregate_years: bool = True
) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """
    Build facility × pollutant × medium matrix for tensor decomposition.

    Parameters
    ----------
    emissions_df : pd.DataFrame
        Combined emissions from load_all_emissions()
    ied_filter : str, optional
        Filter to specific IED activity prefix (e.g., '2' for metals, '6' for paper)
    aggregate_years : bool
        If True, sum across all years. If False, keep separate.

    Returns
    -------
    pivot_df : pd.DataFrame
        Pivoted data with facilities as rows, (pollutant, medium) as columns
    facility_ids : list
        Ordered list of facility IDs
    column_names : list
        Ordered list of (pollutant, medium) column names
    """
    df = emissions_df.copy()

    # Add IED code
    df['ied_code'] = df['eprtr_activity'].apply(get_ied_from_eprtr_activity)

    # Filter by IED if specified
    if ied_filter:
        df = df[df['ied_code'].str.startswith(ied_filter, na=False)]

    # Aggregate by facility, pollutant, medium
    if aggregate_years:
        agg_df = df.groupby(
            ['facility_id', 'pollutant', 'medium']
        )['release_kg'].sum().reset_index()
    else:
        agg_df = df.groupby(
            ['facility_id', 'pollutant', 'medium', 'reporting_year']
        )['release_kg'].sum().reset_index()

    # Create combined column name
    agg_df['pollutant_medium'] = agg_df['pollutant'] + '_' + agg_df['medium']

    # Pivot to facility × pollutant_medium matrix
    pivot_df = agg_df.pivot_table(
        index='facility_id',
        columns='pollutant_medium',
        values='release_kg',
        fill_value=0
    )

    facility_ids = list(pivot_df.index)
    column_names = list(pivot_df.columns)

    return pivot_df, facility_ids, column_names


def build_emission_tensor(
    emissions_df: pd.DataFrame,
    ied_filter: Optional[str] = None
) -> Tuple[np.ndarray, List[str], List[str], List[str]]:
    """
    Build 3D tensor T[facility, pollutant, medium] for tensor decomposition.

    Parameters
    ----------
    emissions_df : pd.DataFrame
        Combined emissions from load_all_emissions()
    ied_filter : str, optional
        Filter to specific IED activity prefix

    Returns
    -------
    tensor : np.ndarray
        3D tensor of shape (n_facilities, n_pollutants, n_media)
    facility_ids : list
        Ordered list of facility IDs (axis 0)
    pollutants : list
        Ordered list of pollutant names (axis 1)
    media : list
        Ordered list of media types (axis 2)
    """
    df = emissions_df.copy()

    # Add IED code
    df['ied_code'] = df['eprtr_activity'].apply(get_ied_from_eprtr_activity)

    # Filter by IED if specified
    if ied_filter:
        df = df[df['ied_code'].str.startswith(ied_filter, na=False)]

    if len(df) == 0:
        raise ValueError(f"No data for IED filter: {ied_filter}")

    # Get ordered unique values for each dimension
    facility_ids = sorted(df['facility_id'].unique())
    pollutants = sorted(df['pollutant'].unique())
    media = sorted(df['medium'].unique())

    # Create index mappings
    fac_idx = {f: i for i, f in enumerate(facility_ids)}
    pol_idx = {p: i for i, p in enumerate(pollutants)}
    med_idx = {m: i for i, m in enumerate(media)}

    # Aggregate by facility, pollutant, medium (sum across years)
    agg_df = df.groupby(
        ['facility_id', 'pollutant', 'medium']
    )['release_kg'].sum().reset_index()

    # Build tensor
    tensor = np.zeros((len(facility_ids), len(pollutants), len(media)))

    for _, row in agg_df.iterrows():
        i = fac_idx[row['facility_id']]
        j = pol_idx[row['pollutant']]
        k = med_idx[row['medium']]
        tensor[i, j, k] = row['release_kg']

    print(f"Built tensor: {tensor.shape} (facilities × pollutants × media)")
    print(f"  Non-zero entries: {np.count_nonzero(tensor):,} / {tensor.size:,} ({100*np.count_nonzero(tensor)/tensor.size:.1f}%)")

    return tensor, facility_ids, pollutants, media


def get_facility_metadata(
    emissions_df: pd.DataFrame,
    ied_filter: Optional[str] = None
) -> pd.DataFrame:
    """
    Get facility metadata (name, country, coordinates, IED code).

    Parameters
    ----------
    emissions_df : pd.DataFrame
        Combined emissions from load_all_emissions()
    ied_filter : str, optional
        Filter to specific IED activity prefix

    Returns
    -------
    pd.DataFrame
        One row per facility with metadata
    """
    df = emissions_df.copy()
    df['ied_code'] = df['eprtr_activity'].apply(get_ied_from_eprtr_activity)

    if ied_filter:
        df = df[df['ied_code'].str.startswith(ied_filter, na=False)]

    # Get unique facility metadata (most recent record)
    metadata = (
        df.sort_values('reporting_year', ascending=False)
        .drop_duplicates(subset=['facility_id'])
        [['facility_id', 'facility_name', 'country', 'city', 'lat', 'lon',
          'eprtr_activity', 'ied_code']]
    )

    return metadata


def get_facility_emissions_for_allocation(
    raw_dir: Path,
    countries: Optional[List[str]] = None,
    n_datapoints: int = 3
) -> pd.DataFrame:
    """
    Get facility emissions aggregated for use with EmissionsAllocator.

    Loads actual E-PRTR emissions and aggregates CO2/NOX/PM10 per facility.
    Returns one row per facility with columns required by EmissionsAllocator.

    Parameters
    ----------
    raw_dir : Path
        Path to data/raw directory containing E-PRTR files
    countries : list, optional
        Filter to specific countries (ISO codes: SE, NO, FI, DK, etc.)
    n_datapoints : int, optional
        Number of most recent reporting years to include. Default: 3

    Returns
    -------
    pd.DataFrame
        One row per facility with columns:
        facility_id, facility_name, country_code, lat, lon, ied_activity,
        CO2, NOX, PM10
    """
    raw_dir = Path(raw_dir)

    # Load all emissions
    emissions = load_all_emissions(raw_dir)

    # Map country names to ISO codes
    country_name_to_iso = {
        'Sweden': 'SE', 'Norway': 'NO', 'Finland': 'FI',
        'Denmark': 'DK', 'Iceland': 'IS', 'Germany': 'DE',
        'France': 'FR', 'Poland': 'PL', 'Netherlands': 'NL',
        'Belgium': 'BE', 'Austria': 'AT', 'Italy': 'IT',
        'Spain': 'ES', 'Portugal': 'PT', 'Greece': 'EL',
        'Ireland': 'IE', 'United Kingdom': 'UK',
        'Czechia': 'CZ', 'Czech Republic': 'CZ',
        'Slovakia': 'SK', 'Hungary': 'HU',
        'Romania': 'RO', 'Bulgaria': 'BG',
        'Slovenia': 'SI', 'Croatia': 'HR',
        'Estonia': 'EE', 'Latvia': 'LV', 'Lithuania': 'LT',
        'Luxembourg': 'LU', 'Malta': 'MT', 'Cyprus': 'CY',
        'Türkiye': 'TR', 'Turkey': 'TR',
    }
    emissions['country_code'] = emissions['country'].map(country_name_to_iso)

    # Filter by country if specified (accepts both ISO codes and full names)
    if countries:
        # Check if input is ISO codes (2 chars) or full names
        iso_to_name = {v: k for k, v in country_name_to_iso.items()}
        country_codes = []
        for c in countries:
            if len(c) == 2 and c.upper() in iso_to_name:
                country_codes.append(c.upper())
            elif c in country_name_to_iso:
                country_codes.append(country_name_to_iso[c])
            else:
                # Try case-insensitive match
                for name, code in country_name_to_iso.items():
                    if name.lower() == c.lower():
                        country_codes.append(code)
                        break
        emissions = emissions[emissions['country_code'].isin(country_codes)]

    # Filter to most recent n reporting years
    available_years = sorted(emissions['reporting_year'].unique(), reverse=True)
    recent_years = available_years[:n_datapoints]
    emissions = emissions[emissions['reporting_year'].isin(recent_years)]
    print(f"Using emissions from years: {sorted(recent_years)}")

    # Normalize pollutant names for aggregation
    # Handle "CO2 excluding biomass" -> "CO2"
    emissions['pollutant_norm'] = emissions['pollutant'].apply(
        lambda x: 'CO2' if 'CO2' in str(x).upper() else x
    )
    # Handle NOx variants
    emissions['pollutant_norm'] = emissions['pollutant_norm'].apply(
        lambda x: 'NOX' if x.upper() in ['NOX', 'NO2', 'NITROGEN OXIDES'] else x
    )
    # Handle PM10 variants
    emissions['pollutant_norm'] = emissions['pollutant_norm'].apply(
        lambda x: 'PM10' if 'PM10' in str(x).upper() or 'PARTICULATE' in str(x).upper() else x
    )

    # Filter to target pollutants
    target_pollutants = ['CO2', 'NOX', 'PM10']
    emissions_filtered = emissions[emissions['pollutant_norm'].isin(target_pollutants)]

    # Aggregate by facility and pollutant (sum across years and media)
    agg = emissions_filtered.groupby(
        ['facility_id', 'pollutant_norm']
    )['release_kg'].sum().reset_index()

    # Pivot to wide format
    pivot = agg.pivot_table(
        index='facility_id',
        columns='pollutant_norm',
        values='release_kg',
        fill_value=0
    ).reset_index()

    # Ensure all pollutant columns exist
    for pol in target_pollutants:
        if pol not in pivot.columns:
            pivot[pol] = 0.0

    # Get facility metadata (most recent record)
    metadata = (
        emissions
        .sort_values('reporting_year', ascending=False)
        .drop_duplicates(subset=['facility_id'])
        [['facility_id', 'facility_name', 'country_code', 'lat', 'lon', 'eprtr_activity']]
        .copy()
    )

    # Add IED activity code
    metadata['ied_activity'] = metadata['eprtr_activity'].apply(get_ied_from_eprtr_activity)

    # Merge metadata with emissions
    result = metadata.merge(pivot, on='facility_id', how='inner')

    # Reorder columns to match expected format
    result = result[[
        'facility_id', 'facility_name', 'country_code', 'lat', 'lon',
        'ied_activity', 'CO2', 'NOX', 'PM10'
    ]]

    print(f"Prepared {len(result)} facilities for allocation")
    return result


if __name__ == '__main__':
    # Test the loader
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent
    raw_dir = project_root / 'data' / 'raw'

    # Load all emissions
    emissions = load_all_emissions(raw_dir)

    print("\nEmissions by medium:")
    print(emissions.groupby('medium').size())

    print("\nTop 10 pollutants:")
    print(emissions['pollutant'].value_counts().head(10))

    # Test tensor building for steel (IED 2)
    print("\n--- Steel sector (IED 2) ---")
    tensor, facilities, pollutants, media = build_emission_tensor(emissions, ied_filter='2')
    print(f"Facilities: {len(facilities)}")
    print(f"Pollutants: {len(pollutants)}")
    print(f"Media: {media}")

    # Test allocation-ready format
    print("\n--- Allocation-ready format (Nordic) ---")
    alloc_df = get_facility_emissions_for_allocation(raw_dir, countries=['SE', 'NO', 'FI', 'DK'])
    print(alloc_df.head())
