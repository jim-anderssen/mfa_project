# Databases for Waste Quantification & Secondary Raw Materials

Compiled: 2026-01-14

## European/EU Official Statistics

### Eurostat Waste Database
- **URL**: https://ec.europa.eu/eurostat/web/waste/database
- **Coverage**: Waste generation, treatment, recovery by NACE sector and waste type across EU
- **Resolution**: Country-level (NUTS 0)
- **Key datasets**:
  - `env_wasgen` - Waste generation by economic activity
  - `env_wastrt` - Waste treatment
  - `env_wasfac` - Recovery and disposal facilities
  - `env_wasoper` / `env_wasflow` - Waste management indicators
  - `env_wassd` - Sankey diagram data for circular economy
- **Format**: Downloadable via API, bulk download
- **Notes**: 2,317 million tonnes total EU waste (2018)

### Eurostat PRODCOM (ds-059359)
- **URL**: https://ec.europa.eu/eurostat/web/prodcom/database
- **Coverage**: Production of ~4,000 manufactured goods
- **Resolution**: Country-level (NUTS 0)
- **NACE Sections**: B (Mining), C (Manufacturing), E (Materials recovery 38.32)
- **Relevant codes**:
  - 23.51 - Cement (incl. slag cement)
  - 24.10 - Basic iron and steel (incl. slag)
  - 38.32 - Materials recovery / secondary raw materials
- **Use case**: Estimate byproduct generation using production volumes + coefficients

### Eurostat Material Flow Accounts
- **URL**: https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Circular_economy_-_material_flows
- **Coverage**: Economy-wide material flows, circular material use rate
- **Key indicators**:
  - Sankey diagram of EU material flows
  - Circular material use rate (CMU)

### E-PRTR / Industrial Emissions Portal
- **URL**: https://www.eea.europa.eu/data-and-maps/data/member-states-reporting-art-7-under-the-european-pollutant-release-and-transfer-register-e-prtr-regulation-23
- **Coverage**: Facility-level pollutant releases and waste transfers
- **Resolution**: Facility-level (point data with coordinates)
- **Activities**: 65 industrial activities in Annex I
- **Pollutants**: 91 pollutants
- **Format**: Microsoft Access database, text files
- **Notes**: Being replaced by Industrial Emissions Portal Regulation (IEPR)

### IED Installations Database
- **URL**: Via EEA reporting
- **Coverage**: Installations under Industrial Emissions Directive 2010/75/EU
- **Resolution**: Facility-level with coordinates
- **Key fields**: IED Annex I activity codes, BAT conclusions, permit info
- **Use case**: Allocate national production to facility locations

---

## Industry-Specific Databases

### EUROSLAG (European Slag Association)
- **URL**: https://www.euroslag.com (statistics via Global Slag)
- **Coverage**: European ferrous slag production and utilization
- **Key statistics**:
  - ~45 Mt/year ferrous slag in EU
  - 29.7 Mt used in building materials (2023)
  - 20.3 Mt granulated blast furnace slag (68%)
  - 9.4 Mt steelwork slag (32%)
- **Notes**: 99% utilization rate

### USGS Iron and Steel Slag Statistics
- **URL**: https://www.usgs.gov/centers/national-minerals-information-center/iron-and-steel-slag-statistics-and-information
- **Coverage**: US and global slag production, consumption, trade
- **Format**: PDF reports (1994-2025), XLS data tables (2002-2021)
- **Included in**: Mineral Commodity Summaries (annual)

### USGS Minerals Yearbook
- **URL**: https://www.usgs.gov/centers/national-minerals-information-center/minerals-yearbook-metals-and-minerals
- **Coverage**: ~90 mineral commodities including industrial byproducts
- **Historical data**: Since 1900

---

## International Trade Databases

### UN Comtrade
- **URL**: https://comtrade.un.org/ / https://comtradeplus.un.org/TradeFlow
- **Coverage**: Global trade statistics from 1962
- **Relevant HS codes**:
  - HS 26 - Ores, slag and ash
  - HS 2620 - Slag and ash nes
  - HS 3915 - Plastic waste
- **Resolution**: Country-level bilateral trade
- **Notes**: EU imports of ores/slag/ash: $28.27B (2024)

### OECD Transboundary Movements of Waste
- **URL**: https://www.oecd.org/en/data/tools/transboundary-movements-of-waste.html
- **Coverage**: Waste movements for recovery between OECD countries
- **Content**: Competent authorities, pre-consented facilities, waste codes
- **Updated**: July 2025

### Basel Convention
- **URL**: https://www.basel.int/
- **Coverage**: Hazardous waste transboundary movements (190 countries)
- **Notes**: ~400 million tonnes hazardous waste generated annually

---

## Circular Economy & Secondary Materials

### Eurostat Circular Economy Indicators
- **URL**: https://ec.europa.eu/eurostat/web/circular-economy/information-data
- **Key indicators**:
  - Circular material use rate (CMU)
  - Recycling rates by material
  - Trade in recyclable raw materials

### Organic Matter Database (OMD)
- **URL**: https://essd.copernicus.org/articles/17/369/2025/
- **Coverage**: Global residue data from agriculture, fisheries, forestry
- **Reference**: Weldesemayat Sileshi et al. (2025), Earth Syst. Sci. Data

### NIST Circular Economy Program
- **URL**: https://www.nist.gov/circular-economy
- **Focus**: Data frameworks for secondary materials quality/performance
- **Notes**: Developing standards for data consistency in recycling

---

## Key Statistics Summary

| Material | Annual Generation | Source |
|----------|------------------|--------|
| EU total waste | 2,317 Mt (2018) | Eurostat |
| EU ferrous slag | ~45 Mt/year | EUROSLAG |
| Global industrial waste | ~3.5 Bt (China: 30%) | Literature |
| Steel industry waste | 2-4 t per tonne steel | Literature |
| EU BF slag (2018) | 20.7 Mt | EUROSLAG |
| EU steelworks slag (2018) | 16.3 Mt | EUROSLAG |
| Global hazardous waste | ~400 Mt/year | Basel Convention |

---

## Waste Generation Factors (Literature)

| Industry | Waste Factor | Type |
|----------|-------------|------|
| Steel production | 0.12-0.15 t slag/t steel | Slag |
| Steel production | 2-4 t total waste/t steel | Mixed |
| Alumina production | 1.5 t red mud/t alumina | Red mud |
| Coal power | 0.10 t ash/t coal | Fly/bottom ash |
| Coal power | 0.03 t FGD sludge/t coal | FGD sludge |

---

## Data Access Notes

### APIs
- Eurostat: REST API with JSON/SDMX output
- UN Comtrade: API with registration required

### Bulk Downloads
- Eurostat: TSV, SDMX-CSV
- E-PRTR: MS Access, CSV
- USGS: PDF, XLS

### Python Libraries
- `eurostat` - Python package for Eurostat data
- `pandas-datareader` - General data access
- `comtradeapicall` - UN Comtrade API wrapper
