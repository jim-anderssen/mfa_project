"""
Emissions-Based Facility-Level Waste Allocator.

Allocates nationally-reported waste generation (from env_wasgen) to individual
facilities using E-PRTR pollutant emissions (CO2, NOx, PM10) as allocation proxies,
with sector-specific weights.

Enhanced with waste type validation: facilities only receive waste types that
their IED activity can actually produce, based on IED → EWC-Stat mapping.

Core logic:
    For each (country, NACE, waste_type) in env_wasgen:
        1. Get total national waste = W_national
        2. Find all E-PRTR facilities in country with matching NACE
        3. **NEW: Filter facilities to only those whose IED activity produces this waste_type**
           - Use IED_TO_EWC_STAT mapping from src/mappings/ied_ewc_stat.py
           - Check if waste_type (EWC-Stat code) is in facility's primary or secondary waste list
           - Skip allocation if no facilities can produce this waste type
        4. For each valid facility f:
           - Calculate weighted emission share:
             share_f = (w_CO2 * CO2_f/CO2_total) +
                       (w_NOx * NOx_f/NOx_total) +
                       (w_PM10 * PM10_f/PM10_total)
           - Handle missing pollutants: normalize weights for available data
        5. Allocate: W_facility_f = W_national * share_f
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

from src.mappings.ied_nace import IED_TO_NACE
from src.mappings.ied_ewc_stat import is_waste_valid_for_ied, get_ied_waste_matrix


# NACE code hierarchy for deduplication
# When both parent and child codes exist, remove parent to avoid double-counting
NACE_HIERARCHY = {
    # Section -> Combined groups
    'C': ['C10-C12', 'C13-C15', 'C16', 'C17_C18', 'C19',
          'C20-C22', 'C23', 'C24_C25', 'C26-C30', 'C31-C33'],
    'E': ['E36_E37_E39', 'E38'],

    # Combined groups -> Individual codes
    'C10-C12': ['C10', 'C11', 'C12'],
    'C13-C15': ['C13', 'C14', 'C15'],
    'C17_C18': ['C17', 'C18'],
    'C20-C22': ['C20', 'C21', 'C22'],
    'C24_C25': ['C24', 'C25'],
    'C26-C30': ['C26', 'C27', 'C28', 'C29', 'C30'],
    'C31-C33': ['C31', 'C32', 'C33'],
    'E36_E37_E39': ['E36', 'E37', 'E39'],
}


class EmissionsAllocator:
    """
    Allocator that distributes national waste to facilities based on emissions.

    Enhanced with waste type validation: filters allocations to ensure facilities
    only receive waste types they can actually produce based on their IED activity.

    Parameters
    ----------
    facilities_df : pd.DataFrame
        E-PRTR facility registry with emissions data.
        Required columns: facility_id, facility_name, country_code,
                         lat, lon, ied_activity, CO2, NOX, PM10
    weights_df : pd.DataFrame
        Sector-specific pollutant weights.
        Required columns: nace, co2_weight, nox_weight, pm10_weight
    ied_nace_map : dict, optional
        Mapping from IED activity codes to NACE codes.
        Defaults to IED_TO_NACE from src.mappings.ied_nace
    validate_waste_types : bool, optional
        Whether to validate waste types against IED-EWC mapping.
        Defaults to True. Set to False to use legacy behavior.

    Attributes
    ----------
    facilities : pd.DataFrame
        Facility data with NACE codes added
    weights : pd.DataFrame
        Sector emission weights
    ied_nace_map : dict
        IED to NACE mapping
    waste_matrix : dict
        IED activity to valid waste types mapping
    """

    # Default pollutant weights if sector not in lookup
    DEFAULT_WEIGHTS = {
        'co2_weight': 0.55,
        'nox_weight': 0.30,
        'pm10_weight': 0.15
    }

    def __init__(
        self,
        facilities_df: pd.DataFrame,
        weights_df: Optional[pd.DataFrame] = None,
        ied_nace_map: Optional[Dict] = None,
        validate_waste_types: bool = True
    ):
        self.ied_nace_map = ied_nace_map or IED_TO_NACE
        self.weights = weights_df
        self.validate_waste_types = validate_waste_types
        self._prepare_facilities(facilities_df)
        self._prepare_weights()
        # Load waste type validation matrix
        if self.validate_waste_types:
            self.waste_matrix = get_ied_waste_matrix()

    def _prepare_facilities(self, facilities_df: pd.DataFrame):
        """Add NACE codes to facilities based on IED activity."""
        self.facilities = facilities_df.copy()

        # Map IED activity to primary NACE code
        def get_primary_nace(ied_code):
            """Get first NACE code for an IED activity."""
            if pd.isna(ied_code):
                return None
            mapping = self.ied_nace_map.get(ied_code, {})
            nace_list = mapping.get('nace', [])
            if nace_list:
                # Return first (most specific) NACE code
                return nace_list[0]
            return None

        def get_all_nace(ied_code):
            """Get all NACE codes for an IED activity."""
            if pd.isna(ied_code):
                return []
            mapping = self.ied_nace_map.get(ied_code, {})
            return mapping.get('nace', [])

        self.facilities['nace_primary'] = self.facilities['ied_activity'].apply(get_primary_nace)
        self.facilities['nace_all'] = self.facilities['ied_activity'].apply(get_all_nace)

        # Add aggregated NACE (2-digit level) for matching with wasgen
        self.facilities['nace_2digit'] = self.facilities['nace_primary'].apply(
            lambda x: x[:2] if x else None
        )

    def _prepare_weights(self):
        """Load weights from CSV if not provided."""
        if self.weights is None:
            weights_path = Path('data/processed/lookuptables/sector_emission_weights.csv')
            if weights_path.exists():
                self.weights = pd.read_csv(weights_path)
            else:
                # Create default weights DataFrame
                self.weights = pd.DataFrame([
                    {'nace': 'DEFAULT', **self.DEFAULT_WEIGHTS}
                ])

        # Create lookup dict for fast access
        self.weights_lookup = {}
        for _, row in self.weights.iterrows():
            nace = row['nace']
            self.weights_lookup[nace] = {
                'co2_weight': row['co2_weight'],
                'nox_weight': row['nox_weight'],
                'pm10_weight': row['pm10_weight']
            }

    def _is_valid_waste_for_facility(
        self,
        facility_ied_code: str,
        waste_code: str
    ) -> bool:
        """
        Check if a facility's IED activity can produce a given waste type.

        Uses the IED → EWC-Stat mapping to validate whether a waste type
        is in the primary or secondary waste list for the IED activity.

        Parameters
        ----------
        facility_ied_code : str
            IED Annex I activity code (e.g., '2.2', '3.3')
        waste_code : str
            EWC-Stat waste code (e.g., 'W061', 'W071')

        Returns
        -------
        bool
            True if waste type is valid for this IED activity, False otherwise.

        Examples
        --------
        >>> allocator._is_valid_waste_for_facility('2.2', 'W061')
        True  # ferrous metal waste from steel production
        >>> allocator._is_valid_waste_for_facility('2.2', 'W071')
        False  # glass waste NOT from steel production
        """
        if not self.validate_waste_types:
            return True  # Legacy mode: accept all

        if pd.isna(facility_ied_code):
            return False

        return is_waste_valid_for_ied(facility_ied_code, waste_code)

    def _parse_nace_code(self, nace_code: str) -> List[str]:
        """
        Parse a NACE code that may be a combined/range code.

        Handles formats like:
        - 'C24' -> ['24']
        - 'C24_C25' -> ['24', '25']
        - 'C10-C12' -> ['10', '11', '12']
        - 'C24.10' -> ['24.10']
        - 'B' -> ['05', '06', '07', '08', '09'] (mining)

        Parameters
        ----------
        nace_code : str
            NACE code to parse (may include 'C' prefix)

        Returns
        -------
        list of str
            Individual NACE prefixes to match against
        """
        # Remove 'C' prefix and normalize
        code = nace_code.replace('C', '').strip()

        # Handle underscore-separated codes like '24_25'
        if '_' in code:
            parts = code.split('_')
            return [p.strip() for p in parts]

        # Handle range codes like '10-12'
        if '-' in code and code.count('-') == 1:
            # Could be a range like '10-12' or a detailed code like '24.1-24.3'
            parts = code.split('-')
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                start, end = int(parts[0]), int(parts[1])
                return [str(i) for i in range(start, end + 1)]
            # Otherwise treat as individual parts
            return [p.strip() for p in parts]

        # Handle section codes (single letter)
        section_map = {
            'B': ['05', '06', '07', '08', '09'],  # Mining
            'A': ['01', '02', '03'],  # Agriculture
            # C = Manufacturing covers 10-33
            '': [str(i) for i in range(10, 34)],  # C alone (empty after removing 'C')
            'D': ['35'],  # Electricity, gas
            'E': ['36', '37', '38', '39'],  # Water, waste
            'F': ['41', '42', '43'],  # Construction
        }
        if code in section_map:
            return section_map[code]

        # Single NACE code
        return [code]

    def get_weights_for_nace(self, nace_code: str) -> Dict[str, float]:
        """
        Get pollutant weights for a NACE code.

        Tries exact match first, then prefix match, then defaults.
        """
        if nace_code in self.weights_lookup:
            return self.weights_lookup[nace_code]

        # Try 2-digit prefix (e.g., 'C24' for 'C24.10')
        prefix_2d = nace_code[:3] if len(nace_code) >= 3 else nace_code
        if prefix_2d in self.weights_lookup:
            return self.weights_lookup[prefix_2d]

        # Try just the letter (e.g., 'C' for 'C24')
        prefix_1d = nace_code[0] if nace_code else 'C'
        for nace, weights in self.weights_lookup.items():
            if nace.startswith(prefix_1d):
                return weights

        return self.DEFAULT_WEIGHTS

    def calculate_emission_shares(
        self,
        country: str,
        nace_code: str,
        waste_code: Optional[str] = None
    ) -> Tuple[pd.DataFrame, str]:
        """
        Calculate each facility's share of total emissions for a country/NACE.

        Enhanced with waste type validation: filters to only facilities whose
        IED activity can produce the specified waste type.

        Parameters
        ----------
        country : str
            ISO 2-letter country code
        nace_code : str
            NACE code (can be 2-digit like 'C24' or detailed like '24.10')
        waste_code : str, optional
            EWC-Stat waste code to validate against IED activities.
            If provided and validate_waste_types=True, filters facilities.

        Returns
        -------
        matched_df : pd.DataFrame
            Facilities with calculated emission shares.
            Columns: facility_id, co2_share, nox_share, pm10_share, weighted_share
        filter_status : str
            Status of filtering: 'ok', 'no_nace_match', 'no_waste_match'
        """
        # Handle combined NACE codes like 'C24_C25' or 'C10-C12'
        nace_prefixes = self._parse_nace_code(nace_code)

        # Find facilities matching country and any of the NACE prefixes
        country_mask = self.facilities['country_code'] == country

        def matches_any_nace(row):
            """Check if facility matches any of the NACE prefixes."""
            for prefix in nace_prefixes:
                # Check nace_primary
                if row['nace_primary'] and str(row['nace_primary']).startswith(prefix):
                    return True
                # Check nace_2digit
                if row['nace_2digit'] and str(row['nace_2digit']).startswith(prefix[:2]):
                    return True
                # Check nace_all
                if row['nace_all']:
                    for nace in row['nace_all']:
                        if nace.startswith(prefix):
                            return True
            return False

        matched = self.facilities[country_mask].copy()
        nace_mask = matched.apply(matches_any_nace, axis=1)
        matched = matched[nace_mask].copy()

        if len(matched) == 0:
            return pd.DataFrame(), 'no_nace_match'

        # Apply waste type validation if enabled and waste_code provided
        if self.validate_waste_types and waste_code is not None:
            # Filter to only facilities that can produce this waste type
            valid_mask = matched['ied_activity'].apply(
                lambda ied: self._is_valid_waste_for_facility(ied, waste_code)
            )
            matched = matched[valid_mask].copy()

            if len(matched) == 0:
                return pd.DataFrame(), 'no_waste_match'

        # Calculate totals for normalization
        co2_total = matched['CO2'].sum()
        nox_total = matched['NOX'].sum()
        pm10_total = matched['PM10'].sum()

        # Calculate individual shares
        matched['co2_share'] = matched['CO2'] / co2_total if co2_total > 0 else 0
        matched['nox_share'] = matched['NOX'] / nox_total if nox_total > 0 else 0
        matched['pm10_share'] = matched['PM10'] / pm10_total if pm10_total > 0 else 0

        # Get weights per facility based on their detailed NACE code
        def get_facility_weights(facility_nace):
            """Get weights using facility's detailed NACE code."""
            if pd.isna(facility_nace):
                return self.get_weights_for_nace(nace_code)  # fallback to group
            # Format as NACE code (e.g., '24.10' -> 'C24.10')
            formatted_nace = f'C{facility_nace}' if not str(facility_nace).startswith('C') else str(facility_nace)
            return self.get_weights_for_nace(formatted_nace)

        # Determine which pollutants have data
        has_co2 = co2_total > 0
        has_nox = nox_total > 0
        has_pm10 = pm10_total > 0

        # Calculate weighted share per facility using facility-specific weights
        def calc_weighted_share(row):
            weights = get_facility_weights(row['nace_primary'])
            eff_weights = self._normalize_weights(
                weights,
                has_co2=has_co2,
                has_nox=has_nox,
                has_pm10=has_pm10
            )
            return (
                eff_weights['co2_weight'] * row['co2_share'] +
                eff_weights['nox_weight'] * row['nox_share'] +
                eff_weights['pm10_weight'] * row['pm10_share']
            ), eff_weights

        # Apply per-facility weight calculation
        results = matched.apply(calc_weighted_share, axis=1)
        matched['weighted_share'] = results.apply(lambda x: x[0])

        # Store weights used per facility for transparency
        matched['co2_weight_used'] = results.apply(lambda x: x[1]['co2_weight'])
        matched['nox_weight_used'] = results.apply(lambda x: x[1]['nox_weight'])
        matched['pm10_weight_used'] = results.apply(lambda x: x[1]['pm10_weight'])

        return matched, 'ok'

    def _normalize_weights(
        self,
        weights: Dict[str, float],
        has_co2: bool,
        has_nox: bool,
        has_pm10: bool
    ) -> Dict[str, float]:
        """
        Normalize weights when some pollutants are missing.

        If a pollutant has no data, redistribute its weight proportionally.
        """
        available = {
            'co2_weight': weights['co2_weight'] if has_co2 else 0,
            'nox_weight': weights['nox_weight'] if has_nox else 0,
            'pm10_weight': weights['pm10_weight'] if has_pm10 else 0
        }

        total = sum(available.values())
        if total == 0:
            # No data at all - use equal weights for available
            n_available = sum([has_co2, has_nox, has_pm10])
            if n_available == 0:
                return {'co2_weight': 0, 'nox_weight': 0, 'pm10_weight': 0}
            equal = 1.0 / n_available
            return {
                'co2_weight': equal if has_co2 else 0,
                'nox_weight': equal if has_nox else 0,
                'pm10_weight': equal if has_pm10 else 0
            }

        # Normalize to sum to 1.0
        return {k: v / total for k, v in available.items()}

    def allocate_waste(
        self,
        wasgen_df: pd.DataFrame,
        countries: Optional[List[str]] = None,
        deduplicate_nace: bool = True
    ) -> pd.DataFrame:
        """
        Allocate national waste generation to facilities.

        Enhanced with waste type validation: only allocates waste types to
        facilities whose IED activity can produce that waste type.

        Parameters
        ----------
        wasgen_df : pd.DataFrame
            National waste generation data from env_wasgen.
            Required columns: geo (country code), nace_r2 (NACE code),
                            waste (waste type code), obs_value (tonnes)
        countries : list, optional
            Countries to process. Default: all in wasgen_df.
        deduplicate_nace : bool, optional
            Whether to remove NACE hierarchy overlaps before allocation.
            When True (default), removes aggregate NACE codes when more
            detailed child codes exist, preventing double-counting.

        Returns
        -------
        pd.DataFrame
            Facility-level waste allocations with columns:
            facility_id, facility_name, country, nace, lat, lon,
            waste_type, allocated_tonnes, co2_share, nox_share,
            pm10_share, method

        Notes
        -----
        Unallocated waste is recorded with reason codes:
        - 'no_nace_match': No E-PRTR facilities match the NACE sector
        - 'no_waste_match': Facilities exist but none can produce this waste type
        """
        # Standardize column names first
        wasgen_df = wasgen_df.copy()
        wasgen_df = self._standardize_wasgen_columns(wasgen_df)

        # Apply NACE hierarchy deduplication if enabled
        if deduplicate_nace:
            wasgen_df, dedup_log = self._deduplicate_nace_hierarchy(wasgen_df)
            self._nace_dedup_log = dedup_log
        else:
            self._nace_dedup_log = pd.DataFrame()

        # Then filter by countries
        if countries:
            wasgen_df = wasgen_df[wasgen_df['country'].isin(countries)]

        results = []
        unallocated = []

        # Ensure se_tonnes column exists (may be missing in older data)
        if 'se_tonnes' not in wasgen_df.columns:
            wasgen_df['se_tonnes'] = np.nan

        # Group by country + NACE + waste type
        # For SE: when summing tonnes, combined SE = sqrt(sum of variances)
        def combine_se(se_series):
            """Combine standard errors when summing: SE_combined = sqrt(sum(SE_i^2))"""
            valid_se = se_series.dropna()
            if len(valid_se) == 0:
                return np.nan
            return np.sqrt((valid_se ** 2).sum())

        grouped = wasgen_df.groupby(['country', 'nace', 'waste']).agg({
            'tonnes': 'sum',
            'se_tonnes': combine_se
        }).reset_index()

        for _, row in grouped.iterrows():
            country, nace, waste = row['country'], row['nace'], row['waste']
            national_tonnes = row['tonnes']
            national_se = row['se_tonnes']

            if national_tonnes <= 0:
                continue

            # Get facility shares (with waste type validation)
            shares, filter_status = self.calculate_emission_shares(
                country, nace, waste_code=waste
            )

            if len(shares) == 0:
                # Map filter status to reason code
                reason_map = {
                    'no_nace_match': 'no_eprtr_facilities',
                    'no_waste_match': 'no_valid_producer'
                }
                reason = reason_map.get(filter_status, 'unknown')

                unallocated.append({
                    'country': country,
                    'nace': nace,
                    'waste': waste,
                    'national_tonnes': national_tonnes,
                    'national_se': national_se,
                    'reason': reason
                })
                continue

            # Allocate waste to each facility
            for _, fac in shares.iterrows():
                allocated_tonnes = national_tonnes * fac['weighted_share']
                # SE scales linearly with the allocation share
                allocated_se = national_se * fac['weighted_share'] if pd.notna(national_se) else np.nan

                if allocated_tonnes > 0:
                    results.append({
                        'facility_id': fac['facility_id'],
                        'facility_name': fac.get('facility_name', ''),
                        'country': country,
                        'nace': nace,
                        'ied_activity': fac.get('ied_activity', ''),
                        'lat': fac.get('lat'),
                        'lon': fac.get('lon'),
                        'waste_type': waste,
                        'allocated_tonnes': allocated_tonnes,
                        'allocated_se': allocated_se,
                        'national_tonnes': national_tonnes,
                        'national_se': national_se,
                        'co2_share': fac['co2_share'],
                        'nox_share': fac['nox_share'],
                        'pm10_share': fac['pm10_share'],
                        'weighted_share': fac['weighted_share'],
                        'co2_weight_used': fac['co2_weight_used'],
                        'nox_weight_used': fac['nox_weight_used'],
                        'pm10_weight_used': fac['pm10_weight_used'],
                        'method': 'emissions_weighted_validated'
                    })

        allocated_df = pd.DataFrame(results)
        self.unallocated = pd.DataFrame(unallocated)

        if len(self.unallocated) > 0:
            total_unalloc = self.unallocated['national_tonnes'].sum()
            total_alloc = allocated_df['allocated_tonnes'].sum() if len(allocated_df) > 0 else 0
            pct = 100 * total_unalloc / (total_alloc + total_unalloc) if (total_alloc + total_unalloc) > 0 else 0

            # Count by reason
            reason_counts = self.unallocated.groupby('reason')['national_tonnes'].agg(['count', 'sum'])
            reason_summary = ', '.join([
                f"{r}: {int(row['count'])} streams ({row['sum']:,.0f}t)"
                for r, row in reason_counts.iterrows()
            ])

            warnings.warn(
                f"{len(self.unallocated)} waste streams ({pct:.1f}% of tonnage) "
                f"could not be allocated. Breakdown: {reason_summary}"
            )

        return allocated_df

    def _standardize_wasgen_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize wasgen column names and convert country names to ISO codes."""
        # Common column name mappings
        renames = {
            'geo': 'country',
            'country_code': 'country',
            'nace_r2': 'nace',
            'obs_value': 'tonnes',
            'mean_wasgen': 'tonnes',
            'se_wasgen': 'se_tonnes',
            'waste': 'waste'
        }

        for old, new in renames.items():
            if old in df.columns and new not in df.columns:
                df = df.rename(columns={old: new})

        # Convert country names to ISO codes if needed
        if 'country' in df.columns:
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
                'Serbia': 'RS', 'Albania': 'AL', 'Montenegro': 'ME',
                'North Macedonia': 'MK', 'Bosnia and Herzegovina': 'BA',
                'Kosovo*': 'XK', 'Liechtenstein': 'LI',
            }
            # Only convert if values look like country names (not already ISO codes)
            sample_value = df['country'].dropna().iloc[0] if len(df['country'].dropna()) > 0 else ''
            if len(sample_value) > 2:  # Looks like a country name
                df['country'] = df['country'].map(
                    lambda x: country_name_to_iso.get(x, x) if pd.notna(x) else x
                )

        return df

    def _deduplicate_nace_hierarchy(
        self,
        wasgen_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Remove NACE hierarchy overlaps to prevent double-counting.

        When env_wasgen contains both aggregate NACE codes (e.g., 'C') and
        detailed codes (e.g., 'C24'), remove the aggregate to avoid allocating
        the same waste twice.

        Parameters
        ----------
        wasgen_df : pd.DataFrame
            Waste generation data with 'country', 'nace', 'waste' columns

        Returns
        -------
        cleaned_df : pd.DataFrame
            Deduplicated waste generation data
        dedup_log : pd.DataFrame
            Log of removed rows with columns:
            country, nace_removed, nace_kept, waste, tonnes_removed
        """
        dedup_log = []
        rows_to_remove = []

        # Process each (country, waste) pair
        for (country, waste), group in wasgen_df.groupby(['country', 'waste']):
            nace_codes = set(group['nace'].unique())

            # Check each parent code in hierarchy
            for parent, children in NACE_HIERARCHY.items():
                if parent in nace_codes:
                    # Check if any children also exist
                    children_present = [c for c in children if c in nace_codes]

                    if children_present:
                        # Remove parent row - children are more detailed
                        parent_mask = (
                            (wasgen_df['country'] == country) &
                            (wasgen_df['nace'] == parent) &
                            (wasgen_df['waste'] == waste)
                        )
                        parent_rows = wasgen_df[parent_mask]

                        if len(parent_rows) > 0:
                            rows_to_remove.extend(parent_rows.index.tolist())

                            # Log the removal
                            for _, row in parent_rows.iterrows():
                                dedup_log.append({
                                    'country': country,
                                    'nace_removed': parent,
                                    'nace_kept': ', '.join(children_present),
                                    'waste': waste,
                                    'tonnes_removed': row.get('tonnes', row.get('mean_wasgen', 0))
                                })

        # Remove identified rows
        cleaned_df = wasgen_df.drop(index=rows_to_remove).reset_index(drop=True)
        dedup_log_df = pd.DataFrame(dedup_log)

        if len(dedup_log) > 0:
            total_removed = dedup_log_df['tonnes_removed'].sum()
            warnings.warn(
                f"NACE hierarchy deduplication removed {len(dedup_log)} rows "
                f"({total_removed:,.0f} tonnes) to avoid double-counting"
            )

        return cleaned_df, dedup_log_df

    def get_allocation_summary(self, allocated_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate summary statistics for the allocation.

        Parameters
        ----------
        allocated_df : pd.DataFrame
            Output from allocate_waste()

        Returns
        -------
        pd.DataFrame
            Summary by country and NACE with coverage statistics
        """
        if len(allocated_df) == 0:
            return pd.DataFrame()

        summary = allocated_df.groupby(['country', 'nace']).agg({
            'allocated_tonnes': 'sum',
            'national_tonnes': 'first',  # Same for all facilities in group
            'facility_id': 'nunique',
            'weighted_share': ['mean', 'std']
        }).reset_index()

        # Flatten multi-level columns
        summary.columns = [
            'country', 'nace', 'allocated_tonnes', 'national_tonnes',
            'n_facilities', 'mean_share', 'std_share'
        ]

        # Calculate coverage and breakdown by reason
        if len(self.unallocated) > 0:
            unalloc_by_nace = self.unallocated.groupby(['country', 'nace'])['national_tonnes'].sum()
            summary['unallocated_tonnes'] = summary.apply(
                lambda r: unalloc_by_nace.get((r['country'], r['nace']), 0),
                axis=1
            )

            # Add breakdown by reason
            for reason in ['no_eprtr_facilities', 'no_valid_producer']:
                reason_mask = self.unallocated['reason'] == reason
                reason_unalloc = self.unallocated[reason_mask].groupby(
                    ['country', 'nace']
                )['national_tonnes'].sum()
                summary[f'unalloc_{reason}'] = summary.apply(
                    lambda r: reason_unalloc.get((r['country'], r['nace']), 0),
                    axis=1
                )
        else:
            summary['unallocated_tonnes'] = 0
            summary['unalloc_no_eprtr_facilities'] = 0
            summary['unalloc_no_valid_producer'] = 0

        summary['coverage_pct'] = 100 * summary['allocated_tonnes'] / (
            summary['allocated_tonnes'] + summary['unallocated_tonnes']
        )

        return summary.sort_values('allocated_tonnes', ascending=False)


def _get_project_root() -> Path:
    """Find project root by looking for pyproject.toml or data/ directory."""
    # Start from this file's location
    current = Path(__file__).resolve().parent

    # Walk up until we find project markers
    for _ in range(5):  # Max 5 levels up
        if (current / 'pyproject.toml').exists() or (current / 'data').is_dir():
            return current
        current = current.parent

    # Fallback to current working directory
    return Path.cwd()


def load_emissions_allocator(
    data_dir: Optional[Path] = None,
    countries: Optional[List[str]] = None,
    validate_waste_types: bool = True
) -> EmissionsAllocator:
    """
    Factory function to create an EmissionsAllocator with loaded data.

    Parameters
    ----------
    data_dir : Path, optional
        Data directory. Default: auto-detected project root + 'data/raw'
    countries : list, optional
        Countries to load. Default: Nordic countries.
    validate_waste_types : bool, optional
        Whether to validate waste types against IED-EWC mapping.
        Defaults to True. Set to False for legacy behavior.

    Returns
    -------
    EmissionsAllocator
        Initialized allocator ready for use
    """
    from src.loaders.eprtr import get_facility_emissions_summary

    project_root = _get_project_root()

    if data_dir is None:
        data_dir = project_root / 'data' / 'raw'

    if countries is None:
        countries = ['SE', 'NO', 'FI', 'DK']

    # Load facility emissions data
    facilities = get_facility_emissions_summary(data_dir, countries)

    # Load weights
    weights_path = project_root / 'data' / 'processed' / 'lookuptables' / 'sector_emission_weights.csv'
    weights = pd.read_csv(weights_path) if weights_path.exists() else None

    return EmissionsAllocator(
        facilities, weights, validate_waste_types=validate_waste_types
    )


def run_allocation_pipeline(
    wasgen_path: str,
    output_dir: str,
    countries: Optional[List[str]] = None,
    validate_waste_types: bool = True,
    deduplicate_nace: bool = True,
    n_datapoints: int = 3
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run the complete allocation pipeline.

    Parameters
    ----------
    wasgen_path : str
        Path to waste generation data (env_wasgen)
    output_dir : str
        Directory for output files
    countries : list, optional
        Countries to process
    validate_waste_types : bool, optional
        Whether to validate waste types against IED-EWC mapping.
        Defaults to True. Set to False for legacy behavior.
    deduplicate_nace : bool, optional
        Whether to remove NACE hierarchy overlaps before allocation.
        Defaults to True. Prevents double-counting from aggregate codes.
    n_datapoints : int, optional
        Number of most recent data points to use for waste statistics.
        Default: 3 (bi-annual data = 6 years)

    Returns
    -------
    allocated_df : pd.DataFrame
        Facility-level allocations
    summary_df : pd.DataFrame
        Allocation coverage summary
    """
    from src.loaders.eurostat import load_dataset

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load waste generation data
    if wasgen_path.endswith('.csv'):
        wasgen = pd.read_csv(wasgen_path)
    else:
        wasgen, _, _ = load_dataset(wasgen_path, n_datapoints=n_datapoints)

    # Create allocator with waste type validation
    allocator = load_emissions_allocator(
        countries=countries,
        validate_waste_types=validate_waste_types
    )

    # Run allocation with NACE deduplication
    allocated = allocator.allocate_waste(
        wasgen, countries, deduplicate_nace=deduplicate_nace
    )

    # Generate summary
    summary = allocator.get_allocation_summary(allocated)

    # Save outputs
    allocated.to_csv(output_dir / 'facility_waste_allocated.csv', index=False)
    summary.to_csv(output_dir / 'allocation_coverage_summary.csv', index=False)

    if len(allocator.unallocated) > 0:
        allocator.unallocated.to_csv(
            output_dir / 'unallocated_waste.csv', index=False
        )

    # Save NACE deduplication log if any rows were removed
    if hasattr(allocator, '_nace_dedup_log') and len(allocator._nace_dedup_log) > 0:
        allocator._nace_dedup_log.to_csv(
            output_dir / 'nace_dedup_log.csv', index=False
        )

    print(f"Allocation complete:")
    print(f"  - {len(allocated)} facility allocations")
    print(f"  - {allocated['allocated_tonnes'].sum():,.0f} tonnes allocated")
    print(f"  - {allocated['facility_id'].nunique()} unique facilities")
    if validate_waste_types:
        print(f"  - Waste type validation: ENABLED")
    if deduplicate_nace:
        print(f"  - NACE hierarchy deduplication: ENABLED")
        if hasattr(allocator, '_nace_dedup_log') and len(allocator._nace_dedup_log) > 0:
            print(f"    Removed {len(allocator._nace_dedup_log)} duplicate NACE rows")
    print(f"  - Data points used: {n_datapoints} most recent")
    print(f"  - Outputs saved to {output_dir}")

    # Print unallocated breakdown
    if len(allocator.unallocated) > 0:
        print(f"\nUnallocated waste breakdown:")
        for reason, group in allocator.unallocated.groupby('reason'):
            pct = 100 * group['national_tonnes'].sum() / wasgen['tonnes'].sum() if 'tonnes' in wasgen.columns else 0
            print(f"  - {reason}: {len(group)} streams, {group['national_tonnes'].sum():,.0f}t")

    return allocated, summary


if __name__ == '__main__':
    # Example usage
    allocated, summary = run_allocation_pipeline(
        wasgen_path='env_wasgen',
        output_dir='data/processed',
        countries=['SE', 'NO', 'FI', 'DK']
    )

    print("\nTop 10 allocations by tonnage:")
    print(allocated.nlargest(10, 'allocated_tonnes')[
        ['facility_name', 'country', 'nace', 'waste_type', 'allocated_tonnes']
    ])

    print("\nAllocation summary:")
    print(summary.head(10))
