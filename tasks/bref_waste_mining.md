# BREF Waste Characterization Mining

**Status:** Research/Data Collection
**Priority:** High
**Dependencies:** None (standalone data collection)

## Objective

Systematically extract waste stream data from BREF (Best Available Techniques Reference) documents to build a comprehensive IED activity → waste characterization database. This enables:
1. More accurate facility-level waste allocation
2. Waste composition estimates (not just classification)
3. Assessment of secondary raw material potential

## Approach

### Data to Extract per BREF

For each industrial process/IED activity:

1. **Waste types** generated (slag, dust, sludge, etc.)
2. **Quantities** (kg per tonne of product or per unit output)
3. **Composition** (% Fe, Zn, CaO, SiO2, heavy metals, etc.)
4. **Process linkage** (which sub-process generates which waste)
5. **Hazardous classification** (if mentioned)
6. **Recycling/recovery potential** (internal or external)

### Output Format

```python
# Example structure for waste_characterization.py
BREF_WASTE_DATA = {
    "iron_steel": {
        "ied_activities": ["2.1", "2.2", "2.3"],
        "wastes": {
            "bf_slag": {
                "quantity_kg_per_t": (180, 350),
                "process": "blast_furnace",
                "composition": {
                    "CaO": (0.30, 0.50),
                    "SiO2": (0.28, 0.38),
                    "Al2O3": (0.08, 0.24),
                    "MgO": (0.01, 0.18),
                    "Fe": (0.00, 0.02),
                },
                "hazardous": False,
                "ewc_stat": "W121",  # mineral waste
            },
            "eaf_dust": {
                "quantity_kg_per_t": (15, 20),
                "process": "electric_arc_furnace",
                "composition": {
                    "Fe": (0.20, 0.40),
                    "Zn": (0.15, 0.48),
                    "Pb": (0.01, 0.05),
                    "Cd": (0.001, 0.005),
                },
                "hazardous": True,
                "ewc_stat": "W061",  # metallic waste
            },
            # ... more waste types
        }
    },
    # ... more sectors
}
```

## Priority Sectors

Based on waste generation volume and data availability:

### Tier 1 - High Priority (large waste volumes, good data)

| Sector | IED Activity | BREF Document | Key Wastes |
|--------|--------------|---------------|------------|
| Iron & Steel | 2.1, 2.2, 2.3 | IS BREF (2012) | Slag, dust, sludge, scale |
| Non-Ferrous Metals | 2.5 | NFM BREF (2016) | Slag, dust, dross, anode slimes |
| Cement/Lime | 3.1 | CLM BREF (2013) | Kiln dust,ite bypass dust |
| Glass | 3.3 | GLS BREF (2012) | Cullet rejects, filter dust |
| Pulp & Paper | 6.1 | PP BREF (2015) | Lime mud, dregs, bark, sludge |

### Tier 2 - Medium Priority

| Sector | IED Activity | BREF Document | Key Wastes |
|--------|--------------|---------------|------------|
| Refineries | 1.2 | REF BREF (2015) | Spent catalysts, tank sludge |
| Large Combustion | 1.1 | LCP BREF (2017) | Fly ash, bottom ash, gypsum |
| Chemicals (organic) | 4.1 | LVOC BREF (2017) | Spent catalysts, tars |
| Chemicals (inorganic) | 4.2 | LVIC BREF (2007) | Phosphogypsum, filter cakes |
| Waste Incineration | 5.2 | WI BREF (2019) | Bottom ash, fly ash, APC residues |

### Tier 3 - Lower Priority

- Ferrous metals processing (FMP BREF)
- Surface treatment (STM BREF)
- Textiles (TXT BREF)
- Food/drink/milk (FDM BREF)

## Tasks

### Phase 1: Iron & Steel (Completed in brainstorming)
- [x] Identify waste types and quantities
- [x] Extract composition data for slag, dust, scale
- [x] Document emission-waste linkages
- [ ] Formalize into data structure

### Phase 2: Non-Ferrous Metals
- [ ] Download NFM BREF document
- [ ] Extract copper production wastes (slag, dust, anode slimes)
- [ ] Extract aluminium production wastes (red mud, SPL, dross)
- [ ] Extract zinc production wastes (jarosite, goethite)
- [ ] Extract lead production wastes

### Phase 3: Minerals (Cement, Glass)
- [ ] Extract cement kiln dust composition
- [ ] Extract glass furnace dust data
- [ ] Documentite/ite waste streams

### Phase 4: Other Sectors
- [ ] Pulp & paper sludges
- [ ] Refinery residues
- [ ] Chemical industry wastes

### Phase 5: Integration
- [ ] Create `src/mappings/bref_waste_characterization.py`
- [ ] Link to IED activity codes
- [ ] Map to EWC-Stat codes
- [ ] Integrate with emissions-based allocation

## Data Sources

### BREF Documents
- Main repository: https://bureau-industrial-transformation.jrc.ec.europa.eu/reference
- Alternative: https://eippcb.jrc.ec.europa.eu/reference (redirects to above)

### Supplementary Sources
- World Steel Association factsheets
- European Aluminium Association
- Eurofer (European Steel Association)
- CEMBUREAU (cement industry)
- Academic literature on industrial ecology

## Expected Outputs

1. **`src/mappings/bref_waste_characterization.py`** - Structured waste data by IED activity
2. **Waste composition lookup** - Given IED activity → expected waste composition
3. **Quantity factors** - kg waste per tonne product for mass balance
4. **Emission-waste correlation matrix** - Link E-PRTR emissions to waste types

## Success Criteria

- Cover IED activities representing >80% of industrial waste generation
- Composition data for major waste streams (slag, dust, sludge)
- Quantity ranges with uncertainty bounds
- Validated against env_wasgen totals where possible

## References

- Brainstorming document: `docs/brainstorming/emissions_based_waste_characterization.md`
- Current IED mappings: `src/mappings/ied_ewc_stat.py`, `src/mappings/ied_nace.py`
- Iron & Steel BREF: [PDF](https://bureau-industrial-transformation.jrc.ec.europa.eu/sites/default/files/2019-11/IS_Adopted_03_2012.pdf)
