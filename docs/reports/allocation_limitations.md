# Emissions-Based Waste Allocation: Coverage and Limitations

This document explains the emissions-based waste allocation methodology, its coverage limitations, and how to interpret allocation results correctly.

## Overview

The emissions-based allocation method distributes nationally-reported waste generation (from Eurostat `env_wasgen`) to individual E-PRTR facilities using pollutant emissions (CO2, NOx, PM10) as allocation proxies.

**Key insight**: Only ~30% of industrial waste can be allocated to specific E-PRTR facilities. The remaining ~70% cannot be allocated due to structural limitations in how data is reported - this is expected behavior, not a data quality issue.

---

## Allocation Method

### How It Works

For each (country, NACE sector, waste type) combination in national waste generation data:

1. **Find matching facilities**: Identify E-PRTR facilities in the country with matching NACE sector
2. **Filter by waste type**: Keep only facilities whose IED activity can produce this waste type (based on IED → EWC-Stat mapping)
3. **Calculate emission shares**: For each valid facility:
   ```
   share = (w_CO2 × CO2_f/CO2_total) + (w_NOx × NOx_f/NOx_total) + (w_PM10 × PM10_f/PM10_total)
   ```
4. **Allocate waste**: `facility_waste = national_waste × facility_share`

### Sector-Specific Emission Weights

Different industries have different emission profiles. The allocator uses sector-specific weights stored in `data/processed/lookuptables/sector_emission_weights.csv`.

Default weights (when sector not specified):
- CO2: 55%
- NOx: 30%
- PM10: 15%

---

## Why Waste Remains Unallocated

### Unallocated Waste Categories

| Category | Example Codes | Typical % | Root Cause |
|----------|--------------|-----------|------------|
| Composite aggregates | `W06_07A`, `W12_X_127NH` | ~57% | Eurostat confidentiality/aggregation |
| Top-level aggregates | `W06`, `W12-13` | ~31% | Incomplete detailed reporting |
| Derived aggregates | `W08A`, `W12A`, `W12B` | ~6% | Statistical composites |
| Detailed codes | `W061`, `W062` | ~6% | No matching IED facility |

### Detailed Explanation

#### 1. Composite Aggregate Codes (~57%)

Eurostat reports certain waste streams as composite codes when individual categories cannot be disclosed:

- **`W06_07A`**: "Metallic and non-metallic mineral wastes" - combines metal processing waste (W06) with glass/mineral waste (W07)
- **`W12_X_127NH`**: "Other waste excluding W127 non-hazardous" - a catch-all category

These codes exist because:
- Individual waste streams are too small to report separately
- Confidentiality rules prevent disclosure of single-facility data
- Member states aggregate to meet reporting thresholds

**These cannot be allocated** because they span multiple waste types that may come from different facility types.

#### 2. Top-Level Aggregate Codes (~31%)

When countries report at aggregate level instead of detailed level:

- **`W06`**: All "Metallic wastes" without breakdown by type
- **`W12-13`**: "Discarded equipment and vehicles" without component detail

This happens when:
- Member states lack detailed tracking systems
- Small quantities are grouped for efficiency
- Historical reporting practices haven't been updated

#### 3. Derived Aggregate Codes (~6%)

Statistical composites created by Eurostat for analysis:

- **`W08A`**: Derived category combining specific waste streams
- **`W12A`**, **`W12B`**: Analytical groupings of equipment waste

#### 4. Detailed Codes Without IED Match (~6%)

Some detailed waste codes exist but no E-PRTR facilities report activities that produce them:

- Small facilities below E-PRTR reporting thresholds
- Non-IED industrial activities
- Waste from sectors not covered by IED (e.g., small workshops)

---

## EWC-Stat Code Hierarchy

Understanding the code structure helps explain allocation coverage:

### Structure

```
W06       (Level 1)  - Metallic wastes
├── W061  (Level 2)  - Ferrous metal wastes
├── W062  (Level 2)  - Non-ferrous metal wastes
└── W063  (Level 2)  - Mixed metallic wastes
```

### Composite Code Examples

| Code | Description | Components |
|------|-------------|------------|
| `W06_07A` | Metallic + non-metallic mineral | W06 + W07A |
| `W077_08` | Glass + chemical deposit waste | W077 + W08 |
| `W091_092` | Animal + vegetal tissue waste | W091 + W092 |
| `W12_X_127NH` | Other waste excl. W127 non-haz | W12 - W127(NH) |
| `W128_13` | WEEE + vehicles | W128 + W13 |

### Key Waste Categories

| Code | Description | Typical Sources |
|------|-------------|-----------------|
| W01-05 | Chemical wastes | Chemical industry (C20) |
| W06 | Metallic wastes | Metal processing (C24, C25) |
| W07 | Non-metallic wastes | Glass, mineral processing (C23) |
| W09 | Animal/vegetal wastes | Food processing (C10-C12) |
| W10 | Mixed ordinary wastes | All manufacturing |
| W12-13 | Equipment/vehicles | Automotive, electronics (C26-C30) |

---

## Interpretation Guidelines

### What Allocated Waste Represents

- **Industrial facilities registered in E-PRTR**: Only large installations meeting reporting thresholds
- **IED-covered activities**: Facilities with Industrial Emissions Directive permits
- **Validated waste-producer relationships**: Allocations only where the facility's activity can actually produce that waste type

