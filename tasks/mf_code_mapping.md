# Task: MF Code Integration with EWC-Stat/NACE/Material Types

## Status: Planned

## Summary

Create a new mapping module `mf_material_flow.py` that integrates Eurostat Material Flow (MF) codes with existing classification systems (material_type, EWC-Stat, NACE).

**Key Challenge**: MF codes track material INPUTS (extraction, consumption), while EWC-Stat tracks WASTE OUTPUTS. The mapping requires inference logic with confidence scoring.

---

## Implementation Steps

### 1. Create New Module

**File**: `src/mappings/mf_material_flow.py`

**Data Structures**:
```python
class MFCodeDefinition(TypedDict):
    description: str
    parent: str | None  # For hierarchical rollup
    level: int          # 1=top, 2=category, 3=subcategory, 4=detail

class MFMaterialMapping(TypedDict, total=False):
    material_type: str
    material_types_secondary: list[str]
    confidence: float  # 0.0-1.0

class MFWasteMapping(TypedDict, total=False):
    ewc_primary: list[str]
    ewc_secondary: list[str]
    ewc_excluded: list[str]  # Waste types this material won't produce
    confidence: float
    rationale: str

class MFNACEMapping(TypedDict, total=False):
    nace_primary: list[str]    # Main consuming industries (NACE 2-4 digit)
    nace_secondary: list[str]  # Secondary consumers
    confidence: float
    rationale: str
```

### 2. Mapping Dictionaries

| Dictionary | Purpose | Example |
|------------|---------|---------|
| `MF_CODES` | Hierarchy definition (77 codes) | `MF21: {parent: MF2, level: 2}` |
| `MF_TO_MATERIAL_TYPE` | Direct semantic mapping | `MF21 → metal_ferrous (1.0)` |
| `MF_TO_EWC_STAT` | Inferential waste mapping | `MF21 → [W061, W12A] (0.98)` |
| `MF_TO_NACE` | Industries consuming materials | `MF21 → [C24] (0.98)` |

### 3. Key Mappings

**MF to Material Type**:
| MF Category | Material Type | Confidence |
|-------------|---------------|------------|
| MF1 Biomass | organic | 1.0 |
| MF21 Iron | metal_ferrous | 1.0 |
| MF22 Non-ferrous | metal_nonferrous | 1.0 |
| MF226 Gold/Silver | metal_precious | 1.0 |
| MF3 Minerals | mineral | 1.0 |
| MF4 Fossil | chemical | 0.9 |

**MF to EWC-Stat** (inferred waste):
| MF Code | Primary Waste | Rationale |
|---------|---------------|-----------|
| MF21 Iron | W061, W12A | Iron processing → ferrous scrap, slag |
| MF227 Bauxite | W062, W12B | Aluminium → red mud, dross |
| MF13 Wood | W075, W072 | Wood → wood waste, paper |
| MF41 Coal | W124, W12A | Combustion → ash, FGD |

