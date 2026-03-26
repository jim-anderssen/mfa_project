"""Compare E-PRTR off-site waste transfers vs Eurostat env_wasgen.

E-PRTR reports facility-level off-site transfers (subset of total waste generation).
env_wasgen reports national waste generation totals (bi-annual).
"""

import sys

import numpy as np
import pandas as pd

from src.loaders import load_dataset, PROCESSED_DIR
from src.mappings.eprtr_nace import (
    get_eprtr_codes_for_nace_section,
    get_eprtr_description,
    get_nace_section_for_eprtr,
)

EPRTR_WASTE_PATH = 'data/raw/eprtr_2025/F4_2_WasteTransfers_Facilities.csv'
OUTPUT_DIR = PROCESSED_DIR / 'eprtr_wasgen_comparison'

# E-PRTR uses full country names, env_wasgen uses ISO codes
COUNTRY_NAME_TO_ISO = {
    'Austria': 'AT', 'Belgium': 'BE', 'Bulgaria': 'BG', 'Croatia': 'HR',
    'Cyprus': 'CY', 'Czechia': 'CZ', 'Denmark': 'DK', 'Estonia': 'EE',
    'Finland': 'FI', 'France': 'FR', 'Germany': 'DE', 'Greece': 'EL',
    'Hungary': 'HU', 'Iceland': 'IS', 'Ireland': 'IE', 'Italy': 'IT',
    'Latvia': 'LV', 'Lithuania': 'LT', 'Luxembourg': 'LU', 'Malta': 'MT',
    'Netherlands': 'NL', 'Norway': 'NO', 'Poland': 'PL', 'Portugal': 'PT',
    'Romania': 'RO', 'Serbia': 'RS', 'Slovakia': 'SK', 'Slovenia': 'SI',
    'Spain': 'ES', 'Sweden': 'SE', 'Switzerland': 'CH',
    'United Kingdom': 'UK',
}
ISO_TO_COUNTRY_NAME = {v: k for k, v in COUNTRY_NAME_TO_ISO.items()}


def _resolve_country(country: str) -> tuple[str, str]:
    """Return (country_name, iso_code) from either format."""
    if len(country) == 2:
        iso = country.upper()
        name = ISO_TO_COUNTRY_NAME.get(iso)
        if not name:
            raise ValueError(f"Unknown ISO code: {iso}")
        return name, iso
    name = country.title()
    iso = COUNTRY_NAME_TO_ISO.get(name)
    if not iso:
        raise ValueError(f"Unknown country: {country}")
    return name, iso


# --- E-PRTR ---

def load_eprtr(country_name: str, nace_sections: list[str]) -> pd.DataFrame:
    """Load E-PRTR waste transfers for a country, filtered to NACE sections."""
    target_codes = get_eprtr_codes_for_nace_section(*nace_sections)
    print(f"E-PRTR activities mapping to {'/'.join(nace_sections)}: {target_codes}")

    df = pd.read_csv(EPRTR_WASTE_PATH)
    df = df[
        (df['countryName'] == country_name)
        & df['EPRTRAnnexIMainActivity'].isin(target_codes)
    ].copy()

    n_conf = (df['wasteClassification'] == 'CONFIDENTIAL').sum()
    if n_conf:
        print(f"  WARNING: {n_conf} rows with CONFIDENTIAL waste classification")

    return df


def eprtr_annual_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate E-PRTR to annual totals (tonnes)."""
    return (
        df.groupby('reportingYear')['wasteTransfers']
        .sum()
        .reset_index()
        .rename(columns={'reportingYear': 'year', 'wasteTransfers': 'eprtr_tonnes'})
    )


def eprtr_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Break down E-PRTR by activity and hazard classification."""
    breakdown = (
        df.groupby(
            ['reportingYear', 'EPRTRAnnexIMainActivity', 'wasteClassification']
        )['wasteTransfers']
        .sum()
        .reset_index()
    )
    breakdown['description'] = breakdown['EPRTRAnnexIMainActivity'].map(
        get_eprtr_description
    )
    breakdown['nace_sections'] = breakdown['EPRTRAnnexIMainActivity'].map(
        lambda x: ', '.join(get_nace_section_for_eprtr(x))
    )
    return breakdown


# --- Eurostat env_wasgen ---

