# Steel Tracker Validation Plan

## Overview

Use Global Iron and Steel Tracker (GEM) data as ground truth to validate the facility allocation pipeline's regime classification (BF/BOF vs EAF).

## Key Validation Opportunity

The pipeline's Stage 2 uses NMF on emissions to classify steel facilities into production regimes. The GEM tracker provides **explicit ground truth** for this classification:

| GEM Data | Pipeline Inference |
|----------|-------------------|
| `Nominal BOF steel capacity (ttpa)` | Regime: BF/BOF (high CO2, PM) |
| `Nominal EAF steel capacity (ttpa)` | Regime: EAF (lower CO2, scrap-based) |
| `Nominal BF capacity (ttpa)` | Ironmaking capacity indicator |
| `Nominal DRI capacity (ttpa)` | Alternative iron route |

## Validation Approach

### 1. Facility Matching (GEM ↔ E-PRTR)

**Match criteria:**
- Geographic proximity: GEM coordinates ↔ E-PRTR IED lat/lon (threshold ~1km)
- Country filter: Same country
- Activity filter: E-PRTR `IEDAnnexIMainActivity = '2.2'`

**Output:** `gem_eprtr_matched.csv` with facility pairs

### 2. Regime Classification Accuracy

**Test:** Compare pipeline-inferred regime with GEM ground truth

```python
# Ground truth from GEM
bof_dominant = gem['Nominal BOF steel capacity'] > gem['Nominal EAF steel capacity']
eaf_dominant = gem['Nominal EAF steel capacity'] > gem['Nominal BOF steel capacity']

# Pipeline inference from emissions NMF
predicted_regime = pipeline.assign_facility_regimes(eprtr_facility)

# Accuracy = matches / total
```

**Metrics:**
- Classification accuracy (BF/BOF vs EAF)
- Confusion matrix by country/region
- Misclassification analysis

### 3. Capacity-Emissions Correlation

**Test:** Validate that emissions scale with declared capacity

```python
correlation(gem['Nominal crude steel capacity'], eprtr['CO2_emissions'])
correlation(gem['Nominal crude steel capacity'], eprtr['total_emissions'])
```

**Expected:** Strong positive correlation for Stage 1 allocation validation

### 4. Coverage Analysis

**European facilities in GEM (0.5 MTPA+):**
- Comprehensive coverage of major steel producers
- Sweden: SSAB Luleå (BF/BOF), SSAB Oxelösund (BF/BOF), Sandvik (EAF)
- Nordic: Outokumpu, Ruukki, etc.

**E-PRTR IED 2.2 coverage:** ~1,804 facilities globally

## Implementation

### New Module: `src/validation/steel_tracker.py`

```python
def load_gem_steel_data(plant_file, unit_file):
    """Load GEM plant and unit-level data."""

def match_gem_to_eprtr(gem_df, eprtr_df, distance_km=1.0):
    """Spatial join GEM plants to E-PRTR facilities."""

def classify_gem_regime(gem_row):
    """Determine ground truth regime from GEM capacity columns."""

def validate_regime_classification(matched_df, pipeline_predictions):
    """Calculate accuracy metrics."""

def validate_capacity_emissions_correlation(matched_df):
    """Test emissions vs capacity scaling."""
```

### Test Cases

| Facility | GEM Classification | Expected Pipeline Regime |
|----------|-------------------|-------------------------|
| SSAB Luleå | BF/BOF dominant | High CO2, PM signature |
| SSAB Borlänge | EAF | Lower CO2, scrap profile |
| ArcelorMittal Gent | BF/BOF | Integrated site |
| Stena Stål | EAF only | Scrap-based |

## Data Requirements

**Input files:**
- `data/raw/Global iron and steel tracker/Plant-level-data-*.xlsx`
- `data/raw/Global iron and steel tracker/Steel-unit-data-*.xlsx`
- `data/raw/F6_1_IED_Installations.csv` (E-PRTR facilities)
- `data/raw/F1_4_Air_Releases_Facilities.csv` (emissions)

**Output files:**
- `data/processed/validation/gem_eprtr_matched.csv`
- `data/processed/validation/regime_accuracy_report.csv`

## Integration with Pipeline

Update `tasks/facility_allocation_pipeline.md` verification section:

```markdown
### Stage 2 validation (enhanced):
- **GEM Steel Tracker validation**: Use Global Iron & Steel Tracker as
  ground truth for BF/BOF vs EAF classification
- Spatial match GEM plants to E-PRTR facilities
- Calculate regime classification accuracy
- Report confusion matrix by technology route
```

## Summary

The GEM tracker is ideal validation data because:
1. **Explicit process labels** (BOF vs EAF capacity) - no inference needed
2. **Capacity metrics** - enables emissions scaling validation
3. **Coordinates** - enables spatial matching
4. **European coverage** - overlaps with E-PRTR geography
5. **Unit-level detail** - can validate integrated vs single-process sites
