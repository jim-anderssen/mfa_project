"""
Emissions-Based Waste Generation Estimation.

Estimates facility-level waste generation by:
1. Back-calculating production from CO2 emissions using BREF factors
2. Applying BREF waste generation factors per technology regime

Logic:
    Production_min = CO2_emissions / CO2_max_factor
    Production_max = CO2_emissions / CO2_min_factor
    Waste_min = Production_max * Waste_factor_min
    Waste_max = Production_min * Waste_factor_max
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings


# Default CO2 emission factors (kg CO2 per tonne product)
CO2_FACTORS = {
    'BF_BOF': {'min': 1800.0, 'max': 2200.0},  # Integrated route
    'EAF': {'min': 72.0, 'max': 180.0},
    'MIXED': {'min': 500.0, 'max': 1500.0},  # Weighted average estimate
    'UNKNOWN': {'min': 200.0, 'max': 2000.0},  # Wide range for unknown
}

# Waste generation factors (kg waste per tonne product)
WASTE_FACTORS = {
    'BF_BOF': {
        'slag': {'min': 250.0, 'max': 525.0},
        'dust': {'min': 10.0, 'max': 65.0},
    },
    'EAF': {
        'slag': {'min': 70.0, 'max': 350.0},
        'dust': {'min': 10.0, 'max': 30.0},
    },
    'MIXED': {
        'slag': {'min': 100.0, 'max': 450.0},
        'dust': {'min': 10.0, 'max': 50.0},
    },
    'UNKNOWN': {
        'slag': {'min': 70.0, 'max': 525.0},
        'dust': {'min': 10.0, 'max': 65.0},
    },
}


def load_bref_factors(
    factors_path: Optional[Path] = None
) -> Tuple[Dict, Dict]:
    """
    Load BREF factors from CSV lookup table.

    Parameters
    ----------
    factors_path : Path, optional
        Path to bref_waste_factors.csv

    Returns
    -------
    co2_factors : dict
        CO2 emission factors by technology regime
    waste_factors : dict
        Waste generation factors by regime and waste type
    """
    if factors_path is None:
        factors_path = Path('data/processed/lookuptables/bref_waste_factors.csv')

    if not factors_path.exists():
        warnings.warn(f"BREF factors file not found at {factors_path}, using defaults")
        return CO2_FACTORS, WASTE_FACTORS

    df = pd.read_csv(factors_path, comment='#')

    # Parse CO2 factors
    co2_mask = df['parameter'] == 'co2_emission_factor'
    co2_factors = {}
    for regime in ['BF_BOF', 'EAF']:
        regime_rows = df[(co2_mask) & (df['technology_regime'] == regime)]
        if len(regime_rows) > 0:
            co2_factors[regime] = {
                'min': regime_rows['min_value'].min(),
                'max': regime_rows['max_value'].max(),
            }

    # Fallback to defaults for missing regimes
    for regime in CO2_FACTORS:
        if regime not in co2_factors:
            co2_factors[regime] = CO2_FACTORS[regime]

    # Parse waste factors
    waste_mask = df['parameter'] == 'waste_factor'
    waste_factors = {}
    for regime in ['BF_BOF', 'EAF', 'MIXED', 'UNKNOWN']:
        waste_factors[regime] = {}

        # Slag
        slag_mask = (waste_mask) & (df['waste_category'] == 'slag') & (df['technology_regime'] == regime)
        slag_rows = df[slag_mask]
        if len(slag_rows) > 0:
            waste_factors[regime]['slag'] = {
                'min': slag_rows['min_value'].min(),
                'max': slag_rows['max_value'].max(),
            }
        elif regime in WASTE_FACTORS:
            waste_factors[regime]['slag'] = WASTE_FACTORS[regime].get('slag', {'min': 100, 'max': 400})

        # Dust
        dust_mask = (waste_mask) & (df['waste_category'] == 'dust') & (df['technology_regime'] == regime)
        dust_rows = df[dust_mask]
        if len(dust_rows) > 0:
            waste_factors[regime]['dust'] = {
                'min': dust_rows['min_value'].min(),
                'max': dust_rows['max_value'].max(),
            }
        elif regime in WASTE_FACTORS:
            waste_factors[regime]['dust'] = WASTE_FACTORS[regime].get('dust', {'min': 10, 'max': 50})

    # Ensure all regimes have factors
    for regime in WASTE_FACTORS:
        if regime not in waste_factors:
            waste_factors[regime] = WASTE_FACTORS[regime]

    return co2_factors, waste_factors


def estimate_production_from_co2(
    co2_emissions_kg: float,
    technology_regime: str,
    co2_factors: Optional[Dict] = None
) -> Tuple[float, float]:
    """
    Estimate production tonnage from CO2 emissions.

    Uses inverse of BREF CO2 emission factors to back-calculate production.
    Returns (min, max) range to account for factor uncertainty.

    Parameters
    ----------
    co2_emissions_kg : float
        Annual CO2 emissions in kg
    technology_regime : str
        Technology regime ('BF_BOF', 'EAF', 'MIXED', 'UNKNOWN')
    co2_factors : dict, optional
        CO2 factors by regime. If None, uses defaults.

    Returns
    -------
    production_min : float
        Minimum estimated production in tonnes
    production_max : float
        Maximum estimated production in tonnes

    Examples
    --------
    >>> estimate_production_from_co2(2_000_000_000, 'BF_BOF')
    (909091, 1111111)  # About 1 Mt steel
    """
    if co2_factors is None:
        co2_factors = CO2_FACTORS

    if pd.isna(co2_emissions_kg) or co2_emissions_kg <= 0:
        return 0.0, 0.0

    co2_tonnes = co2_emissions_kg / 1000  # Convert to tonnes

    regime = technology_regime if technology_regime in co2_factors else 'UNKNOWN'
    factors = co2_factors[regime]

    # Production = CO2 / emission_factor
    # Min production uses max factor (higher emission = less efficient)
    # Max production uses min factor (lower emission = more efficient)
    production_min = co2_tonnes / factors['max']
    production_max = co2_tonnes / factors['min']

    return production_min, production_max


def estimate_waste_generation(
    production_min_t: float,
    production_max_t: float,
    technology_regime: str,
    waste_factors: Optional[Dict] = None
) -> Dict[str, Tuple[float, float]]:
    """
    Estimate waste generation from production.

    Applies BREF waste generation factors to production estimate.
    Returns (min, max) ranges for each waste type.

    Parameters
    ----------
    production_min_t : float
        Minimum estimated production in tonnes
    production_max_t : float
        Maximum estimated production in tonnes
    technology_regime : str
        Technology regime
    waste_factors : dict, optional
        Waste factors by regime. If None, uses defaults.

    Returns
    -------
    dict
        Waste estimates by type: {waste_type: (min_t, max_t)}

    Examples
    --------
    >>> estimate_waste_generation(900000, 1100000, 'BF_BOF')
    {'slag': (225000, 577500), 'dust': (9000, 71500)}
    """
    if waste_factors is None:
        waste_factors = WASTE_FACTORS

    regime = technology_regime if technology_regime in waste_factors else 'UNKNOWN'
    factors = waste_factors[regime]

    estimates = {}
    for waste_type, wf in factors.items():
        # Waste_min = Production_max * Factor_min (conservative)
        # Waste_max = Production_min * Factor_max (high estimate)
        waste_min = production_max_t * wf['min'] / 1000  # Convert kg/t to t
        waste_max = production_min_t * wf['max'] / 1000

        # Swap if inverted (shouldn't happen but safety check)
        if waste_min > waste_max:
            waste_min, waste_max = waste_max, waste_min

        estimates[waste_type] = (waste_min, waste_max)

    return estimates


def estimate_facility_waste(
    facility_row: pd.Series,
    co2_col: str = 'CO2',
    regime_col: str = 'technology_regime',
    co2_factors: Optional[Dict] = None,
    waste_factors: Optional[Dict] = None
) -> Dict:
    """
    Estimate waste generation for a single facility.

    Combines production estimation and waste calculation.

    Parameters
    ----------
    facility_row : pd.Series
        Facility data with CO2 and regime columns
    co2_col : str
        Column name for CO2 emissions (in kg)
    regime_col : str
        Column name for technology regime
    co2_factors : dict, optional
        CO2 factors
    waste_factors : dict, optional
        Waste factors

    Returns
    -------
    dict
        Waste estimates including production estimates
    """
    co2_kg = facility_row.get(co2_col, 0) or 0
    regime = facility_row.get(regime_col, 'UNKNOWN') or 'UNKNOWN'

    production_min, production_max = estimate_production_from_co2(
        co2_kg, regime, co2_factors
    )

    waste_estimates = estimate_waste_generation(
        production_min, production_max, regime, waste_factors
    )

    result = {
        'estimated_production_min_t': production_min,
        'estimated_production_max_t': production_max,
    }

    for waste_type, (wmin, wmax) in waste_estimates.items():
        result[f'estimated_{waste_type}_min_t'] = wmin
        result[f'estimated_{waste_type}_max_t'] = wmax

    return result


def estimate_facilities_batch(
    facilities_df: pd.DataFrame,
    co2_col: str = 'CO2',
    regime_col: str = 'technology_regime',
    bref_factors_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Estimate waste generation for multiple facilities.

    Parameters
    ----------
    facilities_df : pd.DataFrame
        Facilities with CO2 and regime columns
    co2_col : str
        Column name for CO2 emissions (in kg)
    regime_col : str
        Column name for technology regime
    bref_factors_path : Path, optional
        Path to BREF factors CSV

    Returns
    -------
    pd.DataFrame
        Facilities with estimated production and waste columns
    """
    co2_factors, waste_factors = load_bref_factors(bref_factors_path)

    estimates = []
    for _, row in facilities_df.iterrows():
        est = estimate_facility_waste(
            row,
            co2_col=co2_col,
            regime_col=regime_col,
            co2_factors=co2_factors,
            waste_factors=waste_factors
        )
        est['facility_id'] = row['facility_id']
        estimates.append(est)

    estimates_df = pd.DataFrame(estimates)

    # Merge with original
    result = facilities_df.merge(estimates_df, on='facility_id', how='left')

    return result


