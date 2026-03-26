#!/usr/bin/env python3
"""
Steel Facility Waste Classification & Allocation Pipeline.

Orchestrates the 3-step pipeline:
1. Load EPRTR data and classify technology regimes (BF_BOF, EAF, MIXED, UNKNOWN)
2. Estimate process waste generation from BREF factors
3. Allocate national waste statistics to individual facilities

Output per facility:
- Facility metadata (name, country, coordinates, EPRTR/IED activity)
- NACE industry codes (nace_primary, nace_all, nace_2digit)
- Technology regime (BF_BOF, EAF, MIXED, UNKNOWN for steel facilities)
- Estimated process waste generation (min/max from BREF)
- Allocated reported waste (from national NACE statistics)

Usage:
    python classify_tech_generate_and_allocate_waste.py
    python classify_tech_generate_and_allocate_waste.py --countries Sweden Norway Finland
    python classify_tech_generate_and_allocate_waste.py --ied 2.2 --no-allocate
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.loaders.io import RAW_DIR, PROCESSED_DIR
from src.classification.emissions_based_technology_classifier import (
    classify_technology,
    TechnologyClassifier,
)
from src.allocation.emissions_based_waste_generation import (
    generate_waste_estimates,
    load_bref_factors,
)
from src.allocation.emissions_based_allocator import (
    EmissionsAllocator,
    load_emissions_allocator,
)
from src.mappings.ied_nace import get_nace_for_ied


def load_eprtr_facilities(
    data_dir: Path, ied_filter: str = None, countries: list = None
) -> pd.DataFrame:
    """
    Load E-PRTR emissions data, optionally filtered by IED activity.

    Parameters
    ----------
    data_dir : Path
        Raw data directory
    ied_filter : str, optional
        IED activity filter (e.g., '2' for metals, '2.2' for iron/steel).
        If None, loads all facilities.
    countries : list, optional
        Countries to filter (full names like 'Sweden', 'Germany')

    Returns
    -------
    pd.DataFrame
        Raw emissions with columns: facility_id, facility_name, country, city,
        lat, lon, eprtr_activity, reporting_year, pollutant, release_kg, medium, ied_code,
        nace_primary, nace_all, nace_2digit
    """
    from src.loaders.eprtr_emissions import (
        load_all_emissions,
        get_ied_from_eprtr_activity,
    )

    print(f"Loading E-PRTR data from {data_dir}...")
    emissions = load_all_emissions(data_dir)

    # Convert EPRTR activity codes like "2(b)" to IED format "2.b"
    emissions["ied_code"] = emissions["eprtr_activity"].apply(
        get_ied_from_eprtr_activity
    )

    # Map IED activity to NACE codes
    def get_primary_nace(ied_code):
        """Get first (most specific) NACE code."""
        if pd.isna(ied_code):
            return None
        nace_list = get_nace_for_ied(ied_code)
        return nace_list[0] if nace_list else None

    def get_all_nace_str(ied_code):
        """Get all NACE codes as comma-separated string."""
        if pd.isna(ied_code):
            return None
        nace_list = get_nace_for_ied(ied_code)
        return ", ".join(nace_list) if nace_list else None

    def get_2digit_nace(ied_code):
        """Get 2-digit NACE section from primary."""
        primary = get_primary_nace(ied_code)
        if primary and len(primary) >= 2:
            code = primary.replace("C", "").strip()
            return code[:2] if len(code) >= 2 else code
        return None

    emissions["nace_primary"] = emissions["ied_code"].apply(get_primary_nace)
    emissions["nace_all"] = emissions["ied_code"].apply(get_all_nace_str)
    emissions["nace_2digit"] = emissions["ied_code"].apply(get_2digit_nace)

    # Filter by IED activity prefix (if specified)
    if ied_filter is not None:
        mask = emissions["ied_code"].str.startswith(ied_filter, na=False)
        emissions_filtered = emissions[mask].copy()
        filter_desc = f"IED {ied_filter}"
    else:
        emissions_filtered = emissions.copy()
        filter_desc = "all IED codes"

    if countries:
        emissions_filtered = emissions_filtered[
            emissions_filtered["country"].isin(countries)
        ]

    print(f"  Filtered to {filter_desc}: {len(emissions_filtered)} emission records")

    if len(emissions_filtered) == 0:
        print(f"  Warning: No facilities found for {filter_desc}")
        print(
            f"  Available IED codes: {sorted(emissions['ied_code'].dropna().unique())[:20]}..."
        )
        return pd.DataFrame(
            columns=[
                "facility_id",
                "facility_name",
                "country",
                "city",
                "lat",
                "lon",
                "eprtr_activity",
                "reporting_year",
                "pollutant",
                "release_kg",
                "medium",
                "ied_code",
                "nace_primary",
                "nace_all",
                "nace_2digit",
            ]
        )

    print(f"  Facilities: {emissions_filtered['facility_id'].nunique()}")
    if len(emissions_filtered) > 0:
        print(f"  Countries: {sorted(emissions_filtered['country'].unique())}")

    return emissions_filtered


def step1_classify_technology(
    emissions: pd.DataFrame, ied_code: str = None
) -> pd.DataFrame:
    """
    Step 1: Classify technology regimes.

    Uses emissions-based classification without capacity estimates.
    Only steel facilities (IED 2.2) are classified; others get NaN regime.

    Parameters
    ----------
    emissions : pd.DataFrame
        Raw emissions data with ied_code column
    ied_code : str, optional
        IED filter used when loading data (for metadata extraction)
    """
    print("\n" + "=" * 60)
    print("STEP 1: TECHNOLOGY CLASSIFICATION")
    print("=" * 60)

    from src.loaders.eprtr_emissions import get_facility_metadata

    # Extract NACE columns per facility (for merging later)
    nace_cols = ["facility_id", "nace_primary", "nace_all", "nace_2digit"]
    if all(col in emissions.columns for col in nace_cols):
        facility_nace = (
            emissions[nace_cols]
            .drop_duplicates(subset=["facility_id"])
            .reset_index(drop=True)
        )
    else:
        facility_nace = None

    # Split into steel (2.2) and non-steel facilities
    steel_mask = emissions["ied_code"].str.startswith("2.2", na=False)
    steel_emissions = emissions[steel_mask]
    non_steel_emissions = emissions[~steel_mask]

    steel_facility_ids = steel_emissions["facility_id"].unique()
    non_steel_facility_ids = non_steel_emissions["facility_id"].unique()

    print(f"  Steel facilities (IED 2.2): {len(steel_facility_ids)}")
    print(f"  Non-steel facilities: {len(non_steel_facility_ids)}")

    results = []

    # Classify steel facilities
    if len(steel_facility_ids) > 0:
        print("\n  Classifying steel facilities...")
        steel_classified = classify_technology(
            steel_emissions,
            ied_code="2.2",
            capacity_col=None,
            use_tensor_fallback=True,
            confidence_threshold=0.5,
            verbose=True,
        )
        steel_metadata = get_facility_metadata(steel_emissions, ied_filter="2.2")
        steel_classified = steel_classified.merge(
            steel_metadata, on="facility_id", how="left"
        )
        # Merge NACE columns
        if facility_nace is not None:
            steel_classified = steel_classified.merge(
                facility_nace, on="facility_id", how="left"
            )
        results.append(steel_classified)

    # Non-steel facilities: no technology classification applicable
    if len(non_steel_facility_ids) > 0:
        print(f"\n  Non-steel facilities: skipping technology classification")
        non_steel_metadata = get_facility_metadata(non_steel_emissions, ied_filter=None)
        non_steel_metadata["technology_regime"] = np.nan
        non_steel_metadata["classification_confidence"] = np.nan
        non_steel_metadata["classification_method"] = "not_applicable"
        # Merge NACE columns
        if facility_nace is not None:
            non_steel_metadata = non_steel_metadata.merge(
                facility_nace, on="facility_id", how="left"
            )
        results.append(non_steel_metadata)

    if results:
        classified = pd.concat(results, ignore_index=True)
    else:
        classified = pd.DataFrame()

    return classified


def step2_estimate_waste_generation(
    classified: pd.DataFrame, emissions: pd.DataFrame
) -> pd.DataFrame:
    """
    Step 2: Estimate waste generation from BREF factors.

    Back-calculates production from CO2 and applies waste factors.
    Only applies to steel facilities (those with technology_regime).

    Parameters
    ----------
    classified : pd.DataFrame
        Classified facilities from step 1
    emissions : pd.DataFrame
        Raw emissions data with pollutant values
    """
    print("\n" + "=" * 60)
    print("STEP 2: WASTE GENERATION ESTIMATION")
    print("=" * 60)

    # Aggregate CO2 by facility
    co2_totals = (
        emissions[emissions["pollutant"] == "Carbon dioxide (CO2)"]
        .groupby("facility_id")["release_kg"]
        .mean()
        .reset_index()
        .rename(columns={"release_kg": "CO2"})
    )

    # Merge CO2 with classified facilities
    classified_with_emissions = classified.merge(
        co2_totals, on="facility_id", how="left"
    )
    classified_with_emissions["CO2"] = classified_with_emissions["CO2"].fillna(0)

    print(f"  Facilities with CO2 data: {(classified_with_emissions['CO2'] > 0).sum()}")

    # Split into steel (has technology_regime) and non-steel
    has_regime = classified_with_emissions["technology_regime"].notna()
    steel_facilities = classified_with_emissions[has_regime].copy()
    non_steel_facilities = classified_with_emissions[~has_regime].copy()

    print(f"  Steel facilities (for BREF estimation): {len(steel_facilities)}")
    print(f"  Non-steel facilities (skip BREF): {len(non_steel_facilities)}")

    results = []

    # Estimate waste for steel facilities using BREF factors
    if len(steel_facilities) > 0:
        steel_with_waste = generate_waste_estimates(steel_facilities, verbose=True)
        results.append(steel_with_waste)

    # Non-steel: add NaN columns for BREF estimates
    if len(non_steel_facilities) > 0:
        bref_columns = [
            "estimated_production_min_t",
            "estimated_production_max_t",
            "estimated_slag_min_t",
            "estimated_slag_max_t",
            "estimated_dust_min_t",
            "estimated_dust_max_t",
        ]
        for col in bref_columns:
            non_steel_facilities[col] = np.nan
        results.append(non_steel_facilities)

    if results:
        with_waste = pd.concat(results, ignore_index=True)
    else:
        with_waste = pd.DataFrame()

    return with_waste


def step3_allocate_national_waste(
    facilities_with_estimates: pd.DataFrame,
    wasgen_path: str = "env_wasgen",
    countries: list = None,
) -> pd.DataFrame:
    """
    Step 3: Allocate national waste statistics to facilities.

    Uses CO2 emissions as allocation key with technology coefficients.
    """
    print("\n" + "=" * 60)
    print("STEP 3: NATIONAL WASTE ALLOCATION")
    print("=" * 60)

    if countries is None:
        countries = facilities_with_estimates["country"].unique().tolist()

    try:
        allocator = load_emissions_allocator(
            countries=countries,
            validate_waste_types=False,  # Until IED-EWC mapping documented
        )
    except Exception as e:
        print(f"  Warning: Could not load allocator: {e}")
        print("  Skipping national waste allocation")
        facilities_with_estimates["allocated_waste_status"] = "not_allocated"
        return facilities_with_estimates

    # Load waste generation data
    from src.loaders.eurostat import load_dataset

    try:
        wasgen, _, _ = load_dataset(wasgen_path, n_datapoints=3)
        print(f"  Loaded waste generation data: {len(wasgen)} records")
    except Exception as e:
        print(f"  Warning: Could not load waste generation: {e}")
        facilities_with_estimates["allocated_waste_status"] = "wasgen_not_found"
        return facilities_with_estimates

    # Run allocation
    allocated = allocator.allocate_waste(wasgen, countries=countries)

    if len(allocated) == 0:
        print("  No allocations made")
        facilities_with_estimates["allocated_waste_status"] = "no_allocations"
        return facilities_with_estimates

    print(
        f"  Allocated {allocated['allocated_tonnes'].sum():,.0f} tonnes to {allocated['facility_id'].nunique()} facilities"
    )

    # Pivot allocations: one column per waste type
    waste_types = sorted(allocated["waste_type"].unique())

    facility_allocations = allocated.pivot_table(
        index="facility_id",
        columns="waste_type",
        values="allocated_tonnes",
        aggfunc="sum",
        fill_value=0.0,
    ).reset_index()

    # Rename columns to be clear they are allocated tonnes
    facility_allocations.columns = ["facility_id"] + [
        f"alloc_{wt}_tonnes" for wt in waste_types
    ]

    # Also store which waste types were allocated (for reference)
    waste_types_per_facility = (
        allocated.groupby("facility_id")["waste_type"]
        .apply(lambda x: ", ".join(sorted(x.unique())))
        .reset_index()
    )
    waste_types_per_facility.columns = ["facility_id", "allocated_waste_types"]

    facility_allocations = facility_allocations.merge(
        waste_types_per_facility, on="facility_id", how="left"
    )

    # Merge with estimates
    result = facilities_with_estimates.merge(
        facility_allocations, on="facility_id", how="left"
    )

    # Fill NaN in allocation columns with 0
    alloc_cols = [
        c for c in result.columns if c.startswith("alloc_") and c.endswith("_tonnes")
    ]
    for col in alloc_cols:
        result[col] = result[col].fillna(0)

    # Count facilities with any allocation
    has_allocation = (
        result[alloc_cols].sum(axis=1) > 0
        if alloc_cols
        else pd.Series([False] * len(result))
    )
    print(f"  Facilities with allocations: {has_allocation.sum()}")

    # Compute recovery maturity indicator
    total_generated = result["estimated_slag_max_t"].fillna(0) + result["estimated_dust_max_t"].fillna(0)
    total_allocated = result[alloc_cols].sum(axis=1) if alloc_cols else 0
    result["recovery_maturity_indicator"] = np.where(
        total_generated > 0,
        total_allocated / total_generated,
        np.nan
    )

    return result


def build_output_schema(result: pd.DataFrame) -> pd.DataFrame:
    """
    Format output to match expected schema.

    Output schema per facility:
    - facility_id, facility_name, country, lat, lon
    - eprtr_activity, ied_code
    - nace_primary, nace_all, nace_2digit
    - technology_regime, classification_confidence, classification_method
    - CO2, CO
    - estimated_production_min_t, estimated_production_max_t
    - estimated_slag_min_t, estimated_slag_max_t
    - estimated_dust_min_t, estimated_dust_max_t
    - alloc_<waste_type>_tonnes (one column per waste type)
    - allocated_waste_types (comma-separated list)
    """
    output_cols = [
        "facility_id",
        "facility_name",
        "country",
        "lat",
        "lon",
        "eprtr_activity",
        "ied_code",
        "nace_primary",
        "nace_all",
        "nace_2digit",
        "technology_regime",
        "classification_confidence",
        "classification_method",
        "CO2",
        "CO",
        "estimated_production_min_t",
        "estimated_production_max_t",
        "estimated_slag_min_t",
        "estimated_slag_max_t",
        "estimated_dust_min_t",
        "estimated_dust_max_t",
    ]

    # Add allocation columns if present (dynamically find alloc_* columns)
    alloc_cols = [
        c for c in result.columns if c.startswith("alloc_") and c.endswith("_tonnes")
    ]
    if alloc_cols:
        output_cols.extend(sorted(alloc_cols))
    if "allocated_waste_types" in result.columns:
        output_cols.append("allocated_waste_types")
    if "recovery_maturity_indicator" in result.columns:
        output_cols.append("recovery_maturity_indicator")

    # Select available columns
    available_cols = [c for c in output_cols if c in result.columns]
    output = result[available_cols].copy()

    return output


def run_pipeline(
    ied_filter: str = None,
    countries: list = None,
    skip_allocation: bool = False,
    output_dir: Path = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Run full pipeline: classify -> estimate -> allocate.

    Parameters
    ----------
    ied_filter : str, optional
        IED activity code (default: None for all facilities)
    countries : list, optional
        Countries to process (default: all)
    skip_allocation : bool
        Skip national waste allocation step
    output_dir : Path, optional
        Output directory (default: data/processed)
    verbose : bool
        Print progress

    Returns
    -------
    pd.DataFrame
        Final output with all estimates and allocations
    """
    if output_dir is None:
        output_dir = PROCESSED_DIR

    print("=" * 60)
    print("FACILITY WASTE CLASSIFICATION & ALLOCATION PIPELINE")
    print("=" * 60)
    print(f"IED Filter: {ied_filter or 'all'}")
    print(f"Countries: {countries or 'all'}")
    print(f"Output: {output_dir}")
    print(f"Skip allocation: {skip_allocation}")

    # Load data
    facilities = load_eprtr_facilities(
        RAW_DIR, ied_filter=ied_filter, countries=countries
    )

    # Step 1: Classify
    classified = step1_classify_technology(facilities, ied_code=ied_filter)

    # Step 2: Estimate waste
    with_estimates = step2_estimate_waste_generation(classified, facilities)

    # Step 3: Allocate (optional)
    if not skip_allocation:
        final = step3_allocate_national_waste(with_estimates, countries=countries)
    else:
        final = with_estimates
        print("\n(Skipping national waste allocation)")

    # Format output
    output = build_output_schema(final)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d")
    ied_suffix = ied_filter.replace(".", "_") if ied_filter else "all"
    output_path = output_dir / f"facility_waste_classified_{ied_suffix}_{timestamp}.csv"
    output.to_csv(output_path, index=False)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Total facilities: {len(output)}")
    print(f"\nRegime distribution:")
    regime_counts = output["technology_regime"].value_counts(dropna=False)
    for regime, count in regime_counts.items():
        pct = 100 * count / len(output)
        regime_label = regime if pd.notna(regime) else "N/A (non-steel)"
        print(f"  {regime_label}: {count} ({pct:.1f}%)")

    if "estimated_production_min_t" in output.columns:
        prod_min = output["estimated_production_min_t"].sum()
        prod_max = output["estimated_production_max_t"].sum()
        print(f"\nTotal estimated production: {prod_min:,.0f} - {prod_max:,.0f} tonnes")

    # Print per-waste-type allocation totals
    alloc_cols = [
        c for c in output.columns if c.startswith("alloc_") and c.endswith("_tonnes")
    ]
    if alloc_cols:
        print(f"\nAllocated waste by type:")
        for col in sorted(alloc_cols):
            total = output[col].sum()
            if total > 0:
                waste_type = col.replace("alloc_", "").replace("_tonnes", "")
                print(f"  {waste_type}: {total:,.0f} tonnes")
        total_alloc = output[alloc_cols].sum().sum()
        print(f"  TOTAL: {total_alloc:,.0f} tonnes")

    print(f"\nSaved to: {output_path}")

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Steel Facility Waste Classification & Allocation Pipeline"
    )
    parser.add_argument(
        "--ied",
        "-i",
        default=None,
        help="IED activity code filter (default: all facilities; use '2.2' for steel only)",
    )
    parser.add_argument(
        "--countries",
        "-c",
        nargs="+",
        default=None,
        help="Countries to process (default: all)",
    )
    parser.add_argument(
        "--no-allocate", action="store_true", help="Skip national waste allocation step"
    )
    parser.add_argument(
        "--output", "-o", type=Path, default=None, help="Output directory"
    )

    args = parser.parse_args()

    result = run_pipeline(
        ied_filter=args.ied,
        countries=args.countries,
        skip_allocation=args.no_allocate,
        output_dir=args.output,
    )

    # Print top facilities
    print("\nTop 10 facilities by estimated production:")
    if "estimated_production_max_t" in result.columns:
        top = result.nlargest(10, "estimated_production_max_t")
        print(
            top[
                [
                    "facility_name",
                    "country",
                    "technology_regime",
                    "estimated_production_max_t",
                ]
            ].to_string(index=False)
        )


if __name__ == "__main__":
    main()