def load_wasgen(geo_iso: str, nace_r2: str) -> pd.DataFrame:
    """Load env_wasgen for a country/NACE combo, TOTAL waste, HAZ_NHAZ."""
    wasgen, _, _ = load_dataset('env_wasgen')

    mask = (
        (wasgen['geo'] == geo_iso)
        & (wasgen['nace_r2'] == nace_r2)
        & (wasgen['waste'] == 'TOTAL')
        & (wasgen['hazard'] == 'HAZ_NHAZ')
    )
    row = wasgen[mask]
    if row.empty:
        print(f"WARNING: No env_wasgen data for {geo_iso} {nace_r2}")
        return pd.DataFrame(columns=['year', 'wasgen_tonnes'])

    year_cols = [c for c in row.columns if str(c).isdigit()]
    records = []
    for yr in sorted(year_cols, key=int):
        val = row[yr].values[0]
        if pd.notna(val):
            records.append({'year': int(yr), 'wasgen_tonnes': float(val)})
    return pd.DataFrame(records)


# --- Outlier detection ---

def _flag_outliers(df: pd.DataFrame, threshold: float = 2.0) -> pd.Series:
    """Flag rows where eprtr or wasgen deviates >threshold from series median.

    Returns boolean Series (True = outlier).
    """
    flagged = pd.Series(False, index=df.index)
    for col in ('eprtr_tonnes', 'wasgen_tonnes'):
        median = df[col].median()
        if median > 0:
            deviation = (df[col] / median)
            flagged |= (deviation > threshold) | (deviation < 1 / threshold)
    return flagged


# --- Comparison ---

def compare(
    country: str = 'SE',
    nace_sections: list[str] | None = None,
) -> pd.DataFrame:
    """Compare E-PRTR vs env_wasgen for one country. Returns the comparison table."""
    if nace_sections is None:
        nace_sections = ['C24', 'C25']

    country_name, iso = _resolve_country(country)
    nace_r2 = '_'.join(nace_sections)  # e.g. 'C24_C25'

    print("=" * 70)
    print("E-PRTR Off-site Waste Transfers vs Eurostat env_wasgen")
    print(f"{country_name} ({iso}), NACE {'/'.join(nace_sections)}")
    print("=" * 70)

    # Load
    eprtr_df = load_eprtr(country_name, nace_sections)
    eprtr_totals = eprtr_annual_totals(eprtr_df)
    wasgen_df = load_wasgen(iso, nace_r2)

    # Merge on overlapping years
    merged = pd.merge(eprtr_totals, wasgen_df, on='year', how='inner')
    if merged.empty:
        print("No overlapping years found.")
        return merged
    merged['ratio'] = merged['eprtr_tonnes'] / merged['wasgen_tonnes']
    merged['country'] = iso
    merged['nace'] = nace_r2
    merged['flagged'] = _flag_outliers(merged)

    clean = merged[~merged['flagged']]
    n_flagged = merged['flagged'].sum()

    print(f"\nE-PRTR year range: {eprtr_totals['year'].min()}-{eprtr_totals['year'].max()}")
    print(f"env_wasgen years: {sorted(wasgen_df['year'].tolist())}")
    print(f"Overlapping years: {sorted(merged['year'].tolist())}")

    # Comparison table
    print(f"\n{'Year':>6}  {'E-PRTR (t)':>14}  {'env_wasgen (t)':>14}  {'Ratio':>8}")
    print("-" * 53)
    for _, r in merged.iterrows():
        flag = '  *' if r['flagged'] else ''
        print(
            f"{int(r['year']):>6}  {r['eprtr_tonnes']:>14,.0f}  "
            f"{r['wasgen_tonnes']:>14,.0f}  {r['ratio']:>8.1%}{flag}"
        )
    recent_ratio = clean['ratio'].iloc[-3:].mean()
    if n_flagged:
        print(f"\n  * {n_flagged} year(s) flagged as data quality outlier (>2x median deviation)")
        print(f"  Mean ratio (last 3 periods, excl. flagged): {recent_ratio:.1%}")
    else:
        print(f"\n  Mean ratio (last 3 periods): {recent_ratio:.1%}")

    # Breakdown by activity (latest year)
    bd = eprtr_breakdown(eprtr_df)
    latest_year = bd['reportingYear'].max()
    bd_latest = bd[bd['reportingYear'] == latest_year].sort_values(
        'wasteTransfers', ascending=False
    )
    print(f"\n--- E-PRTR breakdown (year {latest_year}) ---")
    print(
        f"{'Activity':>12}  {'Hazard':>14}  {'Tonnes':>12}  "
        f"{'NACE':>8}  Description"
    )
    print("-" * 85)
    for _, r in bd_latest.iterrows():
        print(
            f"{r['EPRTRAnnexIMainActivity']:>12}  "
            f"{r['wasteClassification']:>14}  "
            f"{r['wasteTransfers']:>12,.0f}  "
            f"{r['nace_sections']:>8}  "
            f"{r['description']}"
        )

    # Save
    out_path = OUTPUT_DIR / f'{iso}_{nace_r2}.csv'
    merged[['country', 'nace', 'year', 'eprtr_tonnes', 'wasgen_tonnes', 'ratio', 'flagged']].to_csv(
        out_path, index=False
    )
    print(f"\nSaved to {out_path}")

    return merged


