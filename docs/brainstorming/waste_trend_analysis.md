# Waste Trend Analysis: Growth vs Decline Patterns

## Concept

Analyze the time series data for each waste type (EWC-Stat code) to classify them as:
- **Growing** - increasing waste generation over time (emerging problem, opportunity for new recycling infrastructure)
- **Stagnant** - stable waste volumes (established waste stream, may have existing but saturated recovery pathways)
- **Declining** - decreasing waste generation (viable recycling/recovery already exists, or industry decline)

## Motivation

The Finnish wood waste (W075) example illustrates why this matters:
- In 2004, Finland generated large quantities of wood shavings/sawdust from C16 (sawmilling)
- By 2020s, this waste stream declined significantly
- Reason: OSB and chipboard manufacturers now use this "waste" as input material
- Result: Not recorded as waste anymore because it's a valuable byproduct

**Insight**: Declining waste trends often indicate successful circular economy implementation, NOT investment opportunity.

## Analysis Approach

### Level 1: National Trends

For each `(country, waste_type)` combination:
1. Extract time series from env_wasgen (e.g., 2004-2024)
2. Calculate trend metrics:
   - Linear regression slope (tonnes/year)
   - CAGR (Compound Annual Growth Rate)
   - Volatility (coefficient of variation)
3. Classify:
   - Growing: slope > +2% CAGR, p < 0.05
   - Declining: slope < -2% CAGR, p < 0.05
   - Stagnant: otherwise

### Level 2: Facility-Level Trends (Future)

Using allocated facility data over multiple years:
1. Track waste allocations per facility over time
2. Identify facilities with growing vs declining waste profiles
3. Correlate with facility age, capacity changes, technology upgrades

## Use Cases

### 1. Investment Prioritization

| Trend | Implication | Recommendation |
|-------|-------------|----------------|
| Growing | Unmet recovery need | High priority for new recycling capacity |
| Stagnant | Existing market equilibrium | Evaluate if recovery is economically viable |
| Declining | Recovery path exists | Low priority, unless decline is due to industry shrinkage |

### 2. Market Maturity Assessment

- Compare trends across countries for same waste type
- If W075 declining in FI but growing in PL, indicates:
  - Different industrial development stages
  - Technology transfer opportunity

### 3. Forecast Confidence

- Use trend stability for allocation confidence intervals
- Growing/declining trends = lower confidence in point estimates
- Stagnant trends = higher confidence

## Data Requirements

- `env_wasgen` with full year columns (2004-2024)
- Country-level aggregations
- Later: facility-level time series from multiple allocation runs

## Potential Outputs

1. **Trend dashboard** - heatmap of waste types × countries showing growth/decline
2. **Investment signals** - ranked list of waste types by growth rate + absolute volume
3. **Market maturity index** - per-country circular economy progress by waste category
4. **Forecast intervals** - confidence bounds on waste projections

## Questions to Explore

1. Are declining trends due to:
   - Successful recycling adoption?
   - Industry contraction (e.g., manufacturing moving offshore)?
   - Reclassification in statistics?

2. For growing trends:
   - Is growth in generation or in reporting quality?
   - Which facilities are driving the growth?

3. Cross-country patterns:
   - Do Nordic countries show similar trends?
   - Can leading countries' patterns predict lagging countries' futures?

## Related Work

- Eurostat MFA (Material Flow Accounts) - `env_ac_mfa` dataset
- Circular material use rates by country
- EU Circular Economy monitoring framework indicators

---

*Note: This is a brainstorming document. Implementation not yet planned.*
