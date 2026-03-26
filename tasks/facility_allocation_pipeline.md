# National Waste Allocation & Facility Characterization Pipeline

## Overview

Three-stage system to allocate national waste statistics to facilities and derive facility-specific waste profiles from emissions regimes.

## Stage 1: National Waste Allocation to Facilities

**Goal**: Allocate `env_wasgen` (Country × NACE × Waste type) to individual E-PRTR facilities.

### Allocation Strategy
1. **Primary**: GVA-based allocation using company financial data (Orbis/Retriever)
2. **Fallback**: Emissions-weighted allocation (existing `EmissionsAllocator`)
3. **Final fallback**: Equal distribution among matching facilities

### New Modules

**`src/loaders/company_financials.py`**
- `load_retriever_export()` - Load Swedish company data from Retriever
- `calculate_gva_from_financials()` - Derive GVA from financial statements
- `match_to_eprtr_facilities()` - Match companies to facilities (name/location)

**`src/allocation/economic_allocator.py`**
- `EconomicAllocator` class - GVA-based facility allocation
- Company-to-facility matching with confidence scoring
- Falls back to emissions when GVA unavailable

**`src/allocation/hybrid_allocator.py`**
- `HybridAllocator` class - Orchestrates GVA + emissions allocation
- Tracks allocation method per facility (`gva`, `emissions`, `equal_share`)

### Enhancement to Existing
- Add `allocation_method` column to `EmissionsAllocator` output
- Expose `calculate_emission_shares()` for reuse

### Output
`facility_waste_allocated.csv` with columns:
- facility_id, facility_name, country, lat, lon, ied_activity
- waste_type, allocated_tonnes, allocation_method

---

## Stage 2: Facility Waste Profile Derivation

**Goal**: Use tensor decomposition on emissions to identify process sub-types within IED categories.

### Data Sources

| Source | Facilities | Pollutants | 5+ pollutants |
|--------|-----------|------------|---------------|
| Air releases (F1) | 26,815 | 69 | 8.4% |
| Water releases (F2) | 7,482 | 81 | 38.4% |
| **Transfers (F3)** | 4,780 | 89 | 13.6% |

**Transfers data value**: Reports pollutants *in waste* sent to off-site treatment (not emissions). Directly characterizes waste content. 2,564 facilities report transfers but no air/water releases → extends coverage.

### Data Coverage
- ~15-20% of facilities have 5+ pollutants (fingerprint-viable)
- ~70-80% facilities get IED-level default profiles
- Data-rich IEDs (air+water): energy (42%), waste/wastewater (35%), paper (38%), minerals (28%)

### Algorithm

**For each IED category:**
1. Build matrix `X[n_facilities × n_pollutants]` from E-PRTR air+water releases + transfers
2. Apply NMF (Non-negative Matrix Factorization) → R latent regimes
3. Auto-select R using reconstruction error elbow
4. Interpret regimes using BREF-derived domain knowledge
5. Assign facilities to regimes based on loadings

### New Modules

**`src/loaders/eprtr_extended.py`**
- `load_full_air_releases()` - Load all 69 air pollutants
- `load_full_water_releases()` - Load all 81 water pollutants
- `load_transfers()` - Load all 89 transfer pollutants (waste content)
- `create_facility_pollutant_matrix()` - Build (facility × pollutant) matrix from all sources
- `get_pollutant_coverage_by_ied()` - Analyze data density

**`src/decomposition/emissions_regimes.py`**
- `EmissionsRegimeDecomposer` class
- `fit_ied_category()` - NMF for one IED category
- `_interpret_regimes()` - Map pollutant patterns to process types
- `assign_facility_regimes()` - Tiered assignment (fingerprint vs default)

**`src/decomposition/regime_waste_mapping.py`**
- BREF-derived regime → waste profile mappings
- `STEEL_REGIME_WASTE_PROFILES` (BF/BOF vs EAF routes)
- `PULP_PAPER_REGIME_WASTE_PROFILES` (Kraft vs mechanical vs recycled)
- `get_regime_waste_profile()` - Lookup function

**`src/decomposition/transfer_signatures.py`**
- Transfer-based process discrimination rules
- `KRAFT_SIGNATURE`: High AOX (>10t), high TOC (~2Mt) in transfers
- `RECYCLED_PAPER_SIGNATURE`: No AOX, elevated Zn/phenols (deinking)
- `classify_by_transfers()` - Direct process assignment from transfer profile

### Tiered Assignment Logic
```
IF facility has clear transfer signature (e.g., AOX >10t for Kraft):
    → Direct process assignment from transfers
    → High confidence (waste content directly observed)
ELIF facility has 5+ pollutants (air+water+transfers):
    → Use facility-specific NMF loadings to assign regime
    → Apply regime-specific waste profile
ELSE:
    → Assign IED-level default profile
    → Use emissions only as quantity proxy
```

**Transfer signatures validated** (pulp/paper example):
- AOX >10t → Kraft chemical pulp (35x separation from other processes)
- No AOX + Zn/phenols → Recycled paper deinking

