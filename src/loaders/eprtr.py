"""
E-PRTR (European Pollutant Release and Transfer Register) data loader.

DEPRECATED: Use src/loaders/eprtr_emissions.py instead.
- For allocation: use get_facility_emissions_for_allocation()
- For tensor analysis: use load_all_emissions(), build_emission_tensor()

This module uses synthetic emissions from sector averages as fallback.
The eprtr_emissions module loads actual reported E-PRTR emissions.

Downloads and processes pollutant release data from EEA for use in
facility-level waste allocation based on emissions as allocation proxy.

Data source: EEA Industrial Emissions Portal
https://industry.eea.europa.eu/
"""

import pandas as pd
import requests
import zipfile
import io
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import warnings


# Base URLs for EEA data
EEA_EPRTR_API = "https://industry.eea.europa.eu/api"
EEA_EPRTR_DOWNLOAD = "https://industry.eea.europa.eu/download"

# Pollutants of interest for waste allocation proxy
TARGET_POLLUTANTS = {
    'CO2': {'code': 'CO2', 'name': 'Carbon dioxide', 'unit': 'kg'},
    'NOX': {'code': 'NOX', 'name': 'Nitrogen oxides', 'unit': 'kg'},
    'PM10': {'code': 'PM10', 'name': 'Particulate matter <10um', 'unit': 'kg'},
    'SO2': {'code': 'SO2', 'name': 'Sulphur dioxide', 'unit': 'kg'},  # Optional
}

# Nordic countries scope
NORDIC_COUNTRIES = ['SE', 'NO', 'FI', 'DK', 'IS']


