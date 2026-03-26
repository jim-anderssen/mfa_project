"""
Rules-Based Technology Classifier using Emission Intensity Thresholds.

Classifies facilities into technology regimes based on emission intensities
derived from BREF (Best Available Techniques Reference Documents).

For steel (IED 2.x):
- CO intensity is 18x higher in BF/BOF vs EAF (strongest discriminator)
- CO2 intensity: BF/BOF ~1800-2200 kg/t, EAF ~70-180 kg/t
- Metal emissions (Zn, Pb) much higher in EAF (scrap recycling)
- Works with or without capacity data using pollutant ratios
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, List
from pathlib import Path


def load_process_emissions_thresholds(csv_path: Optional[Path] = None) -> Dict:
    """
    Load emission intensity thresholds from BREF process_emissions.csv.

    Extracts min/max values for BF+BOF vs EAF from the BREF data.

    Parameters
    ----------
    csv_path : Path, optional
        Path to process_emissions.csv. If None, uses default location.

    Returns
    -------
    dict
        Thresholds by IED code, pollutant, and regime
    """
    if csv_path is None:
        # Try default location
        csv_path = Path(__file__).parent.parent.parent / 'data' / 'raw' / 'process_emissions.csv'

    if not csv_path.exists():
        print(f"Warning: process_emissions.csv not found at {csv_path}, using fallback thresholds")
        return DEFAULT_THRESHOLDS

    df = pd.read_csv(csv_path)

    # Filter to air emissions
    df = df[df['category'] == 'Air Emissions'].copy()

    # Standardize pollutant names
    pollutant_map = {
        'Carbon dioxide (CO₂)': 'CO2',
        'Carbon monoxide (CO)': 'CO',
        'Sulphur dioxide (SO₂)': 'SOx',
        'Nitrogen oxides (NOₓ as NO₂)': 'NOx',
        'SOₓ': 'SOx',
        'NOₓ': 'NOx',
        'Zinc (Zn)': 'Zn',
        'Lead (Pb)': 'Pb',
        'Mercury (Hg)': 'Hg',
        'Chromium (Cr)': 'Cr',
        'Nickel (Ni)': 'Ni',
        'Dusts': 'Dust',
        'TOC': 'TOC',
        'Benzene': 'Benzene',
    }

    df['pollutant'] = df['parameter'].map(pollutant_map).fillna(df['parameter'])

    # Convert units to g/tonne for consistency
    def normalize_to_g_per_tonne(row):
        """Convert all emissions to g/tonne basis."""
        unit = row['unit']
        min_val = row['min_value']
        max_val = row['max_value']

        # Convert to g/tonne
        if unit == 'kg':
            min_val = min_val * 1000 if pd.notna(min_val) else None
            max_val = max_val * 1000 if pd.notna(max_val) else None
        elif unit == 'mg':
            min_val = min_val / 1000 if pd.notna(min_val) else None
            max_val = max_val / 1000 if pd.notna(max_val) else None
        elif unit == 'µg I-TEQ' or unit == 'ng I-TEQ':
            # Skip dioxins for now (specialized)
            return None, None
        # else unit == 'g', keep as is

        return min_val, max_val

    df[['min_g_tonne', 'max_g_tonne']] = df.apply(
        lambda row: pd.Series(normalize_to_g_per_tonne(row)), axis=1
    )

    # Build thresholds for BF/BOF vs EAF
    thresholds = {'2.b': {}}

    # BF+BOF: Combine Blast Furnace and BOF emissions
    bf_bof_processes = ['Blast Furnaces', 'BOF Steelmaking']
    eaf_process = 'EAF Steelmaking'

    for pollutant in ['CO2', 'CO', 'SO2', 'NOx', 'Zn', 'Pb', 'Dust', 'TOC', 'Benzene']:
        # BF/BOF thresholds (use BOF ranges as primary for steel production)
        bf_bof_data = df[
            (df['process'].isin(bf_bof_processes)) &
            (df['pollutant'] == pollutant)
        ][['min_g_tonne', 'max_g_tonne']]

        # EAF thresholds
        eaf_data = df[
            (df['process'] == eaf_process) &
            (df['pollutant'] == pollutant)
        ][['min_g_tonne', 'max_g_tonne']]

        if pollutant not in thresholds['2.b']:
            thresholds['2.b'][pollutant] = {}

        # For BF/BOF, use max of BOF ranges (conservative)
        if len(bf_bof_data) > 0:
            bf_bof_max = bf_bof_data['max_g_tonne'].max()
            bf_bof_min = bf_bof_data['min_g_tonne'].min()
            if pd.notna(bf_bof_max):
                thresholds['2.b'][pollutant]['BF_BOF'] = (bf_bof_min, bf_bof_max)

        # For EAF
        if len(eaf_data) > 0:
            eaf_max = eaf_data['max_g_tonne'].max()
            eaf_min = eaf_data['min_g_tonne'].min()
            if pd.notna(eaf_max):
                thresholds['2.b'][pollutant]['EAF'] = (eaf_min, eaf_max)

    return thresholds


# Fallback thresholds if process_emissions.csv not available
DEFAULT_THRESHOLDS = {
    '2.b': {
        'CO2': {'BF_BOF': (22600, 174000), 'EAF': (72000, 180000)},  # g/tonne
        'CO': {'BF_BOF': (393, 7200), 'EAF': (50, 4500)},  # g/tonne
        'Zn': {'BF_BOF': (0.0082, 66.1), 'EAF': (0.2, 24)},  # g/tonne
        'Pb': {'BF_BOF': (0.0022, 0.98), 'EAF': (0.075, 2.85)},  # g/tonne
    }
}


def classify_regime_from_emissions(
    emissions_dict: Dict[str, float],
    capacity_tonnes: Optional[float] = None,
    thresholds: Optional[Dict] = None,
    use_ratios: bool = True
) -> Tuple[str, float]:
    """
    Classify technology regime using all available emission data.

    Uses intensity-based classification (when capacity available) or
    ratio-based classification (when capacity unavailable).

    Key discriminators from BREF:
    - CO/CO2 ratio: BF/BOF has higher CO relative to CO2
    - Zn, Pb: Much higher in EAF (scrap recycling)
    - SOx: Higher in BF/BOF (from blast furnace)

    Parameters
    ----------
    emissions_dict : dict
        Pollutant name -> emissions in kg (e.g., {'CO2': 2e9, 'CO': 3e7, 'Zn': 15000})
    capacity_tonnes : float, optional
        Production capacity in tonnes per year (enables intensity matching)
    thresholds : dict, optional
        Emission thresholds from load_process_emissions_thresholds()
    use_ratios : bool
        If True, use pollutant ratios for classification (works without capacity)

    Returns
    -------
    regime : str
        'BF_BOF', 'EAF', or 'UNKNOWN'
    confidence : float
        Classification confidence (0.0 to 1.0)
    """
    if not emissions_dict or all(v == 0 for v in emissions_dict.values()):
        return 'UNKNOWN', 0.0

    if thresholds is None:
        thresholds = load_process_emissions_thresholds()

    steel_thresholds = thresholds.get('2.b', {})

    # Normalize pollutant names (from E-PRTR format to standard format)
    normalized_emissions = {}
    name_map = {
        'Carbon dioxide (CO2)': 'CO2',
        'Carbon dioxide': 'CO2',
        'Carbon monoxide (CO)': 'CO',
        'Carbon monoxide': 'CO',
        'Sulphur oxides (SOx/SO2)': 'SO2',
        'Sulphur dioxide (SO2)': 'SO2',
        'Nitrogen oxides (NOx/NO2)': 'NOx',
        'Nitrogen oxides': 'NOx',
        'Zinc (Zn)': 'Zn',
        'Zinc': 'Zn',
        'Lead (Pb)': 'Pb',
        'Lead': 'Pb',
        'Total organic carbon (TOC)': 'TOC',
        'Benzene': 'Benzene',
    }

    for pollutant, value in emissions_dict.items():
        clean_name = name_map.get(pollutant, pollutant)
        # Convert kg to g for consistency
        normalized_emissions[clean_name] = value * 1000 if value else 0

    # Strategy 1: Intensity-based (if capacity available)
    if capacity_tonnes and capacity_tonnes > 0:
        intensity_scores = {'BF_BOF': 0, 'EAF': 0}
        votes = {'BF_BOF': 0, 'EAF': 0}

        for pollutant, emission_g in normalized_emissions.items():
            if pollutant not in steel_thresholds or emission_g == 0:
                continue

            intensity = emission_g / capacity_tonnes

            # Check which regime's range this intensity falls into
            for regime in ['BF_BOF', 'EAF']:
                if regime not in steel_thresholds[pollutant]:
                    continue

                min_val, max_val = steel_thresholds[pollutant][regime]

                if pd.isna(min_val) or pd.isna(max_val):
                    continue

                # Check if intensity is in range or close
                if min_val <= intensity <= max_val:
                    intensity_scores[regime] += 1.0
                    votes[regime] += 1
                elif intensity < min_val:
                    # Below range - give partial credit based on distance
                    distance = (min_val - intensity) / min_val
                    score = max(0, 1.0 - distance)
                    intensity_scores[regime] += score
                    votes[regime] += score
                else:
                    # Above range - give partial credit
                    distance = (intensity - max_val) / max_val
                    score = max(0, 1.0 - distance)
                    intensity_scores[regime] += score
                    votes[regime] += score

        if max(votes.values()) > 0:
            best_regime = max(intensity_scores, key=intensity_scores.get)
            confidence = intensity_scores[best_regime] / max(sum(votes.values()), 1)
            return best_regime, min(1.0, confidence)

    # Strategy 2: Ratio-based (works without capacity)
    if use_ratios:
        ratio_scores = {'BF_BOF': 0, 'EAF': 0}

        co2 = normalized_emissions.get('CO2', 0)
        co = normalized_emissions.get('CO', 0)
        zn = normalized_emissions.get('Zn', 0)
        pb = normalized_emissions.get('Pb', 0)
        so2 = normalized_emissions.get('SO2', 0)
        nox = normalized_emissions.get('NOx', 0)

        # Ratio 1: CO/CO2 (BF/BOF has higher ratio)
        if co2 > 0 and co > 0:
            co_co2_ratio = co / co2

            # BF/BOF typical range: 0.002-0.04 (393-7200g CO per 22600-174000g CO2)
            # EAF typical range: 0.0003-0.06 (50-4500g CO per 72000-180000g CO2)
            # But BF/BOF typically higher, especially with blast furnace

            if co_co2_ratio > 0.01:  # High CO/CO2 suggests BF/BOF
                ratio_scores['BF_BOF'] += 1.0
            else:
                ratio_scores['EAF'] += 0.5

        # Ratio 2: Zn/CO2 (EAF has much higher Zn from scrap)
        if co2 > 0 and zn > 0:
            zn_co2_ratio = zn / co2

            # EAF: 0.2-24g Zn per 72000-180000g CO2 = 1e-6 to 3e-4
            # BF/BOF: 0.008-66g Zn per 22600-174000g CO2 = 4e-8 to 3e-3 (but typically low)

            if zn_co2_ratio > 1e-5:  # High Zn suggests EAF
                ratio_scores['EAF'] += 2.0  # Strong signal
            else:
                ratio_scores['BF_BOF'] += 0.5

        # Ratio 3: Pb/CO2 (EAF higher)
        if co2 > 0 and pb > 0:
            pb_co2_ratio = pb / co2

            if pb_co2_ratio > 5e-6:  # High Pb suggests EAF
                ratio_scores['EAF'] += 1.0
            else:
                ratio_scores['BF_BOF'] += 0.3

        # Ratio 4: SO2/NOx (BF/BOF higher SO2 from sinter/BF)
        if nox > 0 and so2 > 0:
            so2_nox_ratio = so2 / nox

            # BF: high SO2 (7-194g) vs low NOx (~2g) = high ratio
            # EAF: lower SO2 (5-210g) vs higher NOx (13-460g) = lower ratio

            if so2_nox_ratio > 2:  # High SO2/NOx suggests BF/BOF
                ratio_scores['BF_BOF'] += 1.0
            else:
                ratio_scores['EAF'] += 0.5

        # Absolute checks
        # Very high Zn or Pb in absolute terms strongly suggests EAF
        if zn > 1e7:  # > 10 tonnes Zn suggests large EAF
            ratio_scores['EAF'] += 1.5
        if pb > 1e6:  # > 1 tonne Pb suggests EAF
            ratio_scores['EAF'] += 1.0

        total_score = sum(ratio_scores.values())
        if total_score > 0:
            best_regime = max(ratio_scores, key=ratio_scores.get)
            confidence = ratio_scores[best_regime] / total_score
            return best_regime, min(1.0, confidence)

    return 'UNKNOWN', 0.0


def classify_facilities_batch(
    emissions_df: pd.DataFrame,
    capacity_df: Optional[pd.DataFrame] = None,
    capacity_col: str = 'capacity_tonnes',
    thresholds: Optional[Dict] = None
) -> pd.DataFrame:
    """
    Classify multiple facilities using rules-based approach with all pollutants.

    Parameters
    ----------
    emissions_df : pd.DataFrame
        Emissions from E-PRTR
        Required: facility_id, pollutant, release_kg
    capacity_df : pd.DataFrame, optional
        Capacity data with columns: facility_id, capacity_tonnes
        If not provided, will use ratio-based classification
    capacity_col : str
        Column name for capacity in capacity_df
    thresholds : dict, optional
        Emission thresholds from load_process_emissions_thresholds()

    Returns
    -------
    pd.DataFrame
        Facilities with technology_regime, classification_confidence, method
    """
    if thresholds is None:
        thresholds = load_process_emissions_thresholds()

    # Build capacity lookup
    capacity_lookup = {}
    if capacity_df is not None:
        capacity_lookup = dict(zip(
            capacity_df['facility_id'],
            capacity_df[capacity_col]
        ))

    # Aggregate all emissions by facility and pollutant
    emissions_by_facility = emissions_df.groupby(['facility_id', 'pollutant'])['release_kg'].sum().reset_index()

    # Classify each facility
    results = []
    for facility_id in emissions_by_facility['facility_id'].unique():
        fac_emissions = emissions_by_facility[emissions_by_facility['facility_id'] == facility_id]

        # Build emissions dict
        emissions_dict = dict(zip(fac_emissions['pollutant'], fac_emissions['release_kg']))

        # Get capacity if available
        capacity = capacity_lookup.get(facility_id, None)

        # Classify
        regime, confidence = classify_regime_from_emissions(
            emissions_dict,
            capacity_tonnes=capacity,
            thresholds=thresholds,
            use_ratios=True
        )

        results.append({
            'facility_id': facility_id,
            'technology_regime': regime,
            'classification_confidence': confidence,
            'classification_method': 'intensity' if capacity else 'ratio',
            'n_pollutants': len(emissions_dict)
        })

    return pd.DataFrame(results)


def calculate_regime_accuracy(
    matched_df: pd.DataFrame,
    predicted_col: str = 'predicted_regime',
    actual_col: str = 'gem_regime'
) -> Dict:
    """
    Calculate accuracy metrics for regime classification.

    Parameters
    ----------
    matched_df : pd.DataFrame
        Facilities with actual and predicted regimes
    predicted_col : str
        Column name for predicted regime
    actual_col : str
        Column name for ground truth regime

    Returns
    -------
    dict
        Accuracy metrics
    """
    df = matched_df.dropna(subset=[predicted_col, actual_col])

    if len(df) == 0:
        return {
            'accuracy': 0.0,
            'confusion_matrix': pd.DataFrame(),
            'precision': {},
            'recall': {},
            'n_samples': 0
        }

    actual = df[actual_col]
    predicted = df[predicted_col]

    accuracy = (actual == predicted).mean()
    confusion = pd.crosstab(actual, predicted, rownames=['Actual'], colnames=['Predicted'])

    regimes = ['BF_BOF', 'EAF', 'MIXED', 'UNKNOWN']
    precision = {}
    recall = {}

    for regime in regimes:
        pred_mask = predicted == regime
        if pred_mask.sum() > 0:
            precision[regime] = (actual[pred_mask] == regime).mean()
        else:
            precision[regime] = np.nan

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


def get_thresholds_for_ied(ied_code: str) -> Dict[str, Dict[str, float]]:
    """
    Get emission thresholds for an IED activity code.

    Parameters
    ----------
    ied_code : str
        IED activity code (e.g., '2.b' for iron/steel)

    Returns
    -------
    dict
        Thresholds by pollutant and regime
    """
    # Normalize IED code (handle formats like '2(b)' -> '2.b')
    normalized = ied_code.replace('(', '.').replace(')', '').rstrip('.')

    # Check for exact match
    if normalized in DEFAULT_THRESHOLDS:
        return DEFAULT_THRESHOLDS[normalized]

    # Try parent code (e.g., '2' for '2.b')
    parent = normalized.split('.')[0]
    for code in DEFAULT_THRESHOLDS:
        if code.startswith(parent):
            return DEFAULT_THRESHOLDS[code]

    # Default fallback
    return DEFAULT_THRESHOLDS.get('2.b', {})


if __name__ == '__main__':
    # Test classification
    test_cases = [
        # (CO2_kg, CO_kg, capacity_tonnes, expected)
        (2_000_000_000, 50_000_000, 1_000_000, 'BF_BOF'),  # Integrated plant
        (150_000_000, 1_000_000, 1_000_000, 'EAF'),        # Electric arc furnace
        (None, None, 1_000_000, 'UNKNOWN'),                 # No emissions data
    ]

    print("Testing rules-based classifier:")
    for co2, co, cap, expected in test_cases:
        regime, conf = classify_regime_from_emissions(co2, co, cap)
        status = "OK" if regime == expected else "FAIL"
        print(f"  {status}: CO2={co2}, CO={co}, cap={cap} -> {regime} (conf={conf:.2f})")
