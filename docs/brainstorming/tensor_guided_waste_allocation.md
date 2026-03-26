# Tensor-Guided Waste Allocation

> **Status: Closed - Unnecessary**
>
> This approach was conceived under the assumption that we'd need to learn NACE→waste affinities from aggregate data. However, the `env_wasgen` dataset already provides waste generation broken down by (Country × NACE × Waste type). The current `emissions_based_allocator.py` allocates sector-specific waste directly—a Swedish steel plant receives waste from Swedish steel sector data (C24), not national totals.
>
> The tensor decomposition approach would only add value for: (1) filling missing data cells, (2) disaggregating higher-level NACE aggregates, or (3) cross-validating reported values. None of these are current requirements.
>
> Retained for reference in case data structure changes or imputation becomes necessary.

---

## Concept

Use tensor decomposition on aggregate statistical data (env_wasgen) to learn NACE→waste patterns, then apply those learned patterns to facility-level waste allocation.

**Key insight**: Instead of hand-coding mappings like `ied_ewc_stat.py`, let the data reveal which NACE sectors produce which waste types and in what proportions.

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│  env_wasgen (Eurostat)                                      │
│  Country × NACE × Waste type × Year                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Tensor Decomposition                                       │
│  Learn: which NACE sectors produce which waste types        │
│  Output: NACE-waste affinity matrix                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Facility Allocation                                        │
│  Facility has NACE code → look up waste affinities          │
│  Allocate national waste proportionally to facilities       │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Sketch

### Step 1: Build and Decompose Tensor

```python
import tensorly as tl
from tensorly.decomposition import parafac

# X shape: (n_countries, n_nace, n_waste_types)
# Values: waste generation in tonnes

factors = parafac(X, rank=R)
country_loadings = factors[1][0]  # (n_countries, R)
nace_loadings = factors[1][1]     # (n_nace, R)
waste_loadings = factors[1][2]    # (n_waste, R)
```

### Step 2: Compute NACE-Waste Affinity Matrix

```python
def get_nace_waste_affinity_matrix(factors):
    """
    From CP factors, compute how strongly each NACE
    associates with each waste type.
    """
    country_loadings = factors[1][0]
    nace_loadings = factors[1][1]
    waste_loadings = factors[1][2]

    # Average over countries (or weight by industrial output)
    country_weights = country_loadings.mean(axis=0)

    # NACE-waste affinity
    n_nace, n_waste = nace_loadings.shape[0], waste_loadings.shape[0]
    R = nace_loadings.shape[1]

    affinity = np.zeros((n_nace, n_waste))
    for r in range(R):
        affinity += country_weights[r] * np.outer(
            nace_loadings[:, r],
            waste_loadings[:, r]
        )

    return affinity
```

### Step 3: Allocate Waste to Facilities

```python
def allocate_waste_to_facility(facility_nace, national_waste_totals, affinity_matrix):
    """
    Given a facility's NACE code and national waste totals,
    determine which waste types (and how much) to allocate.
    """
    nace_idx = nace_to_idx[facility_nace]

    # Get this NACE's waste profile from tensor decomposition
    waste_weights = affinity_matrix[nace_idx, :]
    waste_weights = np.maximum(waste_weights, 0)
    waste_weights /= waste_weights.sum()

    # Allocate national waste proportionally
    allocated = {}
    for waste_code, weight in zip(waste_codes, waste_weights):
        if weight > threshold:
            allocated[waste_code] = national_waste_totals[waste_code] * weight

    return allocated
```

## Country-Specific Profiles

Don't average out the country dimension - use it for regional variation:

```python
def get_country_nace_waste_profile(country, nace, factors):
    """
    Get waste profile for a specific country-NACE combination.
    German steel may have different waste mix than Polish steel.
    """
    c_idx = country_to_idx[country]
    n_idx = nace_to_idx[nace]

    profile = np.zeros(n_waste)
    for r in range(R):
        profile += (
            factors[1][0][c_idx, r] *
            factors[1][1][n_idx, r] *
            factors[1][2][:, r]
        )

    return profile / profile.sum()
```

## Comparison: Rule-Based vs Tensor-Guided

| Aspect | Current (`ied_ewc_stat.py`) | Tensor-Guided |
|--------|----------------------------|---------------|
| Source | BAT documents, expert knowledge | env_wasgen statistical data |
| Output | Binary: primary/secondary/excluded | Continuous: probability weights |
| Format | `[W061, W124, W12A]` | `{W061: 0.42, W124: 0.31, ...}` |
| Country variation | None | Built-in via country loadings |
| Updates | Manual | Re-decompose with new data |

## Benefits

1. **Data-driven**: Patterns from actual reported waste, not just theory
2. **Continuous weights**: Proportions rather than binary inclusion
3. **Country-aware**: German C24 vs Romanian C24 have different profiles
4. **Handles ambiguity**: If C24 and C25 both generate W061, tensor captures the split
5. **Updatable**: New Eurostat release → re-decompose → updated weights

## Potential Use Cases

1. **Replace/augment manual mappings**: Use tensor-derived weights instead of hand-coded rules
2. **Validate existing mappings**: Compare tensor patterns against `ied_ewc_stat.py` to find gaps
3. **Country-specific allocation**: Different allocation weights per member state
4. **Uncertainty quantification**: Low-rank approximation error indicates mapping confidence

## Data Requirements

- `env_wasgen` with sufficient NACE granularity (ideally 2-digit or finer)
- Multiple years for temporal stability
- Coverage across EU member states

## Open Questions

- What rank R to use? (trade-off: interpretability vs accuracy)
- How to handle missing data in the tensor?
- Should we constrain decomposition to match known physics (e.g., steel produces slag)?
- How to integrate with existing BAT-based mappings as priors?

---

*Status: Conceptual - to be explored in future work*
