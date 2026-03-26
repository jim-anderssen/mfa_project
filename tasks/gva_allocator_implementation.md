# GVA-Based Waste Allocator Implementation Plan

## Overview
Create a `GVAAllocator` class that parallels `EmissionsAllocator` but uses calculated GVA (Gross Value Added) from Swedish company data to allocate national waste to facilities.

## GVA Calculation

**Formula:** `GVA = Personalkostnader + EBITDA`

Available columns in Retriever data:
- `Personalkostnader (tkr) 2022/2023/2024` - Personnel costs
- `Rörelseresultat före avskrivningar, EBITDA (tkr) 2022/2023/2024` - EBITDA

Alternative method (validation):
- `GVA = Bruttoresultat + Personalkostnader` (Gross profit + Personnel costs)

Why GVA over turnover:
- Directly measures value creation at firm level
- Matches national accounts methodology (Eurostat uses GVA)
- Accounts for capital intensity differences between firms

## File Structure

```
src/
├── allocation/
│   ├── __init__.py                    # Add GVAAllocator export
│   ├── emissions_based_allocator.py   # Reference (existing)
│   └── gva_based_allocator.py         # NEW
├── loaders/
│   └── retriever.py                   # NEW: Swedish company loader
```

## Implementation

### 1. `src/loaders/retriever.py` - Company Data Loader

```python
def load_swedish_companies(file_path: Path, years: List[int] = [2022, 2023]) -> pd.DataFrame:
    """Load Retriever Excel export, calculate GVA."""
    # Input columns:
    #   Org. nr, Företagsnamn, SNI kodlista all
    #   Personalkostnader (tkr) {year}
    #   Rörelseresultat före avskrivningar, EBITDA (tkr) {year}
    #   Antal anställda {year}
    #
    # Calculate: GVA = Personalkostnader + EBITDA
    # Returns: company_id, company_name, sni_codes, gva, employees, country_code='SE'

def parse_sni_to_nace(sni_code: str) -> str:
    """Convert 5-digit SNI to NACE format: '24101' -> 'C24.10'"""
```

### 2. `src/allocation/gva_based_allocator.py` - Main Allocator

**Reuse from EmissionsAllocator:**
- `NACE_HIERARCHY` dict (import)
- `_deduplicate_nace_hierarchy()` logic
- `_standardize_wasgen_columns()` logic
- `_parse_nace_code()` for combined codes like 'C24_C25'

**Key class:**
```python
class GVAAllocator:
    def __init__(self, companies_df, facilities_df=None, validate_waste_types=True):
        # companies_df: company_id, company_name, nace_codes, gva, country_code
        # facilities_df: optional E-PRTR data for validated mode

    def calculate_gva_shares(self, country, nace_code, waste_code=None):
        # Returns DataFrame with gva_share per company
        # If validate_waste_types: filter by IED-EWC mapping

    def allocate_waste(self, wasgen_df, countries=None, deduplicate_nace=True):
        # Main method: allocate national waste to companies by GVA share
        # Reuse NACE deduplication logic
```

**Allocation formula:**
```
Company_GVA = Personalkostnader + EBITDA
Company_waste = National_waste[NACE] × (Company_GVA / Σ Sector_GVA)
```

### 3. Update `src/allocation/__init__.py`

```python
from .emissions_based_allocator import EmissionsAllocator
from .gva_based_allocator import GVAAllocator
__all__ = ['EmissionsAllocator', 'GVAAllocator']
```

## Two Allocation Modes

### Mode 1: Simple NACE Allocation (Initial)
- All companies in NACE sector get waste proportional to GVA
- No IED/waste type validation
- Output: company-level allocations

### Mode 2: Validated IED Allocation (Future)
- Match companies to E-PRTR facilities
- Validate waste types against IED-EWC mapping
- Output: facility-level allocations with coordinates

## Output Schema

| Column | Description |
|--------|-------------|
| company_id | Organization number |
| company_name | Company name |
| country | 'SE' |
| nace | NACE sector code |
| waste_type | EWC-Stat code |
| allocated_tonnes | Waste allocated |
| national_tonnes | Total national waste |
| gva | Company GVA (tkr) |
| gva_share | Company's share of sector GVA |
| method | 'gva_calculated' |

## Key Data

**Input - Swedish companies:**
- File: `data/raw/Sweden A and C retriever export 2025 08.xlsx`
- Key columns for GVA:
  - `Org. nr` - Organization number
  - `Företagsnamn` - Company name
  - `SNI kodlista all` - SNI codes (NACE equivalent)
  - `Personalkostnader (tkr) 2022/2023` - Personnel costs
  - `Rörelseresultat före avskrivningar, EBITDA (tkr) 2022/2023` - EBITDA
  - `Antal anställda 2022/2023` - Employees (for validation)

**Input - Waste generation:**
- File: `data/interim/Generated_waste_per_nace_country.csv`
- Columns: country, nace_r2, waste, mean_wasgen

**Reference - Facilities:**
- File: `data/raw/eprtr_facilities.csv`
- Columns: facility_id, facility_name, country_code, ied_activity

## SNI to NACE Conversion

Swedish SNI codes are 5-digit NACE codes:
- `24101` → `C24.10` (Basic iron and steel)
- `25120` → `C25.12` (Metal doors/windows)
- Parse: first 2 digits = division, next 2 = group

## NACE Deduplication

Reuse `NACE_HIERARCHY` from emissions allocator:
```python
NACE_HIERARCHY = {
    'C': ['C10-C12', ..., 'C31-C33'],
    'C24_C25': ['C24', 'C25'],
    ...
}
```
When wasgen has both parent (C24_C25) and children (C24, C25), remove parent to avoid double-counting.

## Verification

1. Load Swedish companies, filter to C24/C25: ~4,955 companies expected
2. Run allocation on sample waste data
3. Verify: sum(allocated_tonnes) ≈ national_tonnes
4. Compare output structure with emissions allocator output

## Implementation Order

1. `src/loaders/retriever.py` - data loading
2. `src/allocation/gva_based_allocator.py` - core class (simple mode)
3. Update `__init__.py`
4. Test with Swedish C24/C25 data
5. (Future) Add validated IED mode
