# Facility Waste Allocation Validation Report

Comparison of emission-based waste allocation model against company-reported environmental data from site-specific miljörapporter (environmental reports).

## Summary

| Facility | Country | Allocated | Reported | Ratio | Status |
|----------|---------|----------:|---------:|------:|--------|
| SSAB Luleå | SE | 91,497 t | 83,654 t | 91.4% | VALIDATED |
| SSAB Oxelösund | SE | 100,410 t | - | - | PENDING |
| Outokumpu Tornio | FI | 121,274 t | - | - | PENDING |
| Outokumpu Avesta | SE | 95,089 t | - | - | PENDING |

---

## SSAB Luleå - VALIDATED

**Source:** [Miljörapport 2024 SSAB Luleå](https://www.ssab.com/sv-se/-/media/files/company/sustainability/environmental-reports/miljorapport_2024_ssab_lulea.pdf) (Pages 63-67, Tables 31-34)

### Comparison

| Metric | Value |
|--------|------:|
| Allocated (emission-based model) | 91,497 tonnes |
| Reported (Miljörapport 2024) | 83,654 tonnes |
| Difference | +7,843 tonnes |
| Ratio (reported/allocated) | 91.4% |
| **Status** | **GOOD MATCH** |

### Reported Waste Breakdown

| Category | Tonnes | Source | Notes |
|----------|-------:|--------|-------|
| To landfill (deponi) | 36,700 | Tabell 31 | On-site deposits |
| External recycling (externt återanvänt) | 40,100 | Tabell 31 | Sent for external processing |
| General waste (övriga allmänna avfall) | 5,591 | Tabell 33 | Metal scrap, construction waste |
| Hazardous waste (farligt avfall) | 1,263 | Tabell 34 | Oils, e-waste, contaminated materials |
| **Total external handling** | **83,654** | | |

### Additional Material Flows (not counted as external waste)

| Category | Tonnes | Notes |
|----------|-------:|-------|
| Residual products - internally reused | 722,100 | Recirculated in production (Tabell 31) |
| By-products sold externally | 465,500 | Slag (314 kt), pig iron (69 kt), coke fines (51 kt) (Tabell 32) |
| Total residual products generated | 770,700 | Dry weight basis |

### Interpretation

The allocation model over-estimates waste by approximately 9%, which is reasonable given:
1. The model uses emissions (CO2, NOx, PM10) as a proxy for waste generation
2. Some residual products may be classified differently in statistical reporting vs. environmental permits
3. The reported figure excludes internally recycled materials

**Conclusion:** The emission-based allocation methodology provides a reasonable estimate of facility-level waste generation for SSAB Luleå.

---

## SSAB Oxelösund - PENDING

**Facility ID:** SE.CAED/10027326.Installation
**Allocated:** 100,410 tonnes
**IED Activity:** 2.2 (Production of pig iron or steel)

### Data Sources Identified
- Naturvårdsverket permit page: https://www.naturvardsverket.se/lagar-och-regler/provningsarenden/metallindustri/ssab-oxelosund/
- Site-specific miljörapport: Not found publicly (may need to request from SSAB or Länsstyrelsen)

### Historical Reference
- Target (2017): Reduce waste to landfill by 10,000 tonnes/year
- Progress: More than half achieved as of 2017

---

## Outokumpu Tornio - PENDING

**Facility ID:** http://paikkatiedot.fi/so/1002031/pf/ProductionInstallation/0000006078.ProductionInstallation
**Allocated:** 121,274 tonnes
**IED Activity:** 2.2 (Steel production)

### Data Sources Identified
- Waste management procedure: https://otke-cdn.outokumpu.com/-/media/files/locations/tornio/environment/
- Hietainpää hazardous waste landfill on site
- Finnish ympäristöraportti needed for validation

---

## Outokumpu Avesta - PENDING

**Facility ID:** SE.CAED/10034478.Installation
**Allocated:** 95,089 tonnes
**IED Activity:** 2.2 (Steel production)

### Data Sources Identified
- Swedish emissions register: https://utslappisiffror.naturvardsverket.se/Sok/Anlaggningssida/?pid=3493
- No waste data reported publicly in register
- Site-specific miljörapport needed for validation

---

## Methodology Notes

### Allocation Model
The `facility_waste_allocated.csv` dataset allocates national waste generation statistics to individual IED facilities using:
- Emissions data (CO2, NOx, PM10) as activity proxies
- Weighted combination of emission shares
- NACE sector matching

### Validation Approach
1. Identify site-specific environmental reports (miljörapporter/ympäristöraportit)
2. Extract waste data from official tables
3. Sum waste categories requiring external handling (landfill + external recycling + general waste + hazardous)
4. Compare to allocated tonnes

### Limitations
- By-products sold externally (e.g., slag) may or may not be included in statistical waste reporting
- Internally recycled materials are excluded from external waste totals
- Report years may not perfectly align with allocation data years

---

## Data Files

| File | Description |
|------|-------------|
| `data/processed/facility_waste_allocated.csv` | Emission-based waste allocation |
| `data/processed/validated_company_waste.csv` | Extracted validation data with sources |
| `data/processed/correlation_report.csv` | Validation summary |
| `src/analysis/validation_correlation.py` | Analysis script |

---

*Generated: 2026-01-21*