### What Unallocated Waste Represents

Unallocated waste is NOT missing or erroneous. It represents:

- Waste from **small facilities** below E-PRTR thresholds
- Waste from **non-IED activities** (workshops, small manufacturers)
- **Statistically aggregated** waste that cannot be disaggregated
- Waste from **sectors not in scope** (construction, services)

### Valid Use Cases

**Appropriate for:**
- Identifying large industrial waste sources
- Facility-level emissions-waste correlations
- Hotspot analysis of major industrial facilities
- Comparing waste intensity across large installations

**Not appropriate for:**
- Total national waste accounting
- Small and medium enterprise (SME) waste analysis
- Complete sectoral waste inventories
- Regulatory compliance verification

---

## Coverage by Country (Nordic Example)

Based on current allocation results for manufacturing sector (NACE C):

| Country | Allocated (Mt) | Facilities | Coverage |
|---------|---------------|------------|----------|
| Finland | 30.0 | 360 | ~40% |
| Sweden | 15.1 | 444 | ~29% |
| Denmark | 2.2 | 271 | ~30% |

Coverage varies by:
- **Country**: Reporting practices and facility landscape differ
- **Sector**: Energy-intensive sectors have higher E-PRTR coverage
- **Waste type**: Common industrial wastes have better coverage than specialized streams

---

## Data Sources

| Source | Content | Used For |
|--------|---------|----------|
| E-PRTR | Facility registry and emissions | Allocation base |
| Eurostat `env_wasgen` | National waste by NACE/waste type | Waste volumes |
| IED-EWC mapping | Activity → waste type validation | Producer validation |
| Sector weights | NACE → emission weight profiles | Allocation formula |

---

## Files Reference

| File | Description |
|------|-------------|
| `data/processed/facility_waste_allocated.csv` | Facility-level allocations |
| `data/processed/allocation_coverage_summary.csv` | Coverage statistics by country/NACE |
| `data/processed/unallocated_waste.csv` | Waste streams that could not be allocated |
| `src/allocation/emissions_based_allocator.py` | Allocation implementation |
| `src/mappings/ied_ewc_stat.py` | IED activity → EWC-Stat mapping |

---

## Technical Notes

### Unallocation Reasons

The `unallocated_waste.csv` file includes a `reason` column:

- **`no_eprtr_facilities`**: No E-PRTR facilities exist for this country/NACE combination
- **`no_valid_producer`**: Facilities exist but none have IED activities that produce this waste type

### No Double Counting

The allocation ensures:
- Each tonne is allocated once or not at all
- Allocated + Unallocated = National Total
- Composite codes are never double-counted with their components (they are separate reporting)

### Validation

Allocation quality can be verified by:
1. Summing allocated tonnes per country/NACE should not exceed national totals
2. Coverage percentages should sum with unallocated to 100%
3. Facility shares within a group should sum to 1.0

---

## NACE Hierarchy and Double-Counting Prevention

### The Problem

Eurostat waste generation data (`env_wasgen`) reports waste at multiple NACE hierarchy levels:

| NACE Code | Description | Relationship |
|-----------|-------------|--------------|
| `C` | All manufacturing | Parent aggregate |
| `C16` | Wood products | Subset of C |
| `C17_C18` | Paper/printing | Subset of C |
| `C24_C25` | Basic metals | Subset of C |

If both the aggregate `C` and its detailed subsectors are used in allocation, the same waste would be counted twice. For example, Finland's W075 (wood waste):
- C: 12.7 Mt
- C16: 7.6 Mt (already included in C)
- C17_C18: 5.0 Mt (already included in C)

Without filtering, this would allocate 25.3 Mt instead of the correct ~12.7 Mt.

### The Solution

The data loader (`src/loaders/nuts2.py`) excludes aggregate NACE codes when detailed subsectors are available:

**Excluded aggregates:**
- `C` (all manufacturing)
- `E` (water supply, sewerage, waste management)

**Used instead - detailed subsectors:**
- Manufacturing: C10-C12, C13-C15, C16, C17_C18, C19, C20-C22, C23, C24_C25, C26-C30, C31-C33
- Water/Waste: E36_E37_E39, E38

This ensures each unit of waste is counted exactly once.

### Coverage Check

The loader warns if any country has aggregate `C` data but no detailed manufacturing subsectors. This would indicate potential data loss for that country.

### Subsector Coverage

The detailed manufacturing subsectors cover NACE divisions 10-33:

| Code | NACE Divisions | Description |
|------|---------------|-------------|
| C10-C12 | 10, 11, 12 | Food, beverages, tobacco |
| C13-C15 | 13, 14, 15 | Textiles, apparel, leather |
| C16 | 16 | Wood products |
| C17_C18 | 17, 18 | Paper, printing |
| C19 | 19 | Coke, petroleum |
| C20-C22 | 20, 21, 22 | Chemicals, pharma, rubber/plastic |
| C23 | 23 | Non-metallic minerals |
| C24_C25 | 24, 25 | Basic metals, fabricated metal |
| C26-C30 | 26-30 | Electronics, machinery, vehicles |
| C31-C33 | 31, 32, 33 | Furniture, other, repair |
