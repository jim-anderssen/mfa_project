# IED BAT Reference Codes and Conclusions

## Overview

IED BAT (Best Available Techniques) refers to sector-specific technical reference documents under the EU Industrial Emissions Directive. These documents establish emission limits and operational standards for industrial installations.

**Total BAT Conclusions:** 56 separate documents covering 37 industrial sectors

**Source Database:** EU-BRITE (European Bureau for Research on Industrial Transformation and Emissions)

---

## Complete BAT Reference Document Codes

| Code | Full Sector Name |
|------|------------------|
| **CAK** | Production of Chlor-alkali |
| **CER** | Ceramic Manufacturing Industry |
| **CLM** | Production of Cement, Lime and Magnesium Oxide |
| **CWW** | Common Waste Water and Waste Gas Treatment/Management Systems in the Chemical Sector |
| **ECM** | Economics and Cross-media Effects |
| **EFS** | Emissions from Storage |
| **ENE** | Energy Efficiency |
| **FDM** | Food, Drink and Milk Industries |
| **FMP** | Ferrous Metals Processing Industry |
| **GLS** | Manufacture of Glass |
| **ICS** | Industrial Cooling Systems |
| **IRPP** | Intensive Rearing of Poultry or Pigs |
| **IS** | Iron and Steel Production |
| **LAN** | Landfills |
| **LCP** | Large Combustion Plants |
| **LVIC** | Large Volume Inorganic Chemicals |
| **LVIC-AAF** | Large Volume Inorganic Chemicals – Ammonia, Acids and Fertilisers |
| **LVIC-S** | Large Volume Inorganic Chemicals – Solids and Others Industry |
| **LVOC** | Production of Large Volume Organic Chemicals |
| **MIN** | Mining (extraction) of ores |
| **NFM** | Non-ferrous Metals Industries |
| **OFC** | Manufacture of Organic Fine Chemicals |
| **PBG** | Production of Batteries in Giga-Factories |
| **POL** | Production of Polymers |
| **PP** | Production of Pulp, Paper and Board |
| **REF** | Refining of Mineral Oil and Gas |
| **ROM** | Monitoring of Emissions to Air and Water from IED Installations |
| **SA** | Slaughterhouses, Animal By-products and/or Edible Co-products Industries |
| **SF** | Smitheries and Foundries Industry |
| **SIC** | Production of Speciality Inorganic Chemicals |
| **STM** | Surface Treatment of Metals and Plastics |
| **STS** | Surface Treatment Using Organic Solvents including Wood and Wood Products Preservation |
| **TAN** | Tanning of Hides and Skins |
| **TXT** | Textiles Industry |
| **WBP** | Wood-based Panels Production |
| **WGC** | Common Waste Gas Management and Treatment Systems in the Chemical Sector |
| **WI** | Waste Incineration |
| **WT** | Waste Treatment |

---

## BAT Conclusions by Industrial Category

### Chemical & Inorganic Industries
- CAK - Chlor-alkali
- LVIC, LVIC-AAF, LVIC-S - Large Volume Inorganic Chemicals
- SIC - Speciality Inorganic Chemicals
- LVOC - Large Volume Organic Chemicals
- OFC - Organic Fine Chemicals
- POL - Polymers

### Metals Processing
- FMP - Ferrous Metals Processing
- NFM - Non-ferrous Metals
- IS - Iron and Steel Production
- SF - Smitheries and Foundries

### Manufacturing
- CER - Ceramic Manufacturing
- GLS - Glass Manufacturing
- WBP - Wood-based Panels

### Energy & Environmental
- LCP - Large Combustion Plants
- ICS - Industrial Cooling Systems
- ENE - Energy Efficiency
- EFS - Emissions from Storage

### Food & Agriculture
- FDM - Food, Drink and Milk
- IRPP - Intensive Rearing of Poultry or Pigs
- SA - Slaughterhouses and Animal By-products

### Waste Management
- WI - Waste Incineration
- WT - Waste Treatment
- LAN - Landfills

### Other Industries
- PP - Pulp, Paper and Board
- REF - Refining of Mineral Oil and Gas
- STM, STS - Surface Treatment
- TAN - Tanning
- TXT - Textiles
- MIN - Mining

### Horizontal/Cross-cutting
- CWW, WGC - Common Waste Water/Gas Treatment
- ROM - Monitoring of Emissions

---

## Integration with MFA Project

### IED Installations Data

The project includes IED installations data in:
- `data/raw/F6_1_IED_Installations.csv`

**Key columns:**
- `IEDAnnexIMainActivity` - Main activity code
- `BATConclusion` - Applicable BAT conclusion reference
- `BATAEL` - BAT-Associated Emission Levels

### Linkage to Waste Analysis

IED installations are major industrial waste generators. BAT codes can be mapped to:

| BAT Code | NACE Code(s) | Primary Waste Types |
|----------|--------------|---------------------|
| IS | C24.1-C24.5 | Metal waste (W061), slags (W122), dusts/sludges (W033) |
| FMP | C24.5 | Metal waste, scale, pickling sludge |
| NFM | C24.4 | Metal waste, dross, slags |
| CER | C23.3-C23.4 | Ceramic waste, refractory materials |
| GLS | C23.1 | Glass waste, cullet |
| CLM | C23.5 | Cement kiln dust, slag substitutes |
| WI | E38.2 | Ash, slag, flue gas cleaning residues |
| WT | E38.2 | Various depending on input waste |

### Use Cases for MFA Project

1. **Company-level allocation**: Use IED installation locations (NUTS2) to allocate industrial waste more precisely
2. **Waste generation coefficients**: BAT documents contain process-specific waste generation rates
3. **Validation**: Compare allocated waste against IED installation capacities
4. **Environmental reporting**: IED facilities must report emissions - can validate waste estimates

---

## Key Timeline Updates (2026)

- **Revised IED (IED 2.0)**: Entered into force 4 August 2024
- **Member State Implementation**: EU countries must transpose into national law by 1 July 2026
- **WGC BAT Conclusions**: Must be implemented by December 2026

---

## References

- EU-BRITE Database: https://bureau-industrial-transformation.jrc.ec.europa.eu/reference
- IED Legislation: https://environment.ec.europa.eu/topics/industrial-emissions-and-safety/industrial-and-livestock-rearing-emissions-directive-ied-20_en
- BAT Exchange of Information: https://www.era-comm.eu/IED/module_1/bat.html

---

**Last Updated:** 2026-01-17