### IED-Level Certainty Tracking

Each IED category gets a certainty score based on:
- **Data density**: % of facilities with 5+ pollutants
- **Reconstruction quality**: NMF reconstruction error
- **Regime separation**: How distinct the regimes are (inter-regime distance)

Stored in `ied_certainty_scores.csv`:
- ied_code, n_facilities, pct_fingerprinted, reconstruction_error, certainty_score

### Output
`facility_regime_profiles.csv` with columns:
- facility_id, ied_code, primary_regime, regime_scores
- waste_character (dict of waste type proportions)
- fingerprint_quality (`full` or `ied_default`)
- ied_certainty (0-1: inherited from IED category)

---

## Stage 3: Hotspot Identification

**Goal**: Combine volume (Stage 1) and character (Stage 2) to identify recovery investment opportunities.

### Scoring Dimensions
1. **Volume**: Total tonnes of target waste in region
2. **Concentration**: % of regional waste that's target type
3. **Recovery potential**: Material value from waste composition
4. **Infrastructure gap**: Generation vs existing treatment capacity
5. **Certainty**: Confidence in waste characterization (see below)

### Certainty Scoring

**Regional certainty** (higher = more confident in region's waste character):
- Proportion of facilities with fingerprinted profiles (`full`) vs IED defaults
- Example: Region with 8/10 facilities fingerprinted → high certainty
- Weighted by facility volume (large fingerprinted facilities matter more)

**IED-level certainty** (propagates from Stage 2):
- Based on decomposition quality for each IED category
- Factors: number of facilities with 5+ pollutants, reconstruction error, regime separation
- Data-rich IEDs (cement 74%, pulp 74%, steel 55%) → higher certainty
- Data-poor IEDs → lower certainty, wider confidence intervals

**Certainty calculation**:
```
regional_certainty = sum(fingerprinted_tonnes) / sum(all_tonnes)
ied_certainty = weighted_mean(ied_certainty_scores) by volume per IED in region
combined_certainty = regional_certainty * mean(ied_certainty)
```

### New Module

**`src/analysis/hotspot_scorer.py`**
- `HotspotScorer` class
- `aggregate_by_region()` - Geographic clustering using existing `facility_clustering.py`
- `calculate_volume_score()`, `calculate_concentration_score()`
- `calculate_recovery_potential()` - Material value from regime profiles
- `calculate_regional_certainty()` - Fingerprint coverage in region
- `calculate_ied_certainty()` - Profile specificity by IED category
- `score_hotspots()` - Weighted composite score
- `generate_investment_report()` - Actionable output

### Integration with Existing
- Use `facility_clustering.py` with `features_first` mode
- Max distance constraint (e.g., 300km)
- Waste-profile-consistent geographic subgroups

### Output
`recovery_hotspots.csv` with columns:
- region_id, centroid_lat, centroid_lon, facilities
- total_tonnes, target_tonnes, concentration_pct
- recovery_potential_score, infrastructure_gap
- **regional_certainty** (0-1: proportion fingerprinted by volume)
- **ied_certainty** (0-1: weighted IED profile quality)
- **combined_certainty** (0-1: overall confidence)
- composite_score, dominant_waste_character

---

## Critical Files

**To modify:**
- `src/allocation/emissions_based_allocator.py` - Add allocation_method column

**To create:**
- `src/loaders/company_financials.py`
- `src/allocation/economic_allocator.py`
- `src/allocation/hybrid_allocator.py`
- `src/loaders/eprtr_extended.py`
- `src/decomposition/emissions_regimes.py`
- `src/decomposition/regime_waste_mapping.py`
- `src/decomposition/transfer_signatures.py`
- `src/analysis/hotspot_scorer.py`

**Reference:**
- `docs/brainstorming/emissions_based_waste_characterization.md` - Domain knowledge
- `src/mappings/ied_ewc_stat.py` - IED to waste type mapping
- `src/analysis/facility_clustering.py` - Geographic clustering

---

## Verification Plan

1. **Stage 1 validation**: Compare allocated tonnes with company sustainability reports using existing `validation_correlation.py`
2. **Stage 2 validation**:
   - Verify steel facilities (SSAB Luleå → BF/BOF, Stena Stål → EAF) assigned to correct regimes
   - Verify pulp/paper transfers: Zellstoff Pöls (AOX=117t) → Kraft, recycled mills → deinking profile
3. **Integration test**: Run full pipeline for Sweden using Retriever data

---

## Implementation Order

1. `src/loaders/eprtr_extended.py` - Foundation for Stage 2 (air, water, transfers)
2. `src/decomposition/regime_waste_mapping.py` - BREF knowledge base
3. `src/decomposition/transfer_signatures.py` - Direct process rules from transfers
4. `src/decomposition/emissions_regimes.py` - Core tensor decomposition
5. `src/loaders/company_financials.py` - Foundation for Stage 1 GVA
6. `src/allocation/economic_allocator.py` - GVA-based allocation
7. `src/allocation/hybrid_allocator.py` - Combined allocation
8. `src/analysis/hotspot_scorer.py` - Final stage
