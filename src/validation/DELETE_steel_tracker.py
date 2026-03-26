"""
steel_tracker.py

Validate facility allocation pipeline's regime classification (BF/BOF vs EAF)
using GEM Global Iron and Steel Tracker as ground truth.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, List
from pathlib import Path

from ..loaders.io import RAW_DIR, PROCESSED_DIR, save_csv


# European countries to filter from GEM data
EU_COUNTRIES = [
    'Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus', 'Czech Republic',
    'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary',
    'Ireland', 'Italy', 'Latvia', 'Lithuania', 'Luxembourg', 'Malta',
    'Netherlands', 'Norway', 'Poland', 'Portugal', 'Romania', 'Slovakia',
    'Slovenia', 'Spain', 'Sweden', 'Switzerland', 'United Kingdom'
]


def parse_gem_coordinates(coord_str: str) -> Optional[Tuple[float, float]]:
    """
    Parse GEM coordinate string "lat, lon" to tuple.

    Parameters
    ----------
    coord_str : str
        Coordinate string in format "lat, lon" (e.g., "59.347, 18.052")

    Returns
    -------
    tuple or None
        (lat, lon) tuple, or None if parsing fails
    """
    if pd.isna(coord_str) or not isinstance(coord_str, str):
        return None

    try:
        parts = coord_str.split(',')
        if len(parts) != 2:
            return None
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
        # Basic validation
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return (lat, lon)
        return None
    except (ValueError, AttributeError):
        return None


def classify_gem_regime(
    bof_cap: float,
    eaf_cap: float,
    bf_cap: float,
    dri_cap: float
) -> str:
    """
    Classify steel plant as BF_BOF, EAF, MIXED, or UNKNOWN based on capacities.

    Logic:
    - If no steel capacity: UNKNOWN
    - If both BOF and EAF each represent >=30% of total: MIXED
    - If BOF > EAF or BF capacity exists: BF_BOF
    - Otherwise: EAF

    Parameters
    ----------
    bof_cap : float
        BOF (Basic Oxygen Furnace) steel capacity in ttpa
    eaf_cap : float
        EAF (Electric Arc Furnace) steel capacity in ttpa
    bf_cap : float
        BF (Blast Furnace) iron capacity in ttpa
    dri_cap : float
        DRI (Direct Reduced Iron) capacity in ttpa

    Returns
    -------
    str
        One of 'BF_BOF', 'EAF', 'MIXED', 'UNKNOWN'
    """
    # Convert NaN to 0
    bof = 0 if pd.isna(bof_cap) else float(bof_cap)
    eaf = 0 if pd.isna(eaf_cap) else float(eaf_cap)
    bf = 0 if pd.isna(bf_cap) else float(bf_cap)
    dri = 0 if pd.isna(dri_cap) else float(dri_cap)

    total_steel = bof + eaf
    if total_steel == 0:
        # No steel capacity - check iron capacity
        if bf > 0:
            return 'BF_BOF'
        if dri > 0:
            return 'EAF'  # DRI typically feeds EAF
        return 'UNKNOWN'

    bof_share = bof / total_steel
    eaf_share = eaf / total_steel

    # Mixed if both significant
    if bof_share >= 0.3 and eaf_share >= 0.3:
        return 'MIXED'

    # BF_BOF if BOF dominant or has blast furnace
    if bof > eaf or bf > 0:
        return 'BF_BOF'

    return 'EAF'


def load_gem_steel_plants(
    filepath: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load GEM Global Iron and Steel Tracker, filter to European plants.

    Parameters
    ----------
    filepath : Path, optional
        Path to GEM Excel file. Defaults to standard raw data location.

    Returns
    -------
    pd.DataFrame
        European steel plants with columns:
        - plant_id, plant_name, country, status
        - lat, lon (parsed from coordinates)
        - bof_cap, eaf_cap, bf_cap, dri_cap (capacities in ttpa)
        - gem_regime (classified regime)
    """
    if filepath is None:
        filepath = RAW_DIR / "Global iron and steel tracker" / \
            "Plant-level-data-Global-Iron-and-Steel-Tracker-December-2025-V1.xlsx"

    # Load plant data (has coordinates)
    df_data = pd.read_excel(filepath, sheet_name='Plant data')

    # Load capacities and status
    df_cap = pd.read_excel(filepath, sheet_name='Plant capacities and status')

    # Rename columns for easier handling
    df_data = df_data.rename(columns={
        'Plant ID': 'plant_id',
        'Plant name (English)': 'plant_name',
        'Country/Area': 'country',
        'Coordinates': 'coordinates'
    })

    df_cap = df_cap.rename(columns={
        'Plant ID': 'plant_id',
        'Status': 'status',
        'Nominal BOF steel capacity (ttpa)': 'bof_cap',
        'Nominal EAF steel capacity (ttpa)': 'eaf_cap',
        'Nominal BF capacity (ttpa)': 'bf_cap',
        'Nominal DRI capacity (ttpa)': 'dri_cap',
        'Nominal crude steel capacity (ttpa)': 'total_steel_cap'
    })

    # Merge datasets
    df = df_data[['plant_id', 'plant_name', 'country', 'coordinates']].merge(
        df_cap[['plant_id', 'status', 'bof_cap', 'eaf_cap', 'bf_cap', 'dri_cap', 'total_steel_cap']],
        on='plant_id',
        how='inner'
    )

    # Filter to European countries
    df = df[df['country'].isin(EU_COUNTRIES)].copy()

    # Filter to operating plants (exclude retired, cancelled, etc.)
    # Include 'operating pre-retirement' as these are still active (e.g., SSAB transitioning to green steel)
    operating_statuses = ['operating', 'operating pre-retirement', 'mothballed', 'idled']
    df = df[df['status'].str.lower().isin(operating_statuses)].copy()

    # Parse coordinates
    coords = df['coordinates'].apply(parse_gem_coordinates)
    df['lat'] = coords.apply(lambda x: x[0] if x else None)
    df['lon'] = coords.apply(lambda x: x[1] if x else None)

    # Drop rows without valid coordinates
    df = df.dropna(subset=['lat', 'lon'])

    # Classify regime
    df['gem_regime'] = df.apply(
        lambda row: classify_gem_regime(
            row['bof_cap'], row['eaf_cap'], row['bf_cap'], row['dri_cap']
        ),
        axis=1
    )

    # Clean up
    df = df.drop(columns=['coordinates'])
    df = df.reset_index(drop=True)

    print(f"Loaded {len(df)} European steel plants from GEM tracker")
    print(f"  Regime distribution: {df['gem_regime'].value_counts().to_dict()}")

    return df


