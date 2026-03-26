# Industrial Ecology Data Commons (IEDC) - Database Guide

## Overview

The Industrial Ecology Data Commons (IEDC) is a research database maintained by the University of Freiburg containing structured data for industrial ecology and socio-metabolic research.

- **URL**: https://www.database.industrialecology.uni-freiburg.de/
- **GitHub**: https://github.com/IndEcol/IE_data_commons
- **Tools**: https://github.com/IndEcol/IEDC_tools

## Database Scale

| Metric | Value |
|--------|-------|
| Total datasets | 320+ |
| Data points | 3.2+ million |
| Source publications | ~250 journal papers |
| Data types | 30+ in 8 categories |

### Included Data Sources
- Yale Stocks and Flows Database (YSTAFDB)
- Metabolism of Cities database
- UNEP IRP MFA database
- EUROSTAT circular economy indicators
- ~40 journal papers, 15 government datasets

---

## Data Types

### Core Data Type Codes

| Code | Data Type | Description |
|------|-----------|-------------|
| **1_F** | Flows | Material and energy flows between processes |
| **2_S** | Stocks | In-use stocks of materials in products/infrastructure |
| **3_MC** | Material Composition | Material content of products (e.g., steel in vehicles) |
| **4_LT** | Lifetimes | Product lifetime distributions |
| **5_YF** | Yield Factors | Process efficiency and yield rates |
| **6_PI** | Process Inventories | Input/output data for industrial processes |

