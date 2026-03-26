"""
Hybrid Technology Classifier.

Combines rules-based classification (primary) with tensor decomposition (fallback)
to classify facilities into technology regimes based on emission profiles.

Strategy:
1. Primary: Rules-based using CO/CO2 intensity thresholds (fast, interpretable)
2. Fallback: Tensor decomposition for facilities below confidence threshold
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

from .rules_based_technology_classifier import (
    classify_regime_from_emissions,
    load_process_emissions_thresholds,
    get_thresholds_for_ied,
)


class TechnologyClassifier:
    """
    Hybrid classifier for technology regime identification.

    Uses rules-based classification as primary method, falling back to
    tensor decomposition for low-confidence cases.

    Parameters
    ----------
    ied_code : str
        IED activity code (e.g., '2.b' for iron/steel)
    confidence_threshold : float
        Minimum confidence for rules-based classification (default 0.5)
    use_tensor_fallback : bool
        Whether to use tensor decomposition for low-confidence cases
    tensor_rank : int
        Number of factors for tensor decomposition
    """

    def __init__(
        self,
        ied_code: str = "2.b",
        confidence_threshold: float = 0.3,
        use_tensor_fallback: bool = True,
        tensor_rank: int = 3,
        process_emissions_path: Optional[Path] = None,
    ):
        self.ied_code = ied_code
        self.confidence_threshold = confidence_threshold
        self.use_tensor_fallback = use_tensor_fallback
        self.tensor_rank = tensor_rank

        # Load thresholds from BREF data
        self.thresholds = load_process_emissions_thresholds(process_emissions_path)

        # Cached tensor model
        self._tensor_assignments = None
        self._factor_to_regime = None

    def classify_facility(
        self,
        facility_id: str,
        emissions_dict: Dict[str, float],
        capacity_tonnes: Optional[float] = None,
    ) -> Dict:
        """
        Classify a single facility using all available emissions data.

        Parameters
        ----------
        facility_id : str
            Facility identifier
        emissions_dict : dict
            Pollutant name -> emissions in kg (e.g., {'CO2': 2e9, 'CO': 3e7, 'Zn': 15000})
        capacity_tonnes : float, optional
            Production capacity in tonnes/year (enables intensity matching)

        Returns
        -------
        dict
            Classification result with keys:
            - technology_regime: str
            - classification_confidence: float
            - classification_method: str
        """
        # Try rules-based first (now uses all pollutants)
        regime, confidence = classify_regime_from_emissions(
            emissions_dict,
            capacity_tonnes=capacity_tonnes,
            thresholds=self.thresholds,
            use_ratios=True,
        )

        if regime != "UNKNOWN" and confidence >= self.confidence_threshold:
            method = "intensity" if capacity_tonnes else "ratio"
            return {
                "facility_id": facility_id,
                "technology_regime": regime,
                "classification_confidence": confidence,
                "classification_method": method,
            }

        # Fallback to tensor if enabled and model available
        if self.use_tensor_fallback and self._tensor_assignments is not None:
            tensor_result = self._get_tensor_classification(facility_id)
            if tensor_result is not None:
                return tensor_result

        # Return UNKNOWN if no classification possible
        return {
            "facility_id": facility_id,
            "technology_regime": "UNKNOWN",
            "classification_confidence": 0.0,
            "classification_method": "none",
        }

    def _get_tensor_classification(self, facility_id: str) -> Optional[Dict]:
        """Get classification from pre-computed tensor decomposition."""
        if self._tensor_assignments is None:
            return None

        row = self._tensor_assignments[
            self._tensor_assignments["facility_id"] == facility_id
        ]
        if len(row) == 0:
            return None

        row = row.iloc[0]
        factor_id = row["technology_regime"]

        # Map factor to named regime
        regime = (
            self._factor_to_regime.get(factor_id, "UNKNOWN")
            if self._factor_to_regime
            else f"FACTOR_{factor_id}"
        )

        return {
            "facility_id": facility_id,
            "technology_regime": regime,
            "classification_confidence": row.get("assignment_confidence", 0.5),
            "classification_method": "tensor",
        }

    def fit_tensor_model(
        self,
        emissions_df: pd.DataFrame,
        regime_signatures: Optional[Dict[str, List[str]]] = None,
    ):
        """
        Fit tensor decomposition model on emissions data.

        Parameters
        ----------
        emissions_df : pd.DataFrame
            Emissions data from load_all_emissions()
        regime_signatures : dict, optional
            Pollutant signatures for regime mapping
        """
        from .tensor_technology_classifier import (
            identify_technologies,
            map_factors_to_regimes,
        )

        assignments, interpretations = identify_technologies(
            emissions_df, ied_filter=self.ied_code, rank=self.tensor_rank, verbose=False
        )

        self._tensor_assignments = assignments
        self._factor_to_regime = map_factors_to_regimes(
            interpretations, regime_signatures
        )

    def classify_batch(
        self,
        emissions_df: pd.DataFrame,
        capacity_df: Optional[pd.DataFrame] = None,
        capacity_col: str = "capacity_tonnes",
    ) -> pd.DataFrame:
        """
        Classify multiple facilities using all available emissions data.

        Parameters
        ----------
        emissions_df : pd.DataFrame
            Emissions from E-PRTR with columns: facility_id, pollutant, release_kg
        capacity_df : pd.DataFrame, optional
            Capacity data with columns: facility_id, capacity_tonnes
        capacity_col : str
            Column name for capacity in capacity_df

        Returns
        -------
        pd.DataFrame
            Facilities with classification results
        """
        # Fit tensor model if tensor fallback enabled
        if self.use_tensor_fallback:
            try:
                self.fit_tensor_model(emissions_df)
            except Exception as e:
                print(f"Warning: Tensor fallback disabled due to error: {e}")
                self.use_tensor_fallback = False

        # Build capacity lookup
        capacity_lookup = {}
        if capacity_df is not None:
            capacity_lookup = dict(
                zip(capacity_df["facility_id"], capacity_df[capacity_col])
            )

        # Aggregate emissions by facility and pollutant
        print(emissions_df.columns)
        emissions_by_facility = (
            emissions_df.groupby(["facility_id", "pollutant"])["release_kg"]
            .sum()
            .reset_index()
        )

        results = []
        for facility_id in emissions_by_facility["facility_id"].unique():
            fac_emissions = emissions_by_facility[
                emissions_by_facility["facility_id"] == facility_id
            ]

            # Build emissions dict for this facility
            emissions_dict = dict(
                zip(fac_emissions["pollutant"], fac_emissions["release_kg"])
            )

            # Get capacity if available
            capacity = capacity_lookup.get(facility_id, None)

            # Classify
            result = self.classify_facility(
                facility_id=facility_id,
                emissions_dict=emissions_dict,
                capacity_tonnes=capacity,
            )
            results.append(result)

        return pd.DataFrame(results)


def classify_technology(
    emissions_df: pd.DataFrame,
    capacity_df: Optional[pd.DataFrame] = None,
    ied_code: str = "2.b",
    capacity_col: str = "capacity_tonnes",
    use_tensor_fallback: bool = False,
    confidence_threshold: float = 0.3,
    process_emissions_path: Optional[Path] = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Classify technology regimes for facilities using all available emissions.

    Convenience function wrapping TechnologyClassifier.

    Parameters
    ----------
    emissions_df : pd.DataFrame
        Emissions from E-PRTR with columns: facility_id, pollutant, release_kg
    capacity_df : pd.DataFrame, optional
        Capacity data with columns: facility_id, capacity_tonnes
    ied_code : str
        IED activity code
    capacity_col : str
        Column name for production capacity in capacity_df
    use_tensor_fallback : bool
        Enable tensor decomposition for low-confidence cases
    confidence_threshold : float
        Minimum confidence for classification (default 0.3)
    process_emissions_path : Path, optional
        Path to process_emissions.csv (uses default if None)
    verbose : bool
        Print classification summary

    Returns
    -------
    pd.DataFrame
        Facilities with technology_regime, classification_confidence, classification_method

    Examples
    --------
    >>> from src.loaders.eprtr_emissions import load_all_emissions
    >>> emissions = load_all_emissions(data_dir, countries=['SE', 'FI'])
    >>> classified = classify_technology(emissions, ied_code='2.b')
    >>> classified.groupby('technology_regime').size()
    """
    classifier = TechnologyClassifier(
        ied_code=ied_code,
        confidence_threshold=confidence_threshold,
        use_tensor_fallback=use_tensor_fallback,
        process_emissions_path=process_emissions_path,
    )

    result = classifier.classify_batch(
        emissions_df, capacity_df=capacity_df, capacity_col=capacity_col
    )

    if verbose:
        print(f"\nTechnology Classification Results (IED {ied_code}):")
        print(f"  Total facilities: {len(result)}")
        regime_counts = result["technology_regime"].value_counts()
        for regime, count in regime_counts.items():
            pct = 100 * count / len(result)
            print(f"  {regime}: {count} ({pct:.1f}%)")

        method_counts = result["classification_method"].value_counts()
        print(f"\n  Classification methods:")
        for method, count in method_counts.items():
            print(f"    {method}: {count}")

        if "n_pollutants" in result.columns:
            print(
                f"\n  Average pollutants per facility: {result['n_pollutants'].mean():.1f}"
            )

    return result


