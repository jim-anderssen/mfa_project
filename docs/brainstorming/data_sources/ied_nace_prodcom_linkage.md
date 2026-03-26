# Linking IED Installations to PRODCOM Production Data

## Overview

This document describes how to link facility-level IED (Industrial Emissions Directive) installations to national-level PRODCOM production statistics for spatial allocation of industrial production and waste generation.

## Classification Systems

### IED Annex I Activity Codes
Format: `X.Y(z)` e.g., "2.5(a)", "6.6(b)"

Chapters:
1. Energy industries (1.1-1.4)
2. Production and processing of metals (2.1-2.6)
3. Mineral industry (3.1-3.5)
4. Chemical industry (4.1-4.6)
5. Waste management (5.1-5.6)
6. Other activities (6.1-6.11)

### NACE Rev. 2
Statistical classification of economic activities in the EU.
Format: `XX.XX` e.g., "24.10", "23.51"

### PRODCOM
Production statistics by product (~4,000 products).
Format: `XX.XX.XX.XX` (8 digits)
- First 4 digits = NACE class
- Digits 5-6 = CPA subcategory
- Digits 7-8 = PRODCOM specific

## Key Mappings

### Metals Production

| IED Code | Description | NACE | BAT Ref |
|----------|-------------|------|---------|
| 2.1 | Metal ore roasting/sintering | 24.10 | IS |
| 2.2 | Pig iron/steel production | 24.10 | IS |
| 2.3 | Hot-rolling mills, forges | 24.10-24.34 | FMP |
| 2.4 | Ferrous metal foundries | 24.10, 24.51-52 | SF |
| 2.5(a) | Non-ferrous from ore/secondary | 24.41-24.45 | NFM |
| 2.5(b) | Non-ferrous foundries | 24.53-24.54 | NFM |
| 2.6 | Surface treatment >30m³ | 25.61 | STM |

### Mineral Industry

| IED Code | Description | NACE | BAT Ref |
|----------|-------------|------|---------|
| 3.1(a) | Cement clinker | 23.51 | CLM |
| 3.1(b) | Lime production | 23.52 | CLM |
| 3.3 | Glass manufacture | 23.11-23.19 | GLS |
| 3.5 | Ceramic products | 23.31-23.49 | CER |

### Energy (Combustion)

| IED Code | Description | NACE | BAT Ref |
|----------|-------------|------|---------|
| 1.1 | Combustion >50 MW | 35.11, 35.30 | LCP |
| 1.2 | Refineries | 19.20 | REF |

### Materials Recovery

| IED Code | Description | NACE | BAT Ref |
|----------|-------------|------|---------|
| 5.3(b) | Non-hazardous recovery >75t/day | 38.21, 38.32 | WT |

## Spatial Resolution

| Dataset | Resolution | Use |
|---------|------------|-----|
| PRODCOM | Country (NUTS 0) | Production volumes |
| IED Installations | Facility (lat/lon) | Allocation weights |
| E-PRTR | Facility (lat/lon) | Waste transfers |
| SBS Regional | NUTS 2 | Employment proxy |

## Allocation Method

### Step 1: Count facilities by NACE and country
```
facilities_count[country, nace] = count(IED installations with that NACE)
```

### Step 2: Calculate facility share within country
```
facility_share[region, nace] = facilities_count[region, nace] / sum(facilities_count[country, nace])
```

### Step 3: Allocate PRODCOM production
```
allocated_production[region, nace] = prodcom[country, nace] * facility_share[region, nace]
```

### Step 4: Estimate waste/byproduct generation
```
waste[region, nace] = allocated_production[region, nace] * waste_factor[nace]
```

## Waste Generation Factors

| NACE | Product | Slag Factor | Total Waste Factor |
|------|---------|-------------|-------------------|
| 24.10 | Steel | 0.12 t/t | 0.15 t/t |
| 24.42 | Aluminium | - | 1.5 t red mud/t alumina |
| 35.11 | Power (coal) | - | 0.10 t ash/t coal |
| 23.51 | Cement | Uses slag | 0.02 t/t |

## Implementation

Python module created at:
```
src/agents/mappings/ied_nace_prodcom.py  # Mapping dictionaries
src/utils/ied_prodcom_linker.py          # Linkage utilities
```

### Key Functions

```python
from src.agents.mappings.ied_nace_prodcom import (
    get_nace_for_ied,        # IED code -> NACE codes
    is_prodcom_relevant,     # Check if has production data
    get_prodcom_byproduct_info,  # Waste factors
)

from src.utils.ied_prodcom_linker import (
    load_ied_installations,      # Load & parse IED CSV
    assign_nuts_region,          # Spatial join to NUTS
    count_facilities_by_nace_country,  # Aggregate counts
    allocate_prodcom_to_facilities,    # Allocate production
)
```

## Data Quality Considerations

1. **Not all facilities reported**: IED covers large installations only (thresholds apply)
2. **Multi-product facilities**: One facility may have multiple IED activities
3. **Activity vs. NACE mismatch**: IED activities don't map 1:1 to NACE
4. **Missing coordinates**: Some facilities lack precise location data
5. **Temporal alignment**: Ensure IED reporting year matches PRODCOM year

## References

- IED Directive 2010/75/EU Annex I
- E-PRTR Regulation (EC) No 166/2006
- Eurostat PRODCOM methodology
- BAT Reference Documents (BREFs)