### How to Access Data Types
1. Go to the [search interface](https://www.database.industrialecology.uni-freiburg.de/)
2. Enter the data type code (e.g., `1_F`, `3_MC`) in the search field
3. Filter by classification items (regions, materials, years)
4. Preview and download datasets

---

## Classifications

The IEDC uses standardized classification systems:

| Classification | Code | Description | MFA Project Equivalent |
|---------------|------|-------------|------------------------|
| Regions | `regions_iso_iedc` | ISO country codes | Country codes (allocate to NUTS-2) |
| Materials/Waste | `generic_materials_waste` | Material categories | EWC-Stat codes |
| Industry Groups | `broad_industry_groups` | Industrial sectors | NACE codes |
| Time | `time` | Years | Year-based analysis |
| Products | `general_product_categories` | Product types | Product categories |
| Chemical Elements | `chemical_elements` | Periodic table elements | Material composition |

---

## Key Datasets for MFA Project

### High Priority

#### 1. Steel In-Use Stocks
- **Size**: 63,565 data points
- **Dimensions**: 4 product groups x 146 countries x 109 years
- **Source**: Pauliuk et al. (2013) "Steel all over the world"
- **Use case**: Predict future metal waste volumes from product end-of-life

#### 2. Material Composition Data (3_MC)
- **Content**: Material content of products by type
- **Coverage**: Vehicles, buildings, appliances, infrastructure
- **Use case**: Improve recycling potential indices for specific waste types

### Medium Priority

#### 3. Product Lifetimes (4_LT)
- **Content**: Distribution of product lifetimes by category
- **Use case**: Model waste generation timing

#### 4. Process Yield Factors (5_YF)
- **Content**: Industrial process efficiency data
- **Use case**: Refine allocation beyond employment-based proxies

#### 5. EUROSTAT Circular Economy Indicators
- **Content**: EU-level CE metrics
- **Use case**: Benchmarking and validation

---

## Integration with MFA Project

### Alignment with Existing Pipeline

| IEDC Data | Integration Point | File |
|-----------|------------------|------|
| Country-level flows | Allocation input | `src/nuts2/allocation.py` |
| Material composition | Recycling potential refinement | `src/nuts2/clustering.py` |
| Stock data | Future waste modeling | New analysis |
| EUROSTAT indicators | Validation metrics | `src/nuts2/data_loader.py` |

### Data Format

IEDC datasets are available in a common file format with:
- Multidimensional array structure
- Dimensions: time, region, process, commodity, material, scenario
- Metadata including source publication and uncertainty

---

## Programmatic Access

### Python Tools

```python
# Install IEDC tools
pip install iedc-tools

# Or clone from GitHub
git clone https://github.com/IndEcol/IEDC_tools.git
```

### ODYM Framework
For dynamic material systems modeling:
```python
# https://github.com/IndEcol/ODYM
pip install odym
```

---

## Detailed Data Type Exploration

### 3_MC: Material Composition Data

Material composition datasets describe the material content of products, enabling better understanding of what materials will become waste when products reach end-of-life.

#### Vehicle Material Composition
- **Source**: JRC (Joint Research Centre) datasets
- **Coverage**: Passenger vehicles including EVs, ICE vehicles
- **Materials**: Steel, aluminium, copper, plastics, battery materials, CRMs
- **Components**: 9+ components including battery management, motors, power electronics
- **Elements**: 16 chemical elements tracked
- **Link**: [JRC Material Composition Trends](https://rmis.jrc.ec.europa.eu/uploads/library/JRC126564%20Material%20Composition%20Trends%20in%20vehicles.pdf)

#### Consumer Electronics Material Composition
- **Source**: Figshare open dataset
- **Coverage**: 25 consumer electronic product categories
- **Data**: Total mass and mass percent by material for all products
- **Format**: Two workbooks (disassembly data + bill of materials)
- **License**: CC0 (public domain)
- **Link**: [Consumer Electronics Dataset](https://figshare.com/articles/dataset/Material_composition_of_consumer_electronics/11306792/1)

#### Buildings Material Composition
- **Coverage**: Profiles, flooring, pipes, insulation, cables, films
- **Materials**: Plastics, concrete, steel, glass, insulation materials
- **Application**: Predict future construction & demolition waste

### 2_S: Stock Data

In-use stock data quantifies materials currently in products and infrastructure.

#### Global Steel Stocks
- **Size**: 63,565 data points
- **Dimensions**: 4 product groups × 146 countries × 109 years
- **Source**: Pauliuk et al. (2013)
- **Key finding**: 60-80% of global steel production goes to stock expansion

#### Stock-Flow Dynamics
- Material demand from growing stocks must come from primary production
- Recycling primarily replaces products, not stock growth
- Critical for understanding future secondary material availability

### 4_LT: Product Lifetimes

Product lifetime distributions are essential for predicting when products become waste.

#### 2025 Focus Areas (IEDC Critical Mass Sprint)
- Appliances
- Buildings
- Vehicles
- Infrastructure
- Industrial assets
- Energy system technologies

#### Application
- Model delayed waste generation from long-lived products
- Essential for plastics in buildings (decades of use before becoming waste)

### 5_YF: Yield Factors

Process yield factors describe material efficiency in industrial processes.

#### Coverage
- Mining and extraction yields
- Manufacturing efficiency
- Recycling recovery rates
- Remelting losses

### Related Tools and Frameworks

#### ODYM (Open Dynamic Material Systems Model)
- **URL**: https://github.com/IndEcol/ODYM
- **Documentation**: https://odym.readthedocs.io/
- **Purpose**: Dynamic material flow analysis framework in Python
- **Capabilities**:
  - Products, components, materials, alloys, waste, chemical elements
  - Lifetime models with uncertainty
  - Mass-balanced framework for material cycles

#### ODYM-RECC Model Results
- **Dataset**: [Zenodo - Global Scenarios](https://zenodo.org/records/4698619)
- **Scope**: Global residential buildings and passenger vehicles
- **Variables**: Material use, energy consumption, GHG emissions
- **Size**: 717 MB
- **License**: CC-BY 4.0

### Waste-Specific Data Opportunities

| Waste Stream | Relevant IEDC Data | Potential Use |
|--------------|-------------------|---------------|
| Metal waste (W061) | Steel/aluminium stocks, composition | Predict scrap availability by region |
| Plastic waste (W12A) | Plastics in buildings, vehicles | Model future plastic waste timing |
| WEEE | Electronics composition | Estimate recoverable materials |
| ELV | Vehicle material composition | Calculate recycling potential |
| C&D waste | Building composition | Regional allocation of demolition waste |

---

## Steel Stocks and Flows Data (Pauliuk Dataset)

### Dataset: "Steel all over the world" (Pauliuk et al., 2013)

The most comprehensive global steel stock dataset available, used as a basis for IEDC steel data.

**Link**: [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0921344912002078)

### Coverage

| Dimension | Value |
|-----------|-------|
| Countries | ~200 (UN Comtrade regions) |
| Time period | 1700-2008 |
| Product groups | 4 (construction, machinery, transportation, appliances) |
| Data points | 63,565 |

### Per Capita Stock Saturation Levels

| Product Group | Per Capita Stock |
|--------------|------------------|
| **Total** | 13 ± 2 tonnes |
| Construction | 10 ± 2 tonnes |
| Machinery | 1.3 ± 0.5 tonnes |
| Transportation | 1.5 ± 0.7 tonnes |
| Appliances/containers | 0.6 ± 0.2 tonnes |

### Methodology
- Dynamic MFA covering 288 regions (1700-2008)
- Uses production, trade, and lifetime data
- Full uncertainty analysis included
- Supplementary data available from authors

### NEW: 500m Gridded Global Dataset (2025)
- Steel, aluminium, cement stocks at 500m spatial resolution
- Time series: 2000-2019
- [Nature Scientific Data](https://www.nature.com/articles/s41597-025-05618-0)

---

## Quantifying Slags from Steel Data

### Slag Generation Coefficients

Use these coefficients to estimate slag generation from steel production data:

| Process | Byproduct | Rate (kg/t steel) |
|---------|-----------|-------------------|
| **BF-BOF Route** | Total co-products | ~400 |
| Blast Furnace | BF Slag | 250-300 |
| BOF | Steelmaking slag | 100-150 |
| BF | Dust & sludge | ~20 |
| BOF | Dust & sludge | ~3 |
| **EAF Route** | Total co-products | ~200 |
| EAF | EAF Slag | 110-200 |
| Ladle Furnace | LF Slag | 10-50 |

### Calculation Example

```
Slag_generated = Steel_production × Slag_coefficient

Example for 1 Mt steel (BF-BOF route):
- BF Slag:  1,000,000 t × 0.275 = 275,000 t
- BOF Slag: 1,000,000 t × 0.126 = 126,000 t
- Total:    ~400,000 t co-products
```

### Slag Composition (typical weight %)

| Component | BF Slag | BOF Slag | EAF Slag |
|-----------|---------|----------|----------|
| CaO | 30-50 | 40-52 | 25-40 |
| SiO₂ | 28-38 | 10-19 | 10-20 |
| Al₂O₃ | 8-24 | 1-4 | 3-10 |
| MgO | 1-18 | 5-10 | 5-15 |
| FeO | <1 | 14-20 | 15-30 |
| MnO | <1 | 2-5 | 3-8 |

### Global Slag Production (~2022)

| Slag Type | Global Production | EU Production |
|-----------|-------------------|---------------|
| BF Slag (GBS) | ~312 Mt | ~20 Mt |
| Air-cooled BF slag | ~104 Mt | - |
| BOF Slag | ~143 Mt | ~10 Mt |
| EAF Slag | ~68 Mt | ~5 Mt |
| **Total** | >400 Mt/year | ~35 Mt/year |

---

## Industrial Residues and Secondary Raw Materials

### IEDC Coverage

The IEDC has **limited direct coverage** of slags, ashes, and sludges. For these materials, use complementary sources:

### Alternative Data Sources

| Source | Data Type | Coverage |
|--------|-----------|----------|
| **Eurostat W12x** | Mineral waste tonnages | EU countries by year |
| **Eurostat W033** | Sludges | EU countries by year |
| **Eurostat W124** | Combustion waste (ash) | EU countries by year |
| **JRC RMIS** | SRM composition, recovery | EU scope |
| **WorldSteel** | Byproduct LCI data | Global/regional |
| **Euroslag** | Slag statistics | Europe |

### EWC-Stat Codes for Industrial Residues

| Code | Category | Includes |
|------|----------|----------|
| **W12** | Mineral wastes | Slags, ash, mineral residues |
| **W121** | Mineral construction waste | Concrete, bricks |
| **W122** | Other mineral waste | Slags, dross |
| **W124** | Combustion waste | Fly ash, bottom ash |
| **W033** | Sludges from waste treatment | Industrial sludges |

### JRC RMIS (Raw Materials Information System)

- **URL**: https://rmis.jrc.ec.europa.eu/
- **SRM Dataset**: https://data.jrc.ec.europa.eu/dataset/b759514c-c498-42c6-828c-6200f9cfdfe5
- **Coverage**: Product composition, lifetime data, SRM recovery
- **Scope**: EU, 2015-2018 data

---

## WorldSteel LCI Database

### Overview

The worldsteel Life Cycle Inventory (LCI) is the most comprehensive steel product lifecycle database, updated annually since 2017.

**Access**: Request form at https://worldsteel.org/steel-topics/life-cycle-thinking/lca-lciform/

### Products Covered (17 total)

**Flat Products**:
| Product | BOF Route | EAF Route |
|---------|-----------|-----------|
| Hot rolled coil | ✓ | ✓ |
| Pickled hot rolled coil | ✓ | ✓ |
| Cold rolled coil | ✓ | ✓ |
| Finished cold rolled coil | ✓ | ✓ |
| Tinplated coil | ✓ | - |
| Hot-dipped galvanised | ✓ | ✓ |
| Electro-galvanised | ✓ | ✓ |
| Organic coated flat | ✓ | ✓ |
| Plate | ✓ | ✓ |

**Long Products**:
| Product | BOF Route | EAF Route |
|---------|-----------|-----------|
| Rebar | ✓ | ✓ |
| Wire rod | ✓ | ✓ |
| Engineering steel | ✓ | ✓ |
| Sections | ✓ | ✓ |

**Tubes**:
- Welded pipe
- Seamless pipe
- UO pipe (not recently updated)
- ECCS/tin-free steel (not recently updated)

### Regional Coverage

| Region | Data Available |
|--------|----------------|
| Global | ✓ All products |
| Europe | ✓ Selected products |
| Asia | ✓ Selected products |
| Latin America | ✓ Selected products |

### Byproducts Tracked

| Byproduct | Treatment in LCI |
|-----------|------------------|
| **BF Slag** | System expansion credit (cement substitute) |
| **BOF/EAF Slag** | Credit for aggregate/cement use |
| **Process gases** | COG, BFG, BOFG - internal energy recovery |
| **Dust & sludge** | Recovery and recycling tracked |
| **Scales & oils** | Recovery rates included |

### Data Contents

- Cradle-to-gate LCI for all steel products
- Inputs: raw materials, energy, water, transport
- Outputs: products, co-products, emissions (air, water, land)
- Compliant with ISO 14040/14044
- Available in GaBi software format

### Key Reports

- [2021 LCI Study Report](https://worldsteel.org/wp-content/uploads/2021-LCA-Study-Report.pdf)
- [LCI Methodology Report](https://worldsteel.org/wp-content/uploads/Life-cycle-inventory-methodology-report.pdf)
- [Steel Co-products Fact Sheet](https://worldsteel.org/wp-content/uploads/Fact-sheet-Steel-industry-co-products.pdf)

---

## Recycling Rates and Process Yields

### End-of-Life Recycling Rates (UNEP IRP Data)

| Material | EOL Recycling Rate | Notes |
|----------|-------------------|-------|
| **Steel** | 80-90% | Highest recycled material globally |
| **Aluminium** | ~75% | 96% energy savings vs primary |
| **Copper** | 65-80% | 30% of global supply from recycling |
| **Plastics** | ~9% | Major losses to landfill |
| **Specialty metals** | <1-50% | Varies widely by metal |

### Steel Recycling by Application

| Application | Collection Rate | Recycling Rate |
|-------------|-----------------|----------------|
| Construction | 85-95% | 86% |
| Automotive | 90-95% | >80% |
| Packaging | 70-80% | ~75% |
| Appliances | 80-90% | ~85% |

### Process Efficiency Rates

| Process | Yield/Efficiency |
|---------|------------------|
| BF iron production | ~95% Fe recovery |
| BOF steelmaking | 90-95% |
| EAF steelmaking | 90-95% |
| New scrap recovery | 70-75% |
| Old scrap collection | 60-85% (varies by product) |

### Key Data Sources

- [UNEP IRP Recycling Rates Report](https://www.resourcepanel.org/reports/recycling-rates-metals)
- [UNEP IRP Global Material Flows Database](https://unep-irp.fineprint.global/)
- [IEA EOL Recycling Rates](https://www.iea.org/data-and-statistics/charts/end-of-life-recycling-rates-for-selected-metals)

---

## Data Integration Strategy for MFA Project

### Approach for Slag Quantification

| Method | Data Sources | Output |
|--------|--------------|--------|
| **Top-down** | Pauliuk stocks + slag coefficients | Regional slag potential from EOL steel |
| **Bottom-up** | WorldSteel LCI + Eurostat production | Slag generated per region |
| **Direct** | Eurostat W122/W124 | Reported mineral waste by country |
| **Modeling** | ODYM framework | Dynamic slag generation projections |

### Recommended Workflow

1. **Current production slag**: Use Eurostat steel production × slag coefficients
2. **Future EOL slag**: Use Pauliuk stock data × lifetime models
3. **Validation**: Compare with Eurostat W122 reported data
4. **Composition**: Apply typical slag composition from literature

---

## References

1. Pauliuk, S. et al. (2019). "A general data model for socioeconomic metabolism and its implementation in an industrial ecology data commons prototype." Journal of Industrial Ecology. https://doi.org/10.1111/jiec.12890
2. Pauliuk, S., Wang, T., & Müller, D.B. (2013). "Steel all over the world: Estimating in-use stocks of iron for 200 countries." Resources, Conservation & Recycling, 71, 22-30.
3. UNEP (2011). "Recycling Rates of Metals – A Status Report." International Resource Panel.
4. WorldSteel Association (2021). "Life Cycle Inventory Study - 2021 Data Release."
5. IEDC Documentation: https://www.industrialecology.uni-freiburg.de/iedc.aspx

---

## Links

### IEDC & Industrial Ecology
- [IEDC Database Search](https://www.database.industrialecology.uni-freiburg.de/)
- [IEDC Tools GitHub](https://github.com/IndEcol/IEDC_tools)
- [IE Data Commons GitHub](https://github.com/IndEcol/IE_data_commons)
- [ODYM Framework](https://github.com/IndEcol/ODYM)
- [ODYM Documentation](https://odym.readthedocs.io/)
- [ISIE Announcements](https://is4ie.org/announcements/2167)
- [Freiburg IE Blog](https://www.blog.industrialecology.uni-freiburg.de/)

### Steel & Metals Data
- [WorldSteel LCI Data](https://worldsteel.org/wider-sustainability/life-cycle-thinking/life-cycle-inventory-data-and-eco-profiles/)
- [WorldSteel LCI Request Form](https://worldsteel.org/steel-topics/life-cycle-thinking/lca-lciform/)
- [openLCA Nexus - WorldSteel](https://nexus.openlca.org/database/worldsteel)
- [UNEP IRP Recycling Rates](https://www.resourcepanel.org/reports/recycling-rates-metals)
- [UNEP IRP Global Material Flows Database](https://unep-irp.fineprint.global/)

### Secondary Raw Materials
- [JRC RMIS Portal](https://rmis.jrc.ec.europa.eu/)
- [JRC SRM Dataset](https://data.jrc.ec.europa.eu/dataset/b759514c-c498-42c6-828c-6200f9cfdfe5)
- [Eurostat Waste Statistics](https://ec.europa.eu/eurostat/web/waste)

### Material Composition
- [JRC Vehicle Composition Report](https://rmis.jrc.ec.europa.eu/uploads/library/JRC126564%20Material%20Composition%20Trends%20in%20vehicles.pdf)
- [Consumer Electronics Composition (Figshare)](https://figshare.com/articles/dataset/Material_composition_of_consumer_electronics/11306792/1)
- [ODYM-RECC Global Scenarios (Zenodo)](https://zenodo.org/records/4698619)
