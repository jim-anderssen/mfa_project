# Ecoinvent and LCI Databases for Waste Quantification

## Overview

Life Cycle Inventory (LCI) databases provide process-level data on material inputs, outputs, emissions, and waste generation. These are valuable for deriving waste generation coefficients and transfer factors.

---

## Ecoinvent Database

### General Information
- **Provider**: ecoinvent Association (Swiss non-profit)
- **URL**: https://ecoinvent.org/
- **Current version**: 3.12 (as of 2024)
- **Size**: ~18,000+ datasets
- **Cost**: Commercial license required (free for non-OECD countries)
- **Format**: EcoSpold2 (XML), Excel exports

### Sectors Covered
- Energy supply
- Metals (iron, steel, aluminium, copper, zinc, etc.)
- Chemicals and plastics
- Building and construction
- Agriculture
- Transport
- Pulp and paper
- **Waste management** (2,500+ datasets)
- Textiles
- Forestry and wood

### Data Structure

Each **Unit Process (UPR)** contains:
```
Inputs:
  - Raw materials (kg)
  - Energy (kWh, MJ)
  - Water (kg)
  - Intermediate products from other processes

Outputs:
  - Reference product (functional unit, e.g., 1 kg steel)
  - By-products (kg)
  - Emissions to air/water/soil (kg)
  - Waste for treatment (kg)
```

### Relevant Data for Waste Quantification

#### Metals Sector
| Process | Reference | Slag Output | Notes |
|---------|-----------|-------------|-------|
| Pig iron production | 1 kg pig iron | 0.25-0.30 kg BF slag | Blast furnace |
| Steel (converter) | 1 kg steel | 0.10-0.15 kg steel slag | BOF route |
| Steel (EAF) | 1 kg steel | ~0.15 kg EAF slag | Electric arc |
| GGBFS production | 908.5 kg molten slag | 907.2 kg GGBFS | Granulation process |

#### Waste Treatment Sector
- Municipal solid waste incineration
- Hazardous waste incineration
- Sanitary landfills
- Residual material landfills
- Open burning/dumping (developing countries)
- Wastewater treatment
- Composting and anaerobic digestion

### System Models

| Model | Allocation Approach | Use Case |
|-------|---------------------|----------|
| **Cut-off** | Burden-free recyclables | Most common |
| **APOS** | Substitution for by-products | Credit for recycling |
| **Consequential** | Market-based substitution | Policy analysis |
| **EN15804** | Construction product EPDs | Building sector |

### Access Methods

1. **ecoQuery** (web interface): https://ecoquery.ecoinvent.org/
2. **LCA Software**: SimaPro, GaBi, openLCA, Umberto
3. **Python API** (unofficial): `ecoinvent_interface` library
4. **Bulk download**: EcoSpold2 XML files

---

## Doka LCA Waste Treatment Tools

### Overview
Free Excel-based tools for calculating waste-specific LCI data using transfer coefficients.

- **Website**: https://www.doka.ch/publications.htm
- **License**: GNU Public License (open source)
- **Format**: Excel with EcoSpold1/2 export

### Available Tools

| Tool | Application |
|------|-------------|
| **Municipal waste incineration** | MSWI with transfer coefficients |
| **Hazardous waste incineration** | HWI with element tracking |
| **Sanitary landfill** | MSW landfilling |
| **Residual material landfill** | Ash, slag disposal |
| **Wastewater treatment** | Element fate modeling |
| **Open burning** | Developing country scenarios |
| **Open dumps** | Unsanitary landfilling |
| **Tailings impoundments** | Mining waste |

### Transfer Coefficient Approach

```
Emission = Waste_composition × Transfer_coefficient

Example for incineration:
- Cd in waste: 10 mg/kg
- TK (Cd to fly ash): 0.85
- TK (Cd to air): 0.001
- Cd in fly ash = 10 × 0.85 = 8.5 mg/kg waste
- Cd to air = 10 × 0.001 = 0.01 mg/kg waste
```

Covers **41 chemical elements** with specific transfer coefficients for each treatment type.

### Key Reference
> Doka G. (2003) Life Cycle Inventories of Waste Treatment Services.
> ecoinvent report No. 13, Swiss Centre for Life Cycle Inventories.

---

## Alternative LCI Databases

### Commercial

| Database | Provider | Datasets | Notes |
|----------|----------|----------|-------|
| **GaBi** | Sphera | ~15,000 | Industry-focused |
| **IDEA** | AIST (Japan) | 4,000+ | Japanese industry |
| **AusLCI** | ALCAS | 1,000+ | Australian focus |

### Free / Open Source

