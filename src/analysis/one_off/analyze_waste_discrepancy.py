"""Analyze waste reporting discrepancies across EU countries for NACE C24_C25."""

import pandas as pd
import numpy as np
from src.loaders import load_dataset, extend_eurostat_dataset

# Load data
wasgen, labels, label_descriptions = load_dataset("env_wasgen")
wasgen = extend_eurostat_dataset((wasgen, labels, label_descriptions), ["nace_r2", "waste", "geo"])

# Filter for HAZ_NHAZ and C24_C25
countries = ['SE', 'FI', 'PL', 'DE', 'IT']
df = wasgen[
    (wasgen['hazard'] == 'HAZ_NHAZ') &
    (wasgen['nace_r2'] == 'C24_C25') &
    (wasgen['geo'].isin(countries))
].copy()

# Get year columns
year_cols = [c for c in df.columns if str(c).isdigit()]
year_cols = sorted(year_cols)

print("="*80)
print("ANALYSIS: Waste Reporting Discrepancies in NACE C24_C25")
print("="*80)

# 1. Show TOTAL trends per country
print("\n1. TOTAL WASTE TRENDS (in tonnes)")
print("-"*60)
total_df = df[df['waste'] == 'TOTAL'][['geo', 'geo_description'] + year_cols]
for _, row in total_df.iterrows():
    print(f"\n{row['geo']} ({row['geo_description']}):")
    vals = []
    for y in year_cols:
        v = row[y]
        if pd.notna(v):
            vals.append(f"{y}: {v/1e6:.2f}M")
    print("  " + " | ".join(vals))

# 2. Count waste codes reported per country per year
print("\n\n2. NUMBER OF WASTE CODES REPORTED PER COUNTRY PER YEAR")
print("-"*60)
codes_per_year = {}
for geo in countries:
    geo_df = df[df['geo'] == geo]
    codes_per_year[geo] = {}
    for year in year_cols:
        # Count non-null, non-zero values
        valid = geo_df[year].notna() & (geo_df[year] > 0)
        codes_per_year[geo][year] = valid.sum()

print(pd.DataFrame(codes_per_year))

# 3. Identify waste codes that disappeared or appeared
print("\n\n3. WASTE CODES PRESENCE ANALYSIS")
print("-"*60)

early_years = [y for y in year_cols if int(y) <= 2008]
late_years = [y for y in year_cols if int(y) >= 2018]

for geo in countries:
    geo_df = df[df['geo'] == geo]
    print(f"\n{geo}:")

    # Codes with early data but no late data
    early_present = set()
    late_present = set()

    for _, row in geo_df.iterrows():
        waste = row['waste']
        has_early = any(pd.notna(row[y]) and row[y] > 0 for y in early_years if y in row.index)
        has_late = any(pd.notna(row[y]) and row[y] > 0 for y in late_years if y in row.index)

        if has_early:
            early_present.add(waste)
        if has_late:
            late_present.add(waste)

    disappeared = early_present - late_present
    appeared = late_present - early_present

    if disappeared:
        print(f"  Codes DISAPPEARED (in early years but not recent):")
        for code in sorted(disappeared):
            desc = geo_df[geo_df['waste']==code]['waste_description'].iloc[0] if len(geo_df[geo_df['waste']==code]) > 0 else 'N/A'
            print(f"    {code}: {desc}")

    if appeared:
        print(f"  Codes APPEARED (not in early years but in recent):")
        for code in sorted(appeared):
            desc = geo_df[geo_df['waste']==code]['waste_description'].iloc[0] if len(geo_df[geo_df['waste']==code]) > 0 else 'N/A'
            print(f"    {code}: {desc}")

# 4. Major waste code contributions to TOTAL
print("\n\n4. TOP WASTE CODES BY CONTRIBUTION (2004 vs 2022)")
print("-"*60)

for geo in countries:
    geo_df = df[(df['geo'] == geo) & (df['waste'] != 'TOTAL')].copy()
    print(f"\n{geo}:")

    for year in ['2004', '2022']:
        if year in geo_df.columns:
            year_data = geo_df[['waste', 'waste_description', year]].dropna(subset=[year])
            year_data = year_data[year_data[year] > 0].sort_values(year, ascending=False)

            total = year_data[year].sum()
            print(f"\n  {year} (Total from codes: {total/1e6:.2f}M):")
            for _, row in year_data.head(5).iterrows():
                pct = row[year] / total * 100 if total > 0 else 0
                print(f"    {row['waste']}: {row[year]/1e6:.2f}M ({pct:.1f}%) - {row['waste_description'][:40]}")

# 5. Specific focus: W124 (metallic wastes)
print("\n\n5. W124 (METALLIC WASTES) TRENDS")
print("-"*60)
w124_df = df[df['waste'] == 'W124'][['geo', 'geo_description'] + year_cols]
for _, row in w124_df.iterrows():
    print(f"\n{row['geo']}:")
    vals = []
    for y in year_cols:
        v = row[y]
        if pd.notna(v):
            vals.append(f"{y}: {v/1e6:.2f}M")
    print("  " + " | ".join(vals))

# 6. Check aggregate codes (W06-W09) that may have changed over time
print("\n\n6. AGGREGATE WASTE CODES ANALYSIS")
print("-"*60)
aggregate_codes = [c for c in df['waste'].unique() if c.startswith(('W0', 'W1', 'W2'))]
aggregate_codes = sorted(aggregate_codes)

print(f"Waste codes found: {aggregate_codes[:20]}...")

# Compare W061/W062 etc vs their parent codes
print("\n\nParent vs child code analysis:")
for parent in ['W06', 'W07', 'W08', 'W09', 'W10', 'W11', 'W12']:
    children = [c for c in aggregate_codes if c.startswith(parent) and c != parent]
    if children:
        print(f"\n  {parent} children: {children}")

# 7. Check for specific large changes
print("\n\n7. LARGEST CHANGES BY WASTE CODE (2004 → 2022)")
print("-"*60)
for geo in countries:
    geo_df = df[(df['geo'] == geo) & (df['waste'] != 'TOTAL')].copy()

    if '2004' in geo_df.columns and '2022' in geo_df.columns:
        geo_df['change'] = geo_df['2022'].fillna(0) - geo_df['2004'].fillna(0)
        geo_df['pct_change'] = ((geo_df['2022'].fillna(0) - geo_df['2004'].fillna(0)) / geo_df['2004'].fillna(1)) * 100

        significant = geo_df[abs(geo_df['change']) > 100000].sort_values('change')

        if len(significant) > 0:
            print(f"\n{geo} - Significant changes (>100k tonnes):")
            for _, row in significant.iterrows():
                v2004 = row['2004'] if pd.notna(row['2004']) else 0
                v2022 = row['2022'] if pd.notna(row['2022']) else 0
                print(f"  {row['waste']}: {v2004/1e6:.2f}M → {v2022/1e6:.2f}M (Δ{row['change']/1e6:+.2f}M)")
                print(f"    {row['waste_description'][:60]}")
