# MRIO Database Comparison for MFA Project

Date: 2026-01-16

## Overview

Comparison of seven major Multi-Regional Input-Output (MRIO) databases for potential integration with the European waste MFA project.

## Database Summaries

### 1. Eora MRIO

**Coverage**
- 190 countries
- Time period: 1995-2015
- 163 sectors (Full Eora) or 26 sectors (Eora26)

**Structure**
- Mixed CIOT/IIOT/SUT tables
- 5 margins: basic prices, trade margin, transport margin, taxes, subsidies
- Environmental and social satellite accounts

**Relevance to Project**
- High geographic and sector resolution
- ⚠️ Data ends at 2015 (outdated)
- Environmental satellites available

**Sources**
- [Eora Global MRIO](https://worldmrio.com/)
- [Full Eora](https://worldmrio.com/eora/)
- [Eora26](https://worldmrio.com/eora26/)

---

### 2. GTAP (Global Trade Analysis Project)

**Coverage**
- 141 countries + 19 aggregate regions (99.1% of world GDP)
- Time series: 2004, 2007, 2011, 2014, 2017
- 65 sectors

**Structure**
- Standard MRIO supplemented by macroeconomic data
- GTAP-MRIO extension: bilateral trade by end-users (firms, households, government, investors)
- Extensive satellite datasets: trade policies, GHG emissions, energy, migration, land use

**Relevance to Project**
- Trade-focused database
- Limited waste-specific extensions
- Regular updates from Purdue University

**Sources**
- [GTAP Homepage](https://www.gtap.agecon.purdue.edu/)
- [GTAP-MRIO paper](https://www.tandfonline.com/doi/abs/10.1080/09535314.2012.761953)

---

### 3. OECD ICIO (Inter-Country Input-Output)

**Coverage**
- 80 economies (38 OECD + 42 non-OECD + Rest of World)
- Time period: 1995-2022
- Latest release: 2025 edition (October 2025)
- Extended ICIO splits China and Mexico to account for firm heterogeneity

**Structure**
- Standard IO tables following SNA 2008
- Enhanced sectoral detail:
  - Agriculture and Mining expanded to 2-digit ISIC Divisions
  - **Manufacture of basic metals split into iron/steel vs non-ferrous metals** ⭐
  - Building of ships and boats separated from other transport equipment

**Relevance to Project**
- Most recent official data (2022)
- **Excellent for C24/C25 metal sector analysis** (iron/steel vs non-ferrous split)
- High-quality, regularly updated
- Limited environmental/waste extensions

**Sources**
- [OECD ICIO Homepage](https://www.oecd.org/en/data/datasets/inter-country-input-output-tables.html)
- [2025 Edition Documentation](https://stats.oecd.org/wbos/fileview2.aspx?IDFile=a9868f6c-31ed-4943-95cd-6c42afa2c2a9)

---

### 4. WIOD (World Input-Output Database)

**Coverage**
- 43 countries + Rest of World
- Time period: 2000-2014
- Latest release: 2016
- 56 sectors (ISIC Rev. 4)
- Long-run version available: 1965-2000 (23 sectors, ISIC Rev. 3.1)

**Structure**
- Standard IO tables (SNA 2008)
- Supplementary data: labor inputs, capital inputs, pollution indicators

**Relevance to Project**
- ⚠️ Outdated (data through 2014 only)
- Moderate environmental extensions
- Covers >85% of world GDP

**Sources**
- [WIOD Homepage](https://www.rug.nl/ggdc/valuechain/wiod/?lang=en)
- [WIOD Contents Paper](https://www.rug.nl/ggdc/valuechain/wiod/papers/wiod10.pdf)

---

### 5. EXIOBASE ⭐ TOP CHOICE

**Coverage**
- 44 countries: 28 EU members + 16 major economies + 5 Rest of World regions
- Time series: 1995 to recent years
- 163 industries × 200 products

**Structure**
- Rectangular Supply-Use Tables (SUT)
- Extensive environmentally-extended MR-IOT (EE MRIO)
- **Multiple waste processing sectors included**
- Physical trade data (imports/exports by material)

**Waste & Material Flow Capabilities** ⭐⭐⭐
- Explicit waste processing sectors
- **Recycling rate calculations**
- **Material flow indicators (DMC - Domestic Material Consumption)**
- Direct physical imports/exports for material flow accounting
- Detailed waste data for specific indicators

**Relevance to Project**
- **HIGHEST RELEVANCE** - purpose-built for environmental/waste analysis
- Excellent EU coverage (28 countries)
- 163 industries allow detailed C24/C25 metal sector analysis
- Compatible with Eurostat classifications
- ⚠️ Country-level only (not NUTS2) - requires combination with existing NUTS2 allocation methods

**Sources**
- [EXIOBASE Homepage](https://www.exiobase.eu/)
- [EXIOBASE 3 Paper](https://onlinelibrary.wiley.com/doi/10.1111/jiec.12715)
- [Zenodo Repository](https://zenodo.org/records/5589597)
- Contact: exiobase-support@googlegroups.com

---

### 6. EMERGING

**Coverage**
- 245 economies (focus on emerging markets)
- 135 sectors
- Time period: 2015-2019 (2020-2022 in testing phase)

**Structure**
- Standard MRIO
- High-quality official data from national statistical institutes
- Freely accessible through CEADs platform

**Relevance to Project**
- ⚠️ Low relevance - focuses on emerging economies, not Europe
- Better emerging economy coverage than other databases
- Limited time series

**Sources**
- [EMERGING Paper](https://onlinelibrary.wiley.com/doi/10.1111/jiec.13264)
- [CEADs Platform](https://www.ceads.net/news/20221276.html)

---

### 7. GLORIA (Global Resource Input-Output Assessment)

**Coverage**
- 164 countries
- 120 sectors (homogenous classification across all countries)
- Time period: 1990-2024
- 19,680 region-category combinations
- Transaction matrix: >385 million elements

**Structure**
- Homogenous multi-regional supply-use table (MR-SUT)
- Identical sector labels for industry and commodity sectors
- Environmental and social satellite accounts
- Powers the SCP-HAT (Sustainable Consumption & Production - Hotspots Analysis Tool)

**Relevance to Project**
- Most current data available (through 2024)
- ⚠️ 2019-2024 environmental data mostly forecasted
- High resolution (120 sectors × 164 countries)
- Environmental focus suitable for sustainability assessments
- Country-level only (not NUTS2)

**Sources**
- [GLORIA Technical Documentation](https://scp-hat.org/wp-content/uploads/2021/11/Technical-Documentation_GLORIA_20210913.pdf)
- [GLORIA MRIO Info](https://ielab.info/resources/gloria/about)
- [SCP-HAT Methods](https://scp-hat.org/methods/)

---

## Comparison Matrix

| Database | Countries | Sectors | Latest Year | Waste Focus | EU Detail | Metal Sectors | Updates |
|----------|-----------|---------|-------------|-------------|-----------|---------------|---------|
| **EXIOBASE** | 44 | 163×200 | Recent | ⭐⭐⭐ | 28 EU | High | Active |
| **GLORIA** | 164 | 120 | 2024 | ⭐⭐ | Medium | Medium | Active |
| **OECD ICIO** | 80 | Varied | 2022 | ⭐ | Good | ⭐⭐⭐ | Annual |
| **Eora** | 190 | 163/26 | 2015 | ⭐ | Medium | Medium | Inactive |
| **GTAP** | 141+19 | 65 | 2017 | ⭐ | Limited | Low | Periodic |
| **WIOD** | 43 | 56 | 2014 | ⭐ | Good | Low | Inactive |
| **EMERGING** | 245 | 135 | 2019 | ⭐ | Low | Medium | Active |

---

## Recommendations for MFA Project

### Primary Recommendation: EXIOBASE 3

**Rationale**
1. **Only database with explicit waste processing sectors** - directly addresses project needs
2. **Built-in recycling rate calculations** - aligns with recovery technology investment focus
3. **Material flow indicators (DMC)** - supports material flow analysis methodology
4. **Strong EU coverage** - 28 EU countries at national level
5. **High sectoral detail** - 163 industries enable detailed C24/C25 metal sector analysis
6. **Compatible with Eurostat** - uses similar classification systems

**Implementation Strategy**
- Use EXIOBASE for waste coefficients and environmental linkages
- Maintain Eurostat (env_wasgen, env_wastrt, env_wasship) as primary data source
- Apply EXIOBASE waste/material ratios to NUTS2 allocations using SBS proxy data
- Leverage EXIOBASE recycling rates for technology investment potential analysis

**Limitation to Address**
- Country-level resolution only (not NUTS2)
- **Solution**: Apply EXIOBASE coefficients to existing NUTS2 allocation methodology using SBS employment/turnover proxies

---

### Secondary Recommendation: GLORIA

**Rationale**
1. Most current data (through 2024)
2. High resolution (120 sectors × 164 countries)
3. Environmental satellite accounts
4. Continuous time series 1990-2024

**Use Case**
- Temporal trend analysis
- Validation of EXIOBASE-derived coefficients
- Recent data for scenario projections

**Limitations**
- Less explicit waste sector detail than EXIOBASE
- 2019-2024 environmental data partially forecasted
- Country-level only

---

### Tertiary Recommendation: OECD ICIO

**Rationale**
1. Most recent official data (2022)
2. **Iron/steel vs non-ferrous metals separation** - perfect for C24/C25 analysis
3. High-quality, officially maintained
4. Regular annual updates

**Use Case**
- Metal flow validation and cross-checking
- Trade flow analysis for transboundary shipments
- Official statistics for reporting

**Limitations**
- Limited environmental/waste extensions
- Fewer sectors than EXIOBASE or GLORIA
- Not waste-focused

---

## Integration Approach

### Proposed Multi-Database Strategy

1. **Foundation: Eurostat Data**
   - env_wasgen (waste generation by NACE/waste type)
   - env_wastrt (treatment operations)
   - env_wasship (transboundary movements)
   - sbs_r_nuts06_r2 (NUTS2 economic activity)
   - Maintains NUTS2 resolution and direct EU policy relevance

2. **Enhancement Layer: EXIOBASE**
   - Waste processing coefficients by sector
   - Material flow ratios (input-output of materials per industry)
   - Recycling rates by waste stream
   - Environmental linkages (emissions, resource use per sector)

3. **Validation Layer: OECD ICIO**
   - Metal flow validation (C24/C25)
   - Trade flow cross-checking
   - Official statistics benchmark

4. **Temporal Extension: GLORIA**
   - Recent data (2020-2024) for projections
   - Long time series (1990-2024) for trend analysis

### Technical Implementation

```
NUTS2 Waste Allocation = Eurostat NUTS0 waste × (NUTS2 SBS proxy / Country SBS total)
                        × EXIOBASE sector coefficients
                        × EXIOBASE waste treatment ratios

Where:
- Eurostat provides base quantities (NUTS0, by NACE, by waste type)
- SBS provides geographic distribution (NUTS2 employment/turnover)
- EXIOBASE provides waste generation/treatment coefficients per economic activity
- OECD ICIO validates metal flows
- GLORIA extends temporal coverage
```

---

## Next Steps

1. **Data Acquisition**
   - [ ] Download EXIOBASE 3 latest version from Zenodo
   - [ ] Access OECD ICIO 2025 edition
   - [ ] Explore GLORIA access through SCP-HAT or direct contact

2. **Methodology Development**
   - [ ] Map EXIOBASE sectors to NACE2 codes
   - [ ] Extract waste processing coefficients from EXIOBASE
   - [ ] Develop integration script for EXIOBASE + Eurostat + SBS

3. **Validation**
   - [ ] Compare EXIOBASE metal flows vs OECD ICIO
   - [ ] Validate waste balances: Generation = Treatment + Export - Import + Stock
   - [ ] Check consistency with current NUTS2 allocation results

4. **Analysis Enhancement**
   - [ ] Calculate material circularity indicators using EXIOBASE
   - [ ] Identify recovery technology potential using recycling rates
   - [ ] Enhance transboundary shipment analysis with supply chain linkages

---

## References

### EXIOBASE
- Stadler, K., Wood, R., Bulavskaya, T., et al. (2018). EXIOBASE 3: Developing a Time Series of Detailed Environmentally Extended Multi‐Regional Input‐Output Tables. Journal of Industrial Ecology.
- https://www.exiobase.eu/
- https://zenodo.org/records/5589597

### GLORIA
- Technical Documentation: https://scp-hat.org/wp-content/uploads/2021/11/Technical-Documentation_GLORIA_20210913.pdf
- https://ielab.info/resources/gloria/about

### OECD ICIO
- Development of the OECD Inter Country Input-Output Database 2023
- https://www.oecd.org/en/data/datasets/inter-country-input-output-tables.html

### Other Databases
- Eora: https://worldmrio.com/
- GTAP: https://www.gtap.agecon.purdue.edu/
- WIOD: https://www.rug.nl/ggdc/valuechain/wiod/
- EMERGING: https://www.ceads.net/news/20221276.html