def download_eprtr_data(
    output_dir: Path,
    use_cache: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Download E-PRTR facility and pollutant release data.

    If EEA API fails, falls back to loading from local IED files
    and using facility energy/capacity as emissions proxy.

    Parameters
    ----------
    output_dir : Path
        Directory to save downloaded data
    use_cache : bool
        If True, use cached files if they exist

    Returns
    -------
    facilities_df : pd.DataFrame
        Facility registry with columns:
        facility_id, facility_name, country, city, lat, lon,
        ied_activity, eprtr_activity
    releases_df : pd.DataFrame
        Pollutant releases with columns:
        facility_id, reporting_year, pollutant, release_kg, medium
    """
    output_dir = Path(output_dir)
    facilities_path = output_dir / 'eprtr_facilities.csv'
    releases_path = output_dir / 'eprtr_pollutant_releases.csv'

    # Check cache
    if use_cache and facilities_path.exists() and releases_path.exists():
        print(f"Loading cached E-PRTR data from {output_dir}")
        facilities_df = pd.read_csv(facilities_path)
        releases_df = pd.read_csv(releases_path)
        return facilities_df, releases_df

    # Try EEA API first
    try:
        facilities_df, releases_df = _fetch_from_eea_api()
    except Exception as e:
        warnings.warn(f"EEA API fetch failed: {e}. Using fallback method.")
        facilities_df, releases_df = _load_from_local_ied(output_dir)

    # Save to cache
    facilities_df.to_csv(facilities_path, index=False)
    releases_df.to_csv(releases_path, index=False)

    print(f"Saved E-PRTR data: {len(facilities_df)} facilities, {len(releases_df)} release records")
    return facilities_df, releases_df


def _fetch_from_eea_api() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetch data from EEA Industrial Emissions Portal API.
    """
    # The EEA API endpoints for pollutant releases
    # This requires exploring their SPARQL or REST endpoints

    # Try the reporting data endpoint
    api_url = f"{EEA_EPRTR_API}/reports/pollutant-releases"

    # For now, raise NotImplementedError to trigger fallback
    raise NotImplementedError(
        "EEA API access requires authentication or specific endpoints. "
        "Use local IED data fallback."
    )


def _get_project_root() -> Path:
    """Find project root by looking for pyproject.toml or data/ directory."""
    current = Path(__file__).resolve().parent
    for _ in range(5):
        if (current / 'pyproject.toml').exists() or (current / 'data').is_dir():
            return current
        current = current.parent
    return Path.cwd()


def _load_from_local_ied(data_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load facility data from local IED installations file and generate
    estimated emissions based on sector averages.

    This is a fallback when EEA API is not accessible.
    """
    # Load IED installations
    # Try common locations for the file
    ied_path = data_dir / 'F6_1_IED_Installations.csv'
    if not ied_path.exists():
        ied_path = data_dir.parent / 'raw' / 'F6_1_IED_Installations.csv'

    # Also try project root
    if not ied_path.exists():
        project_root = _get_project_root()
        ied_path = project_root / 'data' / 'raw' / 'F6_1_IED_Installations.csv'

    if not ied_path.exists():
        raise FileNotFoundError(
            f"IED installations file not found. Tried:\n"
            f"  - {data_dir / 'F6_1_IED_Installations.csv'}\n"
            f"  - {data_dir.parent / 'raw' / 'F6_1_IED_Installations.csv'}\n"
            "Please download from EEA Industrial Emissions Portal."
        )

    ied_df = pd.read_csv(ied_path)

    # Extract relevant columns
    facilities_df = ied_df[[
        'InstallationInspireId',
        'installationName',
        'CountryName',
        'City_of_Facility',
        'Latitude',
        'Longitude',
        'IEDAnnexIMainActivity',
        'EPRTRAnnexIMainActivity',
        'reportingYear',
        'BATConclusion'
    ]].copy()

    # Rename columns
    facilities_df.columns = [
        'facility_id', 'facility_name', 'country', 'city',
        'lat', 'lon', 'ied_activity', 'eprtr_activity',
        'reporting_year', 'bat_conclusion'
    ]

    # Get most recent record per facility
    facilities_df = (
        facilities_df
        .sort_values('reporting_year', ascending=False)
        .drop_duplicates(subset=['facility_id'])
    )

    # Map country names to ISO codes
    country_map = {
        'Sweden': 'SE', 'Norway': 'NO', 'Finland': 'FI',
        'Denmark': 'DK', 'Iceland': 'IS', 'Germany': 'DE',
        'France': 'FR', 'Poland': 'PL', 'Netherlands': 'NL',
        'Belgium': 'BE', 'Austria': 'AT', 'Italy': 'IT',
        'Spain': 'ES', 'Portugal': 'PT', 'Greece': 'EL',
        'Ireland': 'IE', 'United Kingdom': 'UK',
        'Czech Republic': 'CZ', 'Czechia': 'CZ',
        'Slovakia': 'SK', 'Hungary': 'HU',
        'Romania': 'RO', 'Bulgaria': 'BG',
        'Slovenia': 'SI', 'Croatia': 'HR',
        'Estonia': 'EE', 'Latvia': 'LV', 'Lithuania': 'LT',
        'Luxembourg': 'LU', 'Malta': 'MT', 'Cyprus': 'CY'
    }
    facilities_df['country_code'] = facilities_df['country'].map(country_map)

    # Generate synthetic emissions data based on sector emission factors
    releases_df = _generate_emissions_from_sectors(facilities_df)

    return facilities_df, releases_df


def _generate_emissions_from_sectors(facilities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate synthetic emissions data based on IED activity sector averages.

    Uses typical emission intensities by sector from EU reference documents.
    These are order-of-magnitude estimates for allocation purposes.
    """
    # Sector-specific emission factors (kg per year, typical large facility)
    # Based on EU-ETS and BAT reference documents
    SECTOR_EMISSIONS = {
        # Energy industries
        '1.1': {'CO2': 500_000_000, 'NOX': 1_000_000, 'PM10': 50_000},
        '1.2': {'CO2': 200_000_000, 'NOX': 500_000, 'PM10': 30_000},
        '1.3': {'CO2': 100_000_000, 'NOX': 200_000, 'PM10': 40_000},
        '1.4': {'CO2': 150_000_000, 'NOX': 300_000, 'PM10': 35_000},

        # Metals
        '2.1': {'CO2': 300_000_000, 'NOX': 600_000, 'PM10': 200_000},
        '2.2': {'CO2': 500_000_000, 'NOX': 800_000, 'PM10': 300_000},
        '2.3': {'CO2': 100_000_000, 'NOX': 200_000, 'PM10': 100_000},
        '2.4': {'CO2': 50_000_000, 'NOX': 100_000, 'PM10': 80_000},
        '2.5(a)': {'CO2': 200_000_000, 'NOX': 400_000, 'PM10': 150_000},
        '2.5(b)': {'CO2': 80_000_000, 'NOX': 150_000, 'PM10': 100_000},
        '2.6': {'CO2': 10_000_000, 'NOX': 20_000, 'PM10': 10_000},

        # Minerals
        '3.1(a)': {'CO2': 400_000_000, 'NOX': 500_000, 'PM10': 400_000},
        '3.1(b)': {'CO2': 100_000_000, 'NOX': 150_000, 'PM10': 200_000},
        '3.1(c)': {'CO2': 50_000_000, 'NOX': 80_000, 'PM10': 100_000},
        '3.3': {'CO2': 80_000_000, 'NOX': 200_000, 'PM10': 50_000},
        '3.4': {'CO2': 60_000_000, 'NOX': 150_000, 'PM10': 40_000},
        '3.5': {'CO2': 30_000_000, 'NOX': 80_000, 'PM10': 60_000},

        # Chemicals
        '4.1(a)': {'CO2': 150_000_000, 'NOX': 300_000, 'PM10': 30_000},
        '4.1(b)': {'CO2': 80_000_000, 'NOX': 150_000, 'PM10': 20_000},
        '4.2(a)': {'CO2': 100_000_000, 'NOX': 200_000, 'PM10': 40_000},
        '4.2(b)': {'CO2': 120_000_000, 'NOX': 250_000, 'PM10': 50_000},
        '4.3': {'CO2': 20_000_000, 'NOX': 40_000, 'PM10': 10_000},
        '4.4': {'CO2': 30_000_000, 'NOX': 50_000, 'PM10': 15_000},
        '4.5': {'CO2': 25_000_000, 'NOX': 60_000, 'PM10': 20_000},

        # Waste management
        '5.1': {'CO2': 50_000_000, 'NOX': 100_000, 'PM10': 50_000},
        '5.2': {'CO2': 100_000_000, 'NOX': 300_000, 'PM10': 20_000},
        '5.3(a)': {'CO2': 20_000_000, 'NOX': 30_000, 'PM10': 30_000},
        '5.3(b)': {'CO2': 15_000_000, 'NOX': 25_000, 'PM10': 25_000},
        '5.4': {'CO2': 30_000_000, 'NOX': 10_000, 'PM10': 10_000},

        # Other activities
        '6.1(a)': {'CO2': 100_000_000, 'NOX': 200_000, 'PM10': 30_000},
        '6.1(b)': {'CO2': 80_000_000, 'NOX': 150_000, 'PM10': 25_000},
        '6.2': {'CO2': 40_000_000, 'NOX': 80_000, 'PM10': 20_000},
        '6.3': {'CO2': 20_000_000, 'NOX': 40_000, 'PM10': 15_000},
        '6.4(a)': {'CO2': 30_000_000, 'NOX': 50_000, 'PM10': 20_000},
        '6.4(b)(i)': {'CO2': 25_000_000, 'NOX': 45_000, 'PM10': 18_000},
        '6.4(b)(ii)': {'CO2': 35_000_000, 'NOX': 55_000, 'PM10': 22_000},
        '6.4(c)': {'CO2': 20_000_000, 'NOX': 35_000, 'PM10': 15_000},
        '6.5': {'CO2': 15_000_000, 'NOX': 25_000, 'PM10': 12_000},
        '6.6(a)': {'CO2': 5_000_000, 'NOX': 30_000, 'PM10': 50_000},
        '6.6(b)': {'CO2': 3_000_000, 'NOX': 20_000, 'PM10': 40_000},
        '6.6(c)': {'CO2': 2_500_000, 'NOX': 18_000, 'PM10': 35_000},
        '6.7': {'CO2': 10_000_000, 'NOX': 15_000, 'PM10': 8_000},
        '6.8': {'CO2': 50_000_000, 'NOX': 100_000, 'PM10': 50_000},
    }

    # Default emissions for unknown sectors
    DEFAULT_EMISSIONS = {'CO2': 50_000_000, 'NOX': 100_000, 'PM10': 50_000}

    releases = []
    for _, fac in facilities_df.iterrows():
        ied_activity = fac['ied_activity']

        # Get sector emissions (with some variation)
        sector_em = SECTOR_EMISSIONS.get(ied_activity, DEFAULT_EMISSIONS)

        # Add some random variation (±50%) for realism
        import random
        random.seed(hash(fac['facility_id']))  # Reproducible per facility

        for pollutant, base_kg in sector_em.items():
            variation = random.uniform(0.5, 1.5)
            release_kg = base_kg * variation

            releases.append({
                'facility_id': fac['facility_id'],
                'reporting_year': fac.get('reporting_year', 2022),
                'pollutant': pollutant,
                'release_kg': release_kg,
                'medium': 'AIR'
            })

    return pd.DataFrame(releases)


def load_eprtr_facilities(
    data_dir: Path,
    countries: Optional[List[str]] = None,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Load E-PRTR facility registry.

    Parameters
    ----------
    data_dir : Path
        Data directory path
    countries : list, optional
        List of ISO country codes to filter. Default: Nordic countries.
    use_cache : bool
        Whether to use cached data

    Returns
    -------
    pd.DataFrame
        Facility registry
    """
    facilities_df, _ = download_eprtr_data(data_dir, use_cache=use_cache)

    if countries is None:
        countries = NORDIC_COUNTRIES

    # Filter by country
    return facilities_df[facilities_df['country_code'].isin(countries)].copy()


def load_eprtr_releases(
    data_dir: Path,
    countries: Optional[List[str]] = None,
    pollutants: Optional[List[str]] = None,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Load E-PRTR pollutant release data.

    Parameters
    ----------
    data_dir : Path
        Data directory path
    countries : list, optional
        List of ISO country codes to filter
    pollutants : list, optional
        List of pollutant codes to filter. Default: CO2, NOX, PM10.
    use_cache : bool
        Whether to use cached data

    Returns
    -------
    pd.DataFrame
        Pollutant releases
    """
    facilities_df, releases_df = download_eprtr_data(data_dir, use_cache=use_cache)

    if countries is None:
        countries = NORDIC_COUNTRIES
    if pollutants is None:
        pollutants = list(TARGET_POLLUTANTS.keys())

    # Get facilities in target countries
    country_facilities = facilities_df[
        facilities_df['country_code'].isin(countries)
    ]['facility_id'].unique()

    # Filter releases
    filtered = releases_df[
        (releases_df['facility_id'].isin(country_facilities)) &
        (releases_df['pollutant'].isin(pollutants))
    ].copy()

    return filtered


def get_facility_emissions_summary(
    data_dir: Path,
    countries: Optional[List[str]] = None,
    year: Optional[int] = None,
    n_datapoints: int = 3
) -> pd.DataFrame:
    """
    Get summary of emissions by facility for allocation.

    Returns one row per facility with CO2, NOx, PM10 columns.

    Parameters
    ----------
    data_dir : Path
        Data directory path
    countries : list, optional
        Country codes to filter
    year : int, optional
        Specific reporting year to filter (overrides n_datapoints)
    n_datapoints : int, optional
        Number of most recent reporting years to include.
        Default: 3 (consistent with Eurostat loader)

    Returns
    -------
    pd.DataFrame
        Facility-level emission totals for CO2, NOX, PM10
        Includes 'emissions_years_used' column showing which years were included
    """
    facilities = load_eprtr_facilities(data_dir, countries)
    releases = load_eprtr_releases(data_dir, countries)

    if year:
        # Specific year requested - use it directly
        releases = releases[releases['reporting_year'] == year]
        years_used = [year]
    else:
        # Filter to most recent n reporting years
        available_years = sorted(releases['reporting_year'].unique(), reverse=True)
        recent_years = available_years[:n_datapoints]
        releases = releases[releases['reporting_year'].isin(recent_years)]
        years_used = sorted(recent_years)

    # Pivot to get pollutants as columns
    emissions = releases.pivot_table(
        index='facility_id',
        columns='pollutant',
        values='release_kg',
        aggfunc='sum'
    ).reset_index()

    # Ensure all pollutant columns exist
    for pol in ['CO2', 'NOX', 'PM10']:
        if pol not in emissions.columns:
            emissions[pol] = 0

    # Merge with facility info
    result = facilities.merge(emissions, on='facility_id', how='left')

    # Fill missing emissions with 0
    result[['CO2', 'NOX', 'PM10']] = result[['CO2', 'NOX', 'PM10']].fillna(0)

    # Store which years were used for transparency
    result['emissions_years_used'] = ', '.join(map(str, years_used))

    return result


if __name__ == '__main__':
    # Test download
    from pathlib import Path
    data_dir = Path('data/raw')

    facilities, releases = download_eprtr_data(data_dir, use_cache=False)
    print(f"\nFacilities: {len(facilities)}")
    print(facilities.head())

    print(f"\nReleases: {len(releases)}")
    print(releases.head())

    # Get summary for Nordic countries
    summary = get_facility_emissions_summary(data_dir)
    print(f"\nNordic facility emissions summary: {len(summary)}")
    print(summary.head())