| Database | Provider | Access |
|----------|----------|--------|
| **USLCI** | NREL (US) | https://www.lcacommons.gov/ |
| **ELCD** | EU JRC | Discontinued 2019 |
| **IMPACTS** | ADEME (France) | French industry |
| **Agribalyse** | ADEME | Agriculture/food |
| **openLCA Nexus** | GreenDelta | Repository of multiple DBs |

### Free Waste-Specific Tools

| Tool | Provider | URL |
|------|----------|-----|
| **EPA WARM** | US EPA | https://www.epa.gov/warm |
| **ecoinvent Wastewater Tool** | ecoinvent | Free web tool |
| **Solid Waste Treatment Tools** | ecoinvent | Free spreadsheets |

---

## Process Efficiency Coefficients from Literature

### Steel Production

| Process | Input | Output | Waste/By-product | Factor |
|---------|-------|--------|------------------|--------|
| Blast furnace | Iron ore + coke | Pig iron | BF slag | 0.25-0.30 kg/kg |
| BOF converter | Pig iron + scrap | Steel | BOF slag | 0.10-0.15 kg/kg |
| Electric arc furnace | Scrap | Steel | EAF slag | 0.10-0.20 kg/kg |
| Rolling mill | Steel billet | Rolled steel | Mill scale | 0.02-0.03 kg/kg |

### Non-Ferrous Metals

| Process | Output | Waste | Factor |
|---------|--------|-------|--------|
| Alumina (Bayer) | Alumina | Red mud | 1.0-2.5 kg/kg alumina |
| Aluminium smelting | Al metal | Spent potlining | 0.02 kg/kg |
| Copper smelting | Cu | Slag | 2.0-3.0 kg/kg Cu |
| Zinc (ISF) | Zn | Slag | 0.8-1.2 kg/kg Zn |

### Combustion

| Fuel | Ash Content | FGD Sludge |
|------|-------------|------------|
| Hard coal | 8-15% | 3-5% of coal |
| Lignite | 5-30% | 2-4% of coal |
| Biomass | 1-5% | - |

### Cement & Minerals

| Process | By-product | Notes |
|---------|------------|-------|
| Cement clinker | CKD (cement kiite dust) | 2-8% of clinite |
| Glass melting | Cullet loss | 1-3% |

---

## Using Ecoinvent for Waste Quantification

### Workflow

1. **Identify relevant processes** in ecoinvent by NACE/ISIC code
2. **Extract waste outputs** from unit process data
3. **Calculate waste factors** (kg waste / kg product)
4. **Apply to production data** (PRODCOM volumes)

### Example: Steel Slag Estimation

```python
# From ecoinvent data
slag_factor_bof = 0.12  # kg slag / kg steel (BOF)
slag_factor_eaf = 0.15  # kg slag / kg steel (EAF)

# From PRODCOM
steel_production_bof = 100_000_000  # kg/year (country)
steel_production_eaf = 50_000_000   # kg/year (country)

# Estimate slag generation
slag_bof = steel_production_bof * slag_factor_bof  # 12,000 t
slag_eaf = steel_production_eaf * slag_factor_eaf  # 7,500 t
```

### Limitations

- **Aggregated data**: Some processes are averaged across technologies
- **Geographic coverage**: Mainly Europe, some global datasets
- **Temporal**: Data may be 5-10 years old
- **By-product allocation**: Depends on system model choice
- **Cost**: Full database requires license (~€2,000-4,000/year)

---

## Recommendations for Your Project

### For Waste Generation Factors
1. Use **Doka LCA tools** (free) for waste treatment modeling
2. Cross-reference with **ecoinvent** metals sector data
3. Validate against **USGS** and **EUROSLAG** statistics

### For Transfer Coefficients
1. **Doka incineration/landfill tools** - element-specific TKs
2. **EPA WARM** - material-specific emission factors
3. **Literature** - process engineering handbooks

### Open Source Workflow
```
PRODCOM (production)
    × ecoinvent factors (waste/product)
    × Doka TK (element fate)
    = Waste generation + composition estimates
```

---

## Data Access Summary

| Resource | Cost | Best For |
|----------|------|----------|
| ecoinvent | €2-4k/year | Comprehensive LCI data |
| Doka tools | Free | Waste treatment TKs |
| USLCI | Free | US processes |
| openLCA | Free software | Database integration |
| EPA WARM | Free | Quick waste emission factors |

---

## References

- Doka G. (2003) Life Cycle Inventories of Waste Treatment Services. ecoinvent report No. 13.
- Classen M. et al. (2009) Life Cycle Inventories of Metals. ecoinvent report No. 10.
- Wernet G. et al. (2016) The ecoinvent database version 3. Int J Life Cycle Assess 21:1218–1230.
- https://ecoinvent.org/
- https://www.doka.ch/publications.htm
- https://nexus.openlca.org/
