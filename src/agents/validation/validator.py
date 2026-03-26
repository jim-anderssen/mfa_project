"""
Validation module for extracted waste data.

Validates extracted data against:
- Schema requirements
- Reference Eurostat data
- Plausibility checks
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import pandas as pd

from src.nuts2.data_loader import COUNTRY_MAP, load_waste_generation, EXCLUDE_WASTES
from src.mappings.ewc_stat import EWC_STAT_CODES


@dataclass
class ValidationResult:
    """Result of validating an extracted record."""
    is_valid: bool
    confidence: float
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class WasteDataValidator:
    """
    Validates extracted waste data against reference datasets and business rules.
    """

    def __init__(self, load_reference: bool = True):
        """
        Initialize validator.

        Parameters
        ----------
        load_reference : bool
            If True, load Eurostat reference data for plausibility checks
        """
        self._reference_data = None
        self._valid_waste_codes = set(EWC_STAT_CODES.keys())
        self._valid_countries = set(COUNTRY_MAP.keys())
        self._valid_country_codes = set(COUNTRY_MAP.values())

        if load_reference:
            try:
                self._reference_data = load_waste_generation()
                # Add waste codes from reference data
                self._valid_waste_codes.update(self._reference_data['waste'].unique())
            except Exception:
                # Reference data not available - continue with basic validation
                pass

    def validate_record(self, record: Dict[str, Any]) -> ValidationResult:
        """
        Validate a single extracted record.

        Parameters
        ----------
        record : dict
            Extracted waste data record

        Returns
        -------
        ValidationResult
            Validation outcome
        """
        issues = []
        warnings = []
        confidence = record.get('confidence_score', 0.5)

        # Schema validation - required fields
        required_fields = {
            'waste': 'EWC-Stat waste code',
            'waste_tonnes': 'Waste amount in tonnes',
            'year': 'Reporting year',
            'source_company': 'Company name'
        }

        for field_name, description in required_fields.items():
            if field_name not in record or record[field_name] is None:
                issues.append(f"Missing required field: {field_name} ({description})")
            elif field_name == 'waste_tonnes' and not isinstance(record[field_name], (int, float)):
                issues.append(f"Invalid type for {field_name}: expected number")

        # Value validation
        if 'waste_tonnes' in record and record['waste_tonnes'] is not None:
            tonnes = record['waste_tonnes']
            if tonnes < 0:
                issues.append("Negative waste amount is invalid")
            elif tonnes == 0:
                warnings.append("Zero waste amount - verify if intentional")
            elif tonnes > 100_000_000:
                warnings.append("Extremely high waste amount (>100M tonnes) - requires verification")
                confidence -= 0.2
            elif tonnes > 10_000_000:
                warnings.append("High waste amount (>10M tonnes) - verify for large facility")
                confidence -= 0.1

        # Waste code validation
        if 'waste' in record and record['waste']:
            waste_code = record['waste']
            if waste_code in EXCLUDE_WASTES:
                warnings.append(f"Waste code {waste_code} is a total/aggregate - prefer specific codes")
            elif waste_code not in self._valid_waste_codes:
                warnings.append(f"Unknown EWC-Stat code: {waste_code}")
                confidence -= 0.1

        # Year validation
        if 'year' in record and record['year']:
            year = record['year']
            if isinstance(year, (int, float)):
                if year < 2010:
                    warnings.append(f"Old reporting year ({year}) - data may be outdated")
                elif year > 2025:
                    issues.append(f"Invalid future year: {year}")
                elif year < 2020:
                    confidence -= 0.05  # Slight penalty for older data

        # Country validation
        if 'country' in record and record['country']:
            country = record['country']
            if country not in self._valid_countries:
                # Check if it's a country code
                if country.upper() not in self._valid_country_codes:
                    warnings.append(f"Unknown country: {country}")

        # NUTS2 validation (if present)
        if 'nuts2_region' in record and record['nuts2_region'] and pd.notna(record['nuts2_region']):
            nuts2 = str(record['nuts2_region'])
            if len(nuts2) != 4:
                warnings.append(f"Invalid NUTS2 code format: {nuts2} (should be 4 characters)")
            elif nuts2[:2].upper() not in self._valid_country_codes:
                warnings.append(f"Unknown country prefix in NUTS2 code: {nuts2[:2]}")

        # Plausibility check against reference data
        if self._reference_data is not None and len(issues) == 0:
            plausibility = self._check_plausibility(record)
            warnings.extend(plausibility['warnings'])
            confidence += plausibility['confidence_adjustment']

        # Calculate final confidence
        final_confidence = max(0, min(1, confidence - 0.05 * len(warnings) - 0.2 * len(issues)))

        return ValidationResult(
            is_valid=len(issues) == 0,
            confidence=final_confidence,
            issues=issues,
            warnings=warnings
        )

    def _check_plausibility(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if extracted values are plausible against reference data.
        """
        warnings = []
        confidence_adj = 0.0

        waste_code = record.get('waste')
        country = record.get('country')
        country_code = record.get('country_code') or COUNTRY_MAP.get(country)
        nace = record.get('nace_r2')
        tonnes = record.get('waste_tonnes')

        if not all([waste_code, country_code, tonnes]):
            return {'warnings': warnings, 'confidence_adjustment': confidence_adj}

        # Find similar records in reference data
        mask = (self._reference_data['waste'] == waste_code)
        if country_code:
            mask &= (self._reference_data['country_code'] == country_code)
        if nace:
            mask &= (self._reference_data['nace_r2'] == nace)

        ref_subset = self._reference_data[mask]

        if len(ref_subset) > 0:
            ref_mean = ref_subset['mean_wasgen'].mean()
            ref_std = ref_subset['mean_wasgen'].std() if len(ref_subset) > 1 else ref_mean * 0.5

            # Check if value is within reasonable range (3 standard deviations)
            if ref_std > 0:
                z_score = abs(tonnes - ref_mean) / ref_std
                if z_score > 5:
                    warnings.append(
                        f"Value {tonnes:,.0f}t differs significantly from reference "
                        f"(mean: {ref_mean:,.0f}t, z-score: {z_score:.1f})"
                    )
                    confidence_adj -= 0.15
                elif z_score > 3:
                    warnings.append(
                        f"Value {tonnes:,.0f}t is outside typical range "
                        f"(reference mean: {ref_mean:,.0f}t)"
                    )
                    confidence_adj -= 0.05
                else:
                    # Value is plausible - slight confidence boost
                    confidence_adj += 0.05
        else:
            # No reference data for comparison
            warnings.append("No reference data available for plausibility check")

        return {'warnings': warnings, 'confidence_adjustment': confidence_adj}

    def validate_batch(
        self,
        df: pd.DataFrame,
        min_confidence: float = 0.6
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Validate a batch of extracted records.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame with extracted records
        min_confidence : float
            Minimum confidence threshold for valid records

        Returns
        -------
        tuple
            (valid_records_df, invalid_records_df)
        """
        valid_records = []
        invalid_records = []

        for idx, row in df.iterrows():
            record = row.to_dict()
            result = self.validate_record(record)

            # Add validation results to record
            record['validation_issues'] = '; '.join(result.issues) if result.issues else None
            record['validation_warnings'] = '; '.join(result.warnings) if result.warnings else None
            record['validated_confidence'] = result.confidence

            if result.is_valid and result.confidence >= min_confidence:
                valid_records.append(record)
            else:
                invalid_records.append(record)

        valid_df = pd.DataFrame(valid_records) if valid_records else pd.DataFrame()
        invalid_df = pd.DataFrame(invalid_records) if invalid_records else pd.DataFrame()

        return valid_df, invalid_df

    def get_validation_summary(
        self,
        valid_df: pd.DataFrame,
        invalid_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Generate summary statistics for validation results.
        """
        total = len(valid_df) + len(invalid_df)

        summary = {
            'total_records': total,
            'valid_records': len(valid_df),
            'invalid_records': len(invalid_df),
            'validation_rate': len(valid_df) / total if total > 0 else 0,
        }

        if len(valid_df) > 0:
            summary['valid_confidence_mean'] = valid_df['validated_confidence'].mean()
            summary['valid_confidence_min'] = valid_df['validated_confidence'].min()

        if len(invalid_df) > 0:
            # Count common issues
            all_issues = []
            for issues in invalid_df['validation_issues'].dropna():
                all_issues.extend(issues.split('; '))

            issue_counts = pd.Series(all_issues).value_counts()
            summary['common_issues'] = issue_counts.head(5).to_dict()

        return summary
