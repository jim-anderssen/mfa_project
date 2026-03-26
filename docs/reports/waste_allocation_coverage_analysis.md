# Waste Allocation Coverage Analysis

**Date:** 2026-01-18
**Context:** Emissions-based facility-level waste allocation with IED-EWC waste type validation

## Summary

After implementing waste type validation (ensuring facilities only receive waste types their IED activity can produce), allocation coverage is:

| Category | Tonnes | Percentage |
|----------|--------|------------|
| Allocated to facilities | 78,413,000 | 29.3% |
| Unallocated (no valid producer) | 189,422,000 | 70.7% |
| Unallocated (no EPRTR facilities) | 53,000 | 0.0% |
| **Total** | **267,888,000** | **100%** |

---

## Allocated Waste Types (Successfully Mapped)

These waste codes have clear IED activity mappings and are correctly allocated:

| Waste Code | Description | Tonnes | Target IED Activities |
|------------|-------------|--------|----------------------|
| W075 | Wood wastes | 31,276,000 | 6.1 (Pulp/paper) |
| W124 | Combustion wastes | 9,601,000 | 1.x, 2.x, 3.x (Energy, metals, minerals) |
| W12A | Mineral wastes from treatment | 8,233,000 | Multiple industrial |
| W12B | Other mineral wastes | 6,592,000 | 3.x (Minerals) |
| W072 | Paper and cardboard wastes | 3,322,000 | 6.1, 6.4 (Paper, food) |
| W091 | Animal and mixed food waste | 2,464,000 | 6.4, 6.5 (Food, slaughter) |
| W02A | Chemical wastes | 2,315,000 | 4.x (Chemicals) |
| W092 | Vegetal wastes | 2,147,000 | 6.1, 6.4 (Paper, food) |
| W11 | Common sludges | 2,129,000 | 6.x (Paper, food, wastewater) |
| W012 | Acid, alkaline or saline wastes | 2,104,000 | 2.6, 4.x (Surface treatment, chemicals) |
| W061 | Metal wastes, ferrous | 2,037,000 | 2.1-2.4 (Metal production) |
| W063 | Metal wastes, mixed | 1,655,000 | 2.4, 2.5 (Foundries) |
| W032 | Industrial effluent sludges | 1,431,000 | Multiple industrial |
| W071 | Glass wastes | 335,000 | 3.3, 3.4 (Glass, mineral fibres) |
| W062 | Metal wastes, non-ferrous | 197,000 | 2.5 (Non-ferrous metals) |

**Total allocated: 78,413,000 tonnes across 26 waste types**

---

## Unallocated Waste Types - Root Causes

### 1. Aggregated/Combined Waste Codes (Primary Issue)

The national statistics (`env_wasgen`) report using aggregated EWC-Stat codes that combine multiple waste categories. These cannot be mapped to specific IED activities.

| Code | Description | Tonnes | Issue |
|------|-------------|--------|-------|
| W06_07A | Recyclable wastes (metals + non-metals) | 74,195,000 | Combines W061-W071 |
| W12-13 | Mineral and solidified wastes | 27,906,000 | Aggregate of W12x + W13 |
| W12_X_127NH | Unknown aggregate code | 27,830,000 | Non-standard code |
| W01-05 | Chemical and medical waste | 12,505,000 | Aggregate code |
| W091_092 | Animal and vegetal combined | 4,615,000 | Aggregate code |
| W077_08 | PCB and equipment combined | 603,000 | Aggregate code |

**Subtotal: ~147M tonnes (55% of total)**

### 2. Mixed/General Waste Categories

These codes represent mixed wastes that don't correspond to specific industrial processes:

| Code | Description | Tonnes |
|------|-------------|--------|
| W102 | Mixed and undifferentiated materials | 5,334,000 |
| W10 | Mixed ordinary wastes | 4,286,000 |
| W101 | Household and similar wastes | 869,000 |
| W103 | Sorting residues | 357,000 |

**Subtotal: ~11M tonnes (4% of total)**

### 3. Partial Coverage (Secondary Allocations)

Some detailed codes are partially allocated but have waste from NACE sectors without matching IED facilities:

| Code | Allocated | Unallocated | Coverage |
|------|-----------|-------------|----------|
| W12A | 8,233,000 | 5,830,000 | 59% |
| W12B | 6,592,000 | 4,613,000 | 59% |
| W061 | 2,037,000 | 840,000 | 71% |
| W02A | 2,315,000 | 798,000 | 74% |

---

## Validation: Waste Type Constraints Working

The implementation correctly enforces waste-facility compatibility:

| Test | Result |
|------|--------|
| W061 (ferrous metal) only to metal IED (2.x) | PASS |
| W071 (glass) only to glass IED (3.3, 3.4) | PASS |
| W072 (paper) only to paper/food IED (6.1, 6.4) | PASS |
| No metal waste in glass facilities | PASS |
| No glass waste in metal facilities | PASS |

---

## Potential Improvements

### Option 1: Disaggregate Combined Codes
Split aggregated codes into detailed codes using sector-typical ratios:
- W06_07A → W061 (ferrous) + W062 (non-ferrous) + W071 (glass) based on NACE sector
- Requires developing disaggregation factors per NACE sector

### Option 2: Extend IED-EWC Mapping for Aggregates
Create mappings for aggregated codes:
- W06_07A in C24 → allocate to IED 2.x (metal-related)
- W06_07A in C23 → allocate to IED 3.x (mineral-related)
- Requires sector-conditional mappings

### Option 3: Fallback Allocation Mode
Add option to allocate aggregated codes without waste type validation:
- Higher coverage but less accurate
- Flag as "unvalidated" allocation method

### Option 4: Use Detailed Waste Data Source
If available, use data sources with detailed EWC-Stat codes rather than aggregated codes.

---

## Files Generated

| File | Description |
|------|-------------|
| `data/processed/facility_waste_allocated.csv` | 9,607 facility-level allocations |
| `data/processed/allocation_coverage_summary.csv` | Summary by country/NACE |
| `data/processed/unallocated_waste.csv` | 690 unallocated waste streams with reasons |

---

## Technical Notes

- Allocation method: `emissions_weighted_validated`
- Validation uses: `src/mappings/ied_ewc_stat.py`
- IED activities mapped: 76 unique activities
- Facilities in dataset: 5,744 (SE, FI, DK)
- Norway excluded (no IED data available)