**MF to NACE** (industries consuming materials):
| MF Code | Description | Primary NACE | Secondary NACE | Conf. |
|---------|-------------|--------------|----------------|-------|
| **Biomass** |
| MF1 | Biomass (all) | C10-12, C16, C17 | A, C13-15, C20 | 0.8 |
| MF11 | Crops | C10, C11 | C20 | 0.95 |
| MF111 | Cereals | C10 (10.61, 10.62) | C11 | 0.98 |
| MF116 | Oil-bearing crops | C10 (10.41) | C20 | 0.95 |
| MF13 | Wood | C16, C17 | C31-32, F | 0.95 |
| MF131 | Timber | C16 (16.10) | C31, F | 0.98 |
| MF132 | Wood fuel | D (35.11) | C16 | 0.95 |
| MF14 | Fish/aquatic | C10 (10.20) | - | 0.98 |
| MF15 | Animals | C10 (10.11-10.13) | C15 | 0.95 |
| MF152 | Meat | C10 (10.11, 10.12) | - | 0.98 |
| MF153 | Dairy | C10 (10.51) | - | 0.98 |
| **Metal Ores** |
| MF2 | Metal ores (all) | C24 | C25, C28-30 | 0.9 |
| MF21 | Iron ores | C24 (24.10) | C25, F | 0.98 |
| MF22 | Non-ferrous ores | C24 (24.41-45) | C25, C26-27 | 0.95 |
| MF221 | Copper ores | C24 (24.44) | C27, C25 | 0.98 |
| MF222 | Nickel ores | C24 (24.45) | C25 | 0.95 |
| MF223 | Lead ores | C24 (24.43) | C27 | 0.95 |
| MF224 | Zinc ores | C24 (24.43) | C25 | 0.95 |
| MF225 | Tin ores | C24 (24.43) | C25 | 0.95 |
| MF226 | Gold/silver/PGM | C24 (24.41) | C26 | 0.95 |
| MF227 | Bauxite/aluminium | C24 (24.42) | C25 | 0.98 |
| MF228 | Uranium/thorium | D (35.11) | - | 0.90 |
| MF23 | Metal products | C25, C28-30 | C33 | 0.80 |
| **Non-metallic Minerals** |
| MF3 | Minerals (all) | C23, F | C20 | 0.9 |
| MF31 | Ornamental stone | C23 (23.70), F | - | 0.98 |
| MF32 | Chalk/dolomite | C23 (23.52) | C24 | 0.95 |
| MF34 | Chemical minerals | C20 (20.15) | C23 | 0.90 |
| MF35 | Salt | C20, C10 | - | 0.90 |
| MF36 | Limestone/gypsum | C23 (23.51, 23.52) | C24, F | 0.95 |
| MF37 | Clays/kaolin | C23 (23.31-23.49) | - | 0.95 |
| MF38 | Sand/gravel | C23 (23.11), F | - | 0.95 |
| MF3B | Mineral products | C23, F | - | 0.85 |
| **Fossil Energy** |
| MF4 | Fossil (all) | C19, D | C20 | 0.9 |
| MF41 | Coal | D (35.11), C19 | C24 | 0.95 |
| MF411 | Lignite | D (35.11) | - | 0.98 |
| MF412 | Hard coal | D (35.11), C19 | C24 | 0.98 |
| MF42 | Oil/gas | C19, D | C20 | 0.95 |
| MF421 | Crude oil | C19 (19.20) | C20 | 0.98 |
| MF422 | Natural gas | D (35.11) | C20 | 0.98 |
| MF43 | Fossil products | C20 (20.16) | C22 | 0.85 |

*NACE codes: C10=Food, C16=Wood, C17=Paper, C19=Petroleum, C20=Chemicals, C22=Plastics, C23=Minerals, C24=Basic metals, C25=Fabricated metals, C26=Electronics, C27=Electrical, D=Electricity, F=Construction*

### 4. Helper Functions

```python
get_material_type_for_mf(mf_code) -> str | None
get_ewc_for_mf(mf_code, include_secondary=True, min_confidence=0.0) -> list[str]
get_nace_for_mf(mf_code, include_secondary=True) -> list[str]
is_waste_valid_for_mf(mf_code, ewc_code) -> bool
get_mf_parent(mf_code) -> str | None  # For hierarchical fallback
aggregate_waste_for_mf_hierarchy(mf_code) -> dict  # Collect from all children
generate_mf_ewc_lookup_csv(output_path)  # Export for analysis
```

### 5. Update `__init__.py`

Export new module functions from `src/mappings/__init__.py`.

---

## Handling Uncertainty

1. **Confidence Scores**: 1.0 (deterministic) to 0.5 (heterogeneous)
2. **Hierarchical Fallback**: If MF111 unmapped, use parent MF11
3. **Primary/Secondary/Excluded**: Three-tier waste classification
4. **Rationale Documentation**: Each mapping explains the inference

---

## Critical Files

- `src/mappings/mf_material_flow.py` - **CREATE** (new module)
- `src/mappings/__init__.py` - **UPDATE** (add exports)
- `src/mappings/prodcom_waste.py` - Reference for patterns
- `data/raw/material_flow.csv` - Source data reference

---

## Verification

1. Run Python import test: `from src.mappings import MF_TO_EWC_STAT`
2. Verify coverage: All 77 MF codes should have hierarchy entries
3. Test fallback: `get_material_type_for_mf('MF111')` should return 'organic' via parent
4. Generate lookup CSV and spot-check mappings
5. Run existing tests: `pytest src/mappings/`

---

## Open Questions

- [ ] Is there Eurostat documentation that provides official MF to NACE correspondence tables?
- [ ] Can we use Supply-Use Tables (SUTs) to derive more deterministic mappings?
- [ ] Are there existing academic papers on MFA-waste linkages?