def load_eprtr_steel_facilities(
    filepath: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load E-PRTR facilities, filter to steel/iron production (IED 2.2).

    Parameters
    ----------
    filepath : Path, optional
        Path to eprtr_facilities.csv. Defaults to standard raw data location.

    Returns
    -------
    pd.DataFrame
        Steel facilities with columns:
        - facility_id, facility_name, country_code, lat, lon, ied_activity
    """
    if filepath is None:
        filepath = RAW_DIR / "eprtr_facilities.csv"

    df = pd.read_csv(filepath)

    # Filter to IED activity 2.2 (ferrous metals production)
    # IED 2.2 covers "Metal processing in ferrous metal foundries"
    # but main steel is 2.2 (integrated steelworks and EAF)
    steel_mask = df['ied_activity'].astype(str).str.startswith('2.2')

    df_steel = df[steel_mask].copy()

    # Keep relevant columns
    df_steel = df_steel[['facility_id', 'facility_name', 'country_code', 'lat', 'lon', 'ied_activity']]
    df_steel = df_steel.dropna(subset=['lat', 'lon'])
    df_steel = df_steel.reset_index(drop=True)

    print(f"Loaded {len(df_steel)} E-PRTR steel facilities (IED 2.2)")

    return df_steel


def load_eprtr_emissions_with_coords(
    filepath: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load E-PRTR air emissions with coordinates for spatial matching.

    Parameters
    ----------
    filepath : Path, optional
        Path to F1_4_Air_Releases_Facilities.csv

    Returns
    -------
    pd.DataFrame
        Emissions data with lat, lon, pollutant, releases (kg/year)
    """
    if filepath is None:
        filepath = RAW_DIR / "F1_4_Air_Releases_Facilities.csv"

    df = pd.read_csv(filepath)

    # Rename columns
    df = df.rename(columns={
        'FacilityInspireId': 'facility_id',
        'Pollutant': 'pollutant',
        'Releases': 'releases',
        'Latitude': 'lat',
        'Longitude': 'lon'
    })

    # Keep relevant columns
    df = df[['facility_id', 'lat', 'lon', 'pollutant', 'releases', 'reportingYear']]

    # Get latest year per facility-pollutant
    df = df.sort_values('reportingYear', ascending=False)
    df = df.drop_duplicates(subset=['facility_id', 'pollutant'], keep='first')

    return df


def haversine_cross_distances(
    coords1: np.ndarray,
    coords2: np.ndarray
) -> np.ndarray:
    """
    Compute haversine distances between two sets of coordinates.

    Parameters
    ----------
    coords1 : np.ndarray
        Array of shape (n1, 2) with [lat, lon] in degrees
    coords2 : np.ndarray
        Array of shape (n2, 2) with [lat, lon] in degrees

    Returns
    -------
    np.ndarray
        Distance matrix of shape (n1, n2) in km
    """
    R = 6371  # Earth radius in km

    # Convert to radians
    coords1_rad = np.radians(coords1)
    coords2_rad = np.radians(coords2)

    lat1 = coords1_rad[:, 0]
    lon1 = coords1_rad[:, 1]
    lat2 = coords2_rad[:, 0]
    lon2 = coords2_rad[:, 1]

    # Compute pairwise differences (broadcasting)
    dlat = lat1[:, np.newaxis] - lat2[np.newaxis, :]
    dlon = lon1[:, np.newaxis] - lon2[np.newaxis, :]

    # Haversine formula
    a = (np.sin(dlat / 2) ** 2 +
         np.cos(lat1[:, np.newaxis]) * np.cos(lat2[np.newaxis, :]) *
         np.sin(dlon / 2) ** 2)
    c = 2 * np.arcsin(np.sqrt(a))

    return R * c


def spatial_match_facilities(
    gem_df: pd.DataFrame,
    eprtr_df: pd.DataFrame,
    max_distance_km: float = 1.0
) -> pd.DataFrame:
    """
    Match GEM plants to E-PRTR facilities by spatial proximity.

    For each GEM plant, finds the nearest E-PRTR facility within threshold.

    Parameters
    ----------
    gem_df : pd.DataFrame
        GEM plants with lat, lon columns
    eprtr_df : pd.DataFrame
        E-PRTR facilities with lat, lon columns
    max_distance_km : float
        Maximum distance for a valid match (default 1 km)

    Returns
    -------
    pd.DataFrame
        Matched facilities with columns from both sources plus:
        - match_distance_km: Distance between matched facilities
    """
    gem_coords = gem_df[['lat', 'lon']].values
    eprtr_coords = eprtr_df[['lat', 'lon']].values

    # Compute cross-distance matrix
    dist_matrix = haversine_cross_distances(gem_coords, eprtr_coords)

    # For each GEM plant, find nearest E-PRTR facility
    matches = []
    for i, gem_row in gem_df.iterrows():
        gem_idx = gem_df.index.get_loc(i)
        distances = dist_matrix[gem_idx, :]
        min_idx = np.argmin(distances)
        min_dist = distances[min_idx]

        if min_dist <= max_distance_km:
            eprtr_row = eprtr_df.iloc[min_idx]
            matches.append({
                # GEM data
                'gem_plant_id': gem_row['plant_id'],
                'gem_plant_name': gem_row['plant_name'],
                'gem_country': gem_row['country'],
                'gem_lat': gem_row['lat'],
                'gem_lon': gem_row['lon'],
                'gem_regime': gem_row['gem_regime'],
                'bof_cap': gem_row['bof_cap'],
                'eaf_cap': gem_row['eaf_cap'],
                'bf_cap': gem_row['bf_cap'],
                'dri_cap': gem_row['dri_cap'],
                'total_steel_cap': gem_row.get('total_steel_cap', np.nan),
                # E-PRTR data
                'eprtr_facility_id': eprtr_row['facility_id'],
                'eprtr_facility_name': eprtr_row['facility_name'],
                'eprtr_country_code': eprtr_row['country_code'],
                'eprtr_lat': eprtr_row['lat'],
                'eprtr_lon': eprtr_row['lon'],
                'eprtr_ied_activity': eprtr_row['ied_activity'],
                # Match info
                'match_distance_km': min_dist
            })

    matched_df = pd.DataFrame(matches)
    n_gem = len(gem_df)
    n_matched = len(matched_df)
    match_rate = n_matched / n_gem * 100 if n_gem > 0 else 0

    print(f"Spatial matching: {n_matched}/{n_gem} GEM plants matched ({match_rate:.1f}%)")
    print(f"  Match threshold: {max_distance_km} km")
    if len(matched_df) > 0:
        print(f"  Mean match distance: {matched_df['match_distance_km'].mean():.3f} km")

    return matched_df


def calculate_regime_accuracy(
    matched_df: pd.DataFrame,
    predicted_regime_col: str = 'predicted_regime'
) -> Dict:
    """
    Calculate accuracy metrics for regime classification.

    Parameters
    ----------
    matched_df : pd.DataFrame
        Matched facilities with 'gem_regime' (ground truth) and
        predicted_regime_col columns
    predicted_regime_col : str
        Column name for predicted regime

    Returns
    -------
    dict
        Accuracy metrics including:
        - accuracy: Overall accuracy
        - confusion_matrix: DataFrame with actual vs predicted counts
        - precision: Dict by regime
        - recall: Dict by regime
        - n_samples: Number of samples used
    """
    # Filter to rows with valid predictions
    df = matched_df.dropna(subset=[predicted_regime_col, 'gem_regime'])

    if len(df) == 0:
        return {
            'accuracy': 0.0,
            'confusion_matrix': pd.DataFrame(),
            'precision': {},
            'recall': {},
            'n_samples': 0
        }

    actual = df['gem_regime']
    predicted = df[predicted_regime_col]

    # Overall accuracy
    accuracy = (actual == predicted).mean()

    # Confusion matrix
    confusion = pd.crosstab(actual, predicted, rownames=['Actual'], colnames=['Predicted'])

    # Per-class precision and recall
    regimes = ['BF_BOF', 'EAF', 'MIXED', 'UNKNOWN']
    precision = {}
    recall = {}

    for regime in regimes:
        # Precision: of predicted regime, how many are correct
        pred_mask = predicted == regime
        if pred_mask.sum() > 0:
            precision[regime] = (actual[pred_mask] == regime).mean()
        else:
            precision[regime] = np.nan

        # Recall: of actual regime, how many were predicted correctly
        actual_mask = actual == regime
        if actual_mask.sum() > 0:
            recall[regime] = (predicted[actual_mask] == regime).mean()
        else:
            recall[regime] = np.nan

    return {
        'accuracy': accuracy,
        'confusion_matrix': confusion,
        'precision': precision,
        'recall': recall,
        'n_samples': len(df)
    }


def classify_regime_from_emissions(
    co2_emissions_kg: float,
    co_emissions_kg: float,
    capacity_ttpa: float,
    co2_threshold: float = 500.0,
    co_threshold: float = 5.0
) -> str:
    """
    Classify regime based on CO2 and CO emissions intensity.

    CO (carbon monoxide) is the strongest discriminator - 18x higher in BF/BOF.
    CO2 alone is less reliable due to incomplete E-PRTR reporting.

    Classification logic: BF_BOF if CO2 >= threshold OR CO >= threshold

    Parameters
    ----------
    co2_emissions_kg : float
        Annual CO2 emissions in kg
    co_emissions_kg : float
        Annual CO emissions in kg
    capacity_ttpa : float
        Steel capacity in thousand tonnes per annum
    co2_threshold : float
        kg CO2/tonne threshold (default 500)
    co_threshold : float
        kg CO/tonne threshold (default 5)

    Returns
    -------
    str
        'BF_BOF', 'EAF', or 'UNKNOWN'
    """
    if pd.isna(capacity_ttpa) or capacity_ttpa <= 0:
        return 'UNKNOWN'

    capacity_tonnes = capacity_ttpa * 1000

    # Check CO2 intensity
    co2_high = False
    if pd.notna(co2_emissions_kg) and co2_emissions_kg > 0:
        co2_intensity = co2_emissions_kg / capacity_tonnes
        co2_high = co2_intensity >= co2_threshold

    # Check CO intensity (strongest discriminator)
    co_high = False
    if pd.notna(co_emissions_kg) and co_emissions_kg > 0:
        co_intensity = co_emissions_kg / capacity_tonnes
        co_high = co_intensity >= co_threshold

    # Need at least one measurement
    if not pd.notna(co2_emissions_kg) and not pd.notna(co_emissions_kg):
        return 'UNKNOWN'

    # BF_BOF if either threshold exceeded
    if co2_high or co_high:
        return 'BF_BOF'
    return 'EAF'


def add_emissions_to_matched(
    matched_df: pd.DataFrame,
    emissions_df: pd.DataFrame,
    max_distance_km: float = 5.0,
    co2_threshold: float = 500.0,
    co_threshold: float = 5.0
) -> pd.DataFrame:
    """
    Add emissions data to matched facilities via spatial matching.

    Uses both CO2 and CO (carbon monoxide) for classification.
    CO is the strongest discriminator (18x higher in BF/BOF).

    Parameters
    ----------
    matched_df : pd.DataFrame
        Matched GEM-EPRTR facilities
    emissions_df : pd.DataFrame
        Emissions with lat, lon, pollutant, releases
    max_distance_km : float
        Max distance for emissions matching
    co2_threshold : float
        kg CO2/tonne threshold for BF_BOF classification
    co_threshold : float
        kg CO/tonne threshold for BF_BOF classification

    Returns
    -------
    pd.DataFrame
        Matched dataframe with emissions, intensities, predicted_regime
    """
    # Get CO2 and CO emissions aggregated by location
    co2_mask = emissions_df['pollutant'].str.contains('Carbon dioxide', case=False, na=False)
    co_mask = emissions_df['pollutant'] == 'Carbon monoxide (CO)'

    co2_totals = emissions_df[co2_mask].groupby(['lat', 'lon'])['releases'].sum().reset_index()
    co2_totals.columns = ['em_lat', 'em_lon', 'co2_emissions']

    co_totals = emissions_df[co_mask].groupby(['lat', 'lon'])['releases'].sum().reset_index()
    co_totals.columns = ['em_lat', 'em_lon', 'co_emissions']

    # Merge CO2 and CO by location
    em_combined = co2_totals.merge(co_totals, on=['em_lat', 'em_lon'], how='outer')
    em_combined = em_combined.dropna(subset=['em_lat', 'em_lon'])

    if len(em_combined) == 0:
        result = matched_df.copy()
        result['co2_emissions'] = np.nan
        result['co_emissions'] = np.nan
        result['co2_intensity'] = np.nan
        result['co_intensity'] = np.nan
        result['predicted_regime'] = 'UNKNOWN'
        return result

    # Spatial matching
    matched_coords = matched_df[['eprtr_lat', 'eprtr_lon']].values
    emissions_coords = em_combined[['em_lat', 'em_lon']].values
    dist_matrix = haversine_cross_distances(matched_coords, emissions_coords)

    # Add emissions to each matched facility
    result = matched_df.copy()
    co2_values = []
    co_values = []

    for i in range(len(matched_df)):
        distances = dist_matrix[i, :]
        min_idx = np.argmin(distances)
        min_dist = distances[min_idx]

        if min_dist <= max_distance_km:
            co2_values.append(em_combined.iloc[min_idx]['co2_emissions'])
            co_values.append(em_combined.iloc[min_idx]['co_emissions'])
        else:
            co2_values.append(np.nan)
            co_values.append(np.nan)

    result['co2_emissions'] = co2_values
    result['co_emissions'] = co_values

    # Calculate intensities (kg / tonne capacity)
    def calc_intensity(emissions, capacity):
        if pd.notna(emissions) and pd.notna(capacity) and capacity > 0:
            return emissions / (capacity * 1000)
        return np.nan

    result['co2_intensity'] = result.apply(
        lambda row: calc_intensity(row['co2_emissions'], row['total_steel_cap']), axis=1
    )
    result['co_intensity'] = result.apply(
        lambda row: calc_intensity(row['co_emissions'], row['total_steel_cap']), axis=1
    )

    # Predict regime from emissions intensity (using both CO2 and CO)
    result['predicted_regime'] = result.apply(
        lambda row: classify_regime_from_emissions(
            row['co2_emissions'], row['co_emissions'], row['total_steel_cap'],
            co2_threshold, co_threshold
        ),
        axis=1
    )

    n_with_co2 = result['co2_emissions'].notna().sum()
    n_with_co = result['co_emissions'].notna().sum()
    n_with_any = ((result['co2_emissions'].notna()) | (result['co_emissions'].notna())).sum()
    print(f"  Matched emissions: CO2={n_with_co2}, CO={n_with_co}, any={n_with_any}/{len(result)}")

    return result


def run_steel_tracker_validation(
    gem_path: Optional[Path] = None,
    eprtr_facilities_path: Optional[Path] = None,
    eprtr_emissions_path: Optional[Path] = None,
    max_distance_km: float = 5.0,
    emissions_match_km: float = 5.0,
    co2_threshold: float = 500.0,
    co_threshold: float = 5.0,
    save_results: bool = True
) -> Dict:
    """
    Run full steel tracker validation pipeline.

    Validates emissions-based regime classification against GEM ground truth.

    Parameters
    ----------
    gem_path : Path, optional
        Path to GEM Excel file
    eprtr_facilities_path : Path, optional
        Path to E-PRTR facilities CSV
    eprtr_emissions_path : Path, optional
        Path to E-PRTR air releases CSV
    max_distance_km : float
        Maximum matching distance for GEM-EPRTR (default 5 km)
    emissions_match_km : float
        Maximum distance for emissions matching (default 5 km)
    intensity_threshold : float
        CO2 intensity threshold (kg/tonne) for regime classification
    save_results : bool
        Whether to save results to CSV

    Returns
    -------
    dict
        Validation results including matched data, accuracy metrics
    """
    print("=" * 60)
    print("STEEL TRACKER VALIDATION PIPELINE")
    print("=" * 60)

    # Step 1: Load GEM data
    print("\n1. Loading GEM steel plants...")
    gem_plants = load_gem_steel_plants(gem_path)

    # Step 2: Load E-PRTR facilities
    print("\n2. Loading E-PRTR steel facilities...")
    eprtr_facilities = load_eprtr_steel_facilities(eprtr_facilities_path)

    # Step 3: Spatial matching GEM to E-PRTR
    print("\n3. Performing spatial matching...")
    matched = spatial_match_facilities(gem_plants, eprtr_facilities, max_distance_km)
    match_rate = len(matched) / len(gem_plants) * 100 if len(gem_plants) > 0 else 0

    # Step 4: Add emissions and predict regime
    print("\n4. Adding emissions data and predicting regime...")
    print(f"  Thresholds: CO2 >= {co2_threshold} OR CO >= {co_threshold} kg/tonne => BF_BOF")
    emissions = load_eprtr_emissions_with_coords(eprtr_emissions_path)
    matched = add_emissions_to_matched(
        matched, emissions, emissions_match_km, co2_threshold, co_threshold
    )

    # Step 5: Calculate regime accuracy
    print("\n5. Calculating regime classification accuracy...")

    # Accuracy including UNKNOWN (all matched plants)
    accuracy_results = calculate_regime_accuracy(matched, 'predicted_regime')

    # Accuracy excluding UNKNOWN (plants with emissions data only)
    matched_with_pred = matched[matched['predicted_regime'] != 'UNKNOWN']
    accuracy_excl_unknown = calculate_regime_accuracy(matched_with_pred, 'predicted_regime')

    print(f"\n  REGIME CLASSIFICATION ACCURACY")
    print(f"  ================================")
    print(f"  Plants matched to E-PRTR: {len(matched)}")
    print(f"  Plants with emissions data: {len(matched_with_pred)}")
    print(f"  Accuracy (with emissions): {accuracy_excl_unknown['accuracy']:.1%}")
    print(f"  Accuracy (all, UNKNOWN=wrong): {accuracy_results['accuracy']:.1%}")
    print(f"\n  Confusion Matrix (excluding UNKNOWN predictions):")
    if len(accuracy_excl_unknown['confusion_matrix']) > 0:
        print(accuracy_excl_unknown['confusion_matrix'].to_string())
    print(f"\n  Precision: BF_BOF={accuracy_excl_unknown['precision'].get('BF_BOF', 0):.1%}, EAF={accuracy_excl_unknown['precision'].get('EAF', 0):.1%}")
    print(f"  Recall: BF_BOF={accuracy_excl_unknown['recall'].get('BF_BOF', 0):.1%}, EAF={accuracy_excl_unknown['recall'].get('EAF', 0):.1%}")

    # Step 6: Save results
    if save_results and len(matched) > 0:
        print("\n6. Saving results...")
        output_dir = PROCESSED_DIR / "validation"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save matched facilities with predictions
        matched_path = output_dir / "gem_eprtr_matched.csv"
        matched.to_csv(matched_path, index=False)
        print(f"  Saved matched facilities to: {matched_path}")

        # Save accuracy report
        report_rows = [
            {'metric': 'gem_plants_total', 'value': len(gem_plants)},
            {'metric': 'eprtr_facilities_total', 'value': len(eprtr_facilities)},
            {'metric': 'matched_count', 'value': len(matched)},
            {'metric': 'match_rate_pct', 'value': match_rate},
            {'metric': 'plants_with_emissions', 'value': len(matched_with_pred)},
            {'metric': 'max_distance_km', 'value': max_distance_km},
            {'metric': 'co2_threshold', 'value': co2_threshold},
            {'metric': 'co_threshold', 'value': co_threshold},
            {'metric': 'regime_accuracy_with_emissions', 'value': accuracy_excl_unknown['accuracy']},
            {'metric': 'regime_accuracy_all', 'value': accuracy_results['accuracy']},
            {'metric': 'precision_BF_BOF', 'value': accuracy_excl_unknown['precision'].get('BF_BOF', np.nan)},
            {'metric': 'precision_EAF', 'value': accuracy_excl_unknown['precision'].get('EAF', np.nan)},
            {'metric': 'recall_BF_BOF', 'value': accuracy_excl_unknown['recall'].get('BF_BOF', np.nan)},
            {'metric': 'recall_EAF', 'value': accuracy_excl_unknown['recall'].get('EAF', np.nan)},
        ]
        report = pd.DataFrame(report_rows)
        report_path = output_dir / "regime_accuracy_report.csv"
        report.to_csv(report_path, index=False)
        print(f"  Saved report to: {report_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"GEM European plants: {len(gem_plants)}")
    print(f"E-PRTR steel facilities: {len(eprtr_facilities)}")
    print(f"Matched to E-PRTR: {len(matched)} ({match_rate:.1f}%)")
    print(f"With emissions data: {len(matched_with_pred)}")
    print(f"\nGround truth regime distribution:")
    print(f"  {matched['gem_regime'].value_counts().to_dict()}")
    print(f"\nPredicted regime distribution:")
    print(f"  {matched['predicted_regime'].value_counts().to_dict()}")
    print(f"\nREGIME CLASSIFICATION ACCURACY: {accuracy_excl_unknown['accuracy']:.1%}")
    print(f"  (on {len(matched_with_pred)} plants with emissions data)")

    return {
        'gem_plants': gem_plants,
        'eprtr_facilities': eprtr_facilities,
        'matched': matched,
        'match_rate': match_rate,
        'accuracy_results': accuracy_excl_unknown,
        'accuracy_all': accuracy_results
    }


if __name__ == '__main__':
    run_steel_tracker_validation(save_results=True)