def _fmt_tonnes(val: float) -> str:
    """Format tonnes as human-readable string (e.g. '1.2M', '850k')."""
    if val >= 1_000_000:
        return f'{val / 1_000_000:.1f}M'
    return f'{val / 1_000:.0f}k'


def _describe_trend(series: pd.Series) -> str:
    """Describe a time series trend as 'Rising/Stable/Declining (Xk->Yk)'."""
    first, last = series.iloc[0], series.iloc[-1]
    change = (last - first) / first if first else 0
    if change > 0.25:
        direction = 'Rising'
    elif change < -0.25:
        direction = 'Declining'
    else:
        direction = 'Stable'
    return f'{direction} ({_fmt_tonnes(first)}->{_fmt_tonnes(last)})'


def _describe_ratio_trend(series: pd.Series) -> str:
    """Describe ratio trend as 'Rising/Stable/Declining (X%->Y%)'."""
    first, last = series.iloc[0], series.iloc[-1]
    change = last - first  # absolute pp change
    if change > 0.10:
        direction = 'Rising'
    elif change < -0.10:
        direction = 'Declining'
    else:
        direction = 'Stable'
    return f'{direction} ({first:.0%}->{last:.0%})'


def _build_summary(combined: pd.DataFrame) -> pd.DataFrame:
    """Build transposed summary: metrics as rows, countries as columns.

    Excludes flagged (data quality outlier) rows from all calculations.
    """
    records = {}
    for iso, grp in combined.sort_values('year').groupby('country'):
        clean = grp[~grp['flagged']]
        if clean.empty:
            continue
        name = ISO_TO_COUNTRY_NAME.get(iso, iso)
        records[name] = {
            'Mean coverage ratio': f'{clean["ratio"].iloc[-3:].mean():.0%}',
            'Ratio trend': _describe_ratio_trend(clean['ratio']),
            'env_wasgen trend': _describe_trend(clean['wasgen_tonnes']),
            'E-PRTR trend': _describe_trend(clean['eprtr_tonnes']),
        }
    return pd.DataFrame(records)


def compare_multiple_countries(
    countries: list[str],
    nace_sections: list[str] | None = None,
) -> pd.DataFrame:
    """Run compare() for each country, combine results into one table."""
    if nace_sections is None:
        nace_sections = ['C24', 'C25']

    all_results = []
    for c in countries:
        print()
        try:
            result = compare(c, nace_sections)
            if not result.empty:
                all_results.append(result)
        except ValueError as e:
            print(f"Skipping {c}: {e}")

    if not all_results:
        print("No results.")
        return pd.DataFrame()

    combined = pd.concat(all_results, ignore_index=True)
    nace_r2 = '_'.join(nace_sections)

    # Build transposed summary table
    summary = _build_summary(combined)

    print("\n" + "=" * 70)
    print(f"Cross-country summary — NACE {'/'.join(nace_sections)}")
    print("=" * 70)

    # Print as transposed table with countries as columns
    max_val_len = max(
        len(str(summary.loc[m, c]))
        for m in summary.index for c in summary.columns
    )
    col_width = max(max_val_len + 4, 22)
    label_width = max(len(idx) for idx in summary.index) + 2
    sep = '  '

    header = ' ' * label_width + sep.join(c.center(col_width) for c in summary.columns)
    print(header)
    print('-' * len(header))
    for metric in summary.index:
        row = metric.ljust(label_width)
        row += sep.join(
            str(summary.loc[metric, c]).center(col_width) for c in summary.columns
        )
        print(row)

    # Save
    out_combined = OUTPUT_DIR / f'multi_{nace_r2}.csv'
    out_summary = OUTPUT_DIR / f'multi_{nace_r2}_summary.csv'
    combined.to_csv(out_combined, index=False)
    summary.to_csv(out_summary)
    print(f"\nSaved to {out_combined}")
    print(f"Saved to {out_summary}")

    return combined


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        compare()
    elif args[0] == '--multi':
        countries = args[1:]
        compare_multiple_countries(countries)
    else:
        country = args[0]
        nace = args[1].split(',') if len(args) > 1 else None
        compare(country, nace)