def generate_waste_estimates(
    classified_facilities: pd.DataFrame,
    output_path: Optional[Path] = None,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Generate waste estimates for classified facilities.

    Main entry point for waste generation estimation.

    Parameters
    ----------
    classified_facilities : pd.DataFrame
        Facilities with CO2 and technology_regime columns
    output_path : Path, optional
        Save results to CSV
    verbose : bool
        Print summary

    Returns
    -------
    pd.DataFrame
        Facilities with waste estimates

    Examples
    --------
    >>> from src.classification import classify_technology
    >>> from src.allocation.emissions_based_waste_generation import generate_waste_estimates
    >>> classified = classify_technology(facilities)
    >>> with_waste = generate_waste_estimates(classified)
    """
    result = estimate_facilities_batch(classified_facilities)

    if verbose:
        print(f"\nWaste Generation Estimates:")
        print(f"  Facilities: {len(result)}")

        # Summary by regime
        for regime in ['BF_BOF', 'EAF', 'MIXED', 'UNKNOWN']:
            regime_df = result[result['technology_regime'] == regime]
            if len(regime_df) > 0:
                prod_sum = regime_df['estimated_production_min_t'].sum()
                slag_sum = regime_df['estimated_slag_min_t'].sum() if 'estimated_slag_min_t' in regime_df.columns else 0
                dust_sum = regime_df['estimated_dust_min_t'].sum() if 'estimated_dust_min_t' in regime_df.columns else 0
                print(f"\n  {regime} ({len(regime_df)} facilities):")
                print(f"    Est. production: {prod_sum:,.0f} - {regime_df['estimated_production_max_t'].sum():,.0f} t")
                print(f"    Est. slag: {slag_sum:,.0f} t (min)")
                print(f"    Est. dust: {dust_sum:,.0f} t (min)")

    if output_path is not None:
        result.to_csv(output_path, index=False)
        print(f"\nSaved to: {output_path}")

    return result


if __name__ == '__main__':
    # Test with sample data
    test_data = pd.DataFrame([
        {'facility_id': 'F001', 'facility_name': 'Integrated Steel Plant', 'CO2': 2_000_000_000, 'technology_regime': 'BF_BOF'},
        {'facility_id': 'F002', 'facility_name': 'Mini Mill', 'CO2': 150_000_000, 'technology_regime': 'EAF'},
        {'facility_id': 'F003', 'facility_name': 'Unknown Facility', 'CO2': 500_000_000, 'technology_regime': 'UNKNOWN'},
    ])

    result = generate_waste_estimates(test_data, verbose=True)
    print("\nDetailed results:")
    print(result[['facility_name', 'technology_regime',
                  'estimated_production_min_t', 'estimated_production_max_t',
                  'estimated_slag_min_t', 'estimated_slag_max_t']].to_string())
