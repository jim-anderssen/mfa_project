"""
validation_correlation.py

Functions for correlating company-reported waste data from sustainability reports
with facility-level allocated waste data from the IED/E-PRTR database.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Facility ID patterns for matching companies to allocated data
COMPANY_FACILITY_PATTERNS = {
    'SSAB': ['SSAB'],
    'Outokumpu': ['Outokumpu', 'OUTOKUMPU'],
    'Boliden': ['Boliden'],
    'Stena': ['Stena'],
}

# IED activity codes for steel and metals
STEEL_METAL_ACTIVITIES = ['2.2', '2.3', '2.5(a)', '2.5(b)', '2.6']


def load_facility_allocated(filepath: str = 'data/processed/facility_waste_allocated.csv') -> pd.DataFrame:
    """Load facility waste allocation data."""
    return pd.read_csv(filepath)


def load_validated_waste(filepath: str = 'data/processed/validated_company_waste.csv') -> pd.DataFrame:
    """Load company-reported validation data from sustainability reports."""
    return pd.read_csv(filepath)


def aggregate_facility_waste_by_company(
    facility_df: pd.DataFrame,
    company_patterns: Dict[str, List[str]] = COMPANY_FACILITY_PATTERNS
) -> pd.DataFrame:
    """
    Aggregate total allocated waste per company based on facility name patterns.

    Parameters
    ----------
    facility_df : pd.DataFrame
        Facility waste allocated data
    company_patterns : dict
        Mapping of company names to facility name search patterns

    Returns
    -------
    pd.DataFrame
        Aggregated waste by company with facility details
    """
    results = []

    for company, patterns in company_patterns.items():
        pattern = '|'.join(patterns)
        mask = facility_df['facility_name'].str.contains(pattern, case=False, na=False)
        company_data = facility_df[mask].copy()

        if len(company_data) > 0:
            # Aggregate by facility
            by_facility = company_data.groupby(
                ['facility_id', 'facility_name', 'country', 'ied_activity']
            ).agg({
                'allocated_tonnes': 'sum',
                'national_tonnes': 'sum',
                'waste_type': lambda x: ', '.join(sorted(set(x)))
            }).reset_index()

            by_facility['company'] = company
            results.append(by_facility)

    if results:
        return pd.concat(results, ignore_index=True)
    return pd.DataFrame()


def calculate_correlation_metrics(
    allocated_df: pd.DataFrame,
    validated_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate correlation metrics between allocated and reported waste.

    Parameters
    ----------
    allocated_df : pd.DataFrame
        Aggregated facility allocation data (from aggregate_facility_waste_by_company)
    validated_df : pd.DataFrame
        Company-reported validation data

    Returns
    -------
    pd.DataFrame
        Correlation report with ratios and flags
    """
    # Summarize allocated data by company
    allocated_summary = allocated_df.groupby('company').agg({
        'allocated_tonnes': 'sum',
        'facility_id': 'count',
        'country': lambda x: ', '.join(sorted(set(x)))
    }).reset_index()
    allocated_summary.columns = ['company', 'allocated_tonnes', 'n_facilities', 'countries']

    # Summarize validated data by company (total waste only)
    validated_total = validated_df[
        validated_df['waste_type'].isin(['total', 'hazardous', 'non_hazardous'])
    ].copy()

    validated_summary = validated_total.groupby('company_name').agg({
        'reported_tonnes': 'sum',
        'report_year': 'first',
        'source_url': 'first'
    }).reset_index()
    validated_summary.columns = ['company', 'reported_tonnes', 'report_year', 'source_url']

    # Merge allocated and validated
    correlation = pd.merge(
        allocated_summary,
        validated_summary,
        on='company',
        how='outer'
    )

    # Calculate metrics
    correlation['ratio'] = correlation['allocated_tonnes'] / correlation['reported_tonnes']
    correlation['coverage_pct'] = (
        correlation['allocated_tonnes'] / correlation['reported_tonnes'] * 100
    ).round(1)

    # Flag outliers (>2x or <0.5x deviation)
    correlation['flag'] = 'OK'
    correlation.loc[correlation['ratio'] > 2.0, 'flag'] = 'HIGH - allocated >> reported'
    correlation.loc[correlation['ratio'] < 0.5, 'flag'] = 'LOW - allocated << reported'
    correlation.loc[correlation['ratio'].isna(), 'flag'] = 'NO_MATCH'

    return correlation


def generate_detailed_comparison(
    facility_df: pd.DataFrame,
    validated_df: pd.DataFrame,
    company: str
) -> pd.DataFrame:
    """
    Generate detailed facility-level comparison for a specific company.

    Parameters
    ----------
    facility_df : pd.DataFrame
        Raw facility allocation data
    validated_df : pd.DataFrame
        Company-reported validation data
    company : str
        Company name to analyze

    Returns
    -------
    pd.DataFrame
        Detailed facility breakdown with reported data notes
    """
    patterns = COMPANY_FACILITY_PATTERNS.get(company, [company])
    pattern = '|'.join(patterns)

    mask = facility_df['facility_name'].str.contains(pattern, case=False, na=False)
    company_facilities = facility_df[mask].copy()

    # Aggregate by facility
    facility_summary = company_facilities.groupby(
        ['facility_id', 'facility_name', 'country', 'ied_activity']
    ).agg({
        'allocated_tonnes': 'sum',
        'waste_type': lambda x: ', '.join(sorted(set(x)))
    }).reset_index()

    # Get reported data for this company
    reported = validated_df[
        validated_df['company_name'].str.contains(company, case=False, na=False)
    ]

    facility_summary['company'] = company
    facility_summary['reported_notes'] = reported['extraction_notes'].iloc[0] if len(reported) > 0 else 'No reported data'

    return facility_summary.sort_values('allocated_tonnes', ascending=False)


def run_validation_analysis(
    facility_path: str = 'data/processed/facility_waste_allocated.csv',
    validated_path: str = 'data/processed/validated_company_waste.csv',
    output_path: str = 'data/processed/correlation_report.csv'
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run full validation analysis and save results.

    Parameters
    ----------
    facility_path : str
        Path to facility allocation data
    validated_path : str
        Path to company validation data
    output_path : str
        Path to save correlation report

    Returns
    -------
    tuple
        (correlation_report, detailed_facilities) DataFrames
    """
    # Load data
    facility_df = load_facility_allocated(facility_path)
    validated_df = load_validated_waste(validated_path)

    # Aggregate by company
    allocated_by_company = aggregate_facility_waste_by_company(facility_df)

    # Calculate correlation
    correlation = calculate_correlation_metrics(allocated_by_company, validated_df)

    # Save results
    correlation.to_csv(output_path, index=False)
    print(f"Correlation report saved to: {output_path}")

    # Print summary
    print("\n" + "="*80)
    print("VALIDATION CORRELATION SUMMARY")
    print("="*80)
    for _, row in correlation.iterrows():
        print(f"\n{row['company']}:")
        print(f"  Allocated (facility-level): {row['allocated_tonnes']:>12,.0f} tonnes")
        print(f"  Reported (sustainability):  {row['reported_tonnes']:>12,.0f} tonnes")
        if pd.notna(row['ratio']):
            print(f"  Ratio (allocated/reported): {row['ratio']:>12.2%}")
        print(f"  Status: {row['flag']}")

    return correlation, allocated_by_company


if __name__ == '__main__':
    correlation, facilities = run_validation_analysis()