def load_and_classify(
    data_dir: Optional[Path] = None,
    countries: Optional[List[str]] = None,
    ied_filter: str = "2.b",
    capacity_df: Optional[pd.DataFrame] = None,
    save_output: bool = True,
) -> pd.DataFrame:
    """
    Load EPRTR data and classify technology regimes using all pollutants.

    Parameters
    ----------
    data_dir : Path, optional
        Data directory
    countries : list, optional
        Countries to include (full names like 'Sweden', 'Germany')
    ied_filter : str
        IED activity filter (e.g., '2.b' for iron/steel)
    capacity_df : pd.DataFrame, optional
        Capacity data with columns: facility_id, capacity_tonnes
    save_output : bool
        Save results to CSV

    Returns
    -------
    pd.DataFrame
        Classified facilities with metadata
    """
    from src.loaders.eprtr_emissions import (
        load_all_emissions,
        get_ied_from_eprtr_activity,
        get_facility_metadata,
    )
    from src.loaders.io import RAW_DIR, PROCESSED_DIR

    if data_dir is None:
        data_dir = RAW_DIR

    print(f"Loading emissions data from {data_dir}...")
    emissions = load_all_emissions(data_dir)

    # Convert EPRTR activity codes like "2(b)" to IED format "2.b"
    emissions["ied_code"] = emissions["eprtr_activity"].apply(
        get_ied_from_eprtr_activity
    )

    # Filter to IED activity
    mask = emissions["ied_code"].str.startswith(ied_filter, na=False)
    emissions_filtered = emissions[mask].copy()

    if countries:
        emissions_filtered = emissions_filtered[
            emissions_filtered["country"].isin(countries)
        ]

    if len(emissions_filtered) == 0:
        print(f"Warning: No facilities found for IED {ied_filter}")
        return pd.DataFrame()

    print(
        f"Found {emissions_filtered['facility_id'].nunique()} facilities with {len(emissions_filtered)} emission records"
    )

    # Classify using all emissions
    result = classify_technology(
        emissions_filtered,
        capacity_df=capacity_df,
        ied_code=ied_filter,
        use_tensor_fallback=True,
        verbose=True,
    )

    # Add facility metadata
    metadata = get_facility_metadata(emissions_filtered, ied_filter=ied_filter)
    result = result.merge(metadata, on="facility_id", how="left")

    if save_output:
        output_path = (
            PROCESSED_DIR
            / f"technology_classification_{ied_filter.replace('.', '_')}.csv"
        )
        result.to_csv(output_path, index=False)
        print(f"\nSaved to: {output_path}")

    return result


if __name__ == "__main__":
    result = load_and_classify(ied_filter="2.b", save_output=True)
    if len(result) > 0:
        print(f"\n=== Classification Summary ===")
        print(f"\nMethod breakdown:")
        print(result["classification_method"].value_counts())

        print(f"\nConfidence distribution:")
        print(result["classification_confidence"].describe())

        print(f"\nTop 10 facilities by classification:")
        # Show a sample of results
        display_cols = [
            "facility_name",
            "country",
            "technology_regime",
            "classification_confidence",
            "classification_method",
        ]
        print(result[display_cols].head(10))
