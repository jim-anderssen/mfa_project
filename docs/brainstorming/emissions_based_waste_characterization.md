# Emissions-Based Waste Characterization

## Concept

National * NACE-level EWC-Stat waste statistics have been allocated to individual facilities (using economic data, emissions weighting, etc.). We now know which facilities/hotspots generate the largest waste volumes, and roughly which waste categories (EWC-Stat).

**The next question**: How do we go deeper and specify the actual detailed residue streams being generated at each facility? EWC-Stat categories (e.g., "metallic waste", "chemical sludges") are broad—we need process-specific characterization to identify recovery opportunities.

**Approach**: Use E-PRTR air/water/transfer data as proxies to infer waste generation patterns at the IED/BAT level. Facilities with similar emission "fingerprints" likely have similar waste streams.

**Key insight**: The same industrial processes that generate specific emissions also generate specific solid wastes. Steel plants emitting high CO2 are BOF processes, and plants with low CO2 are EAF, and will produce the corresponding slag (low Zn vs. high Zn dust etc.). Paper & pulp plants emitting high SO2 and high AOX will be Kraft processes and produce dregs, grits, lime mud, black liquor. Recycled/deinking mills will emit Low SO2, high mineral effluent and generate high-volume deinking sludge (clays, fibers).


**Foundational reference**: BREF/BAT documents provide fairly detailed characterization of residue streams for each industrial process. These link IED activities to specific waste compositions and quantities. Scientific papers gives further detail of the waste characterization.

## Data Foundation

### E-PRTR Emissions Data

Available in `data/raw/`:
- `F1_4_Air_Releases_Facilities.csv`: 353k rows, 26k facilities, 69 pollutants
- `F2_4_Water_Releases_Facilities.csv`: 241k rows, 7.5k facilities, 81 pollutants

**Coverage analysis** (Jan 2026):
- Facility-level: Very sparse (median 1.7 pollutants per facility)
- IED-level aggregation: Good coverage (mean 25 pollutants per IED activity)
- Metals sector (IED 2.*): 11 activities × 55 pollutants, 54.5% matrix density

### E-PRTR Transfers Data (Supplementary)

Available in `data/raw/`:
- `F3_2_Transfers_Facilities.csv`: 61k rows, 4,780 facilities, 89 pollutants

**Key difference**: Transfers = pollutants in waste sent to off-site treatment, not emissions to environment. This directly characterizes *waste content*.

**Coverage analysis** (Jan 2027):
- 4,780 facilities (vs 26k air, 7.5k water)
- 2,564 facilities report transfers but NO air/water releases → extends coverage
- 13.6% have 5+ pollutants (vs 8.4% air, 38.4% water)
- 425 facilities have all three data types

**Top pollutants in transfers** (by facility count):
- TOC (2,526 facs), Ni (1,016), Zn (1,010), Total P (955), Total N (825)
- Heavy metals dominate: Ni, Zn, Cu, As, Cr, Pb, Hg, Cd
- Organics: Phenols, PAHs, toluene, xylenes

**Value for waste characterization**:
- Heavy metal content in waste is *directly reported* (not inferred)
- AOX in transfers = chlorine-based process indicator
- Complements emissions fingerprinting with actual waste composition signals

### Pollutant Categories

**Air emissions**:
- Heavy metals: Zn, Pb, Ni, Cd, Hg, Cu, Cr, As
- Combustion: CO2, NOx, SOx, CO, PM10
- Organics: NMVOC, benzene, PAHs, naphthalene
- Halogenated: HCl, HF, dioxins, PCBs

**Water emissions**:
- Heavy metals: Zn, Cu, Ni, Cr, Pb, Cd, As, Hg
- Nutrients: Total N, Total P
- Organics: TOC, AOX, phenols
- Other: Chlorides, fluorides, cyanides

**Transfers to waste** (directly characterizes waste content):
- Heavy metals: Ni, Zn, Cu, Cr, Pb, As, Hg, Cd (dominant)
- Organics: TOC, phenols, PAHs, toluene, xylenes
- Halogenated: AOX (strong process signature for chlorine use)
- Nutrients: Total N, Total P

## Approach

### Step 1: Tensor Decomposition on Emissions

Build tensor: `IED activity × Pollutant × Country` (or just `IED × Pollutant` if country dimension is too sparse)

```python
import tensorly as tl
from tensorly.decomposition import parafac

# X shape: (n_ied_activities, n_pollutants, n_countries)
# or simpler: (n_ied_activities, n_pollutants)
factors = parafac(X, rank=R, mask=~np.isnan(X))  # handles missing data
```

### Step 2: Identify Latent "Process Regimes"

Expected regime types from emission patterns:

| Regime | Characteristic Emissions | Industrial Process |
|--------|-------------------------|-------------------|
| Pyrometallurgy | High Zn, Pb, SO2, PM10, CO | Metal smelting, steel production |
| Electrochemistry | High Cr, Ni, HF, cyanides | Surface treatment, plating |
| Solvent-based | High NMVOC, benzene, toluene | Chemical processing, coating |
| Combustion | High CO2, NOx, PM10, low metals | Power generation, incineration |
| Chlor-alkali | High Hg, Cl2, dioxins | Chlorine production |

### Step 3: Map Regimes to Waste Types

**Option A: BREF-informed transfer matrix** (semi-manual)
- Create Pollutant → Waste type soft mapping from BREF documents
- E.g., heavy metals → W061 (metallic): 0.6, W124 (sludge): 0.2

**Option B: Hybrid with any available facility-waste data**
- If we have sparse facility-level waste data, use it to learn Regime → Waste weights

### Step 4: Output - Continuous Waste Affinities

For each IED activity (and thus each facility):
```python
waste_weights = {
    'W061': 0.35,  # metallic waste
    'W071': 0.22,  # chemical waste
    'W063': 0.18,  # slag
    'W124': 0.12,  # chemical sludges
    ...           # all waste types get a weight (summing to 1.0)
}
```

## Extension: Waste Composition Characterization

### Beyond EWC-Stat Classification

Instead of just waste type codes, predict waste composition:

```
Facility emission profile → Process regime → Waste composition estimate

Example output:
{
  "metallic_dust": {Fe: 35%, Zn: 12%, Pb: 3%, CaO: 15%},
  "slag": {Cite: 40%, SiO2: 25%, Fe2O3: 8%, heavy_metals: 2%}
}
```

### Potential Data Sources for Composition

| Source                   | Coverage          | Detail                          | IED-linkage             |
| ------------------------ | ----------------- | ------------------------------- | ----------------------- |
| BREF documents           | Good              | Qualitative + some quantitative | Direct (IED activities) |
| National waste registers | Varies by country | Sometimes composition           | Facility-level          |
| Industry studies         | Sector-specific   | High detail                     | Manual matching         |



### BREF Documents as Primary Source

BREF (Best Available Techniques Reference) documents contain:
- Process descriptions with material flows
- Typical waste streams per process
- Some composition data (especially for major wastes)
- Directly linked to IED Annex I activities

**TODO**: Mine BREF documents systematically for waste characterization data.

## Implementation Roadmap

1. [ ] **Prototype tensor decomposition** on metals sector (IED 2.*)
2. [ ] **Extract BREF waste data** - start with iron/steel BREF
3. [ ] **Build Emission → Waste transfer matrix** from BREF knowledge
4. [ ] **Validate** against known facility-waste data (if available)
5. [ ] **Extend** to other sectors (chemicals, minerals, etc.)

## Benefits

1. **Data-driven**: Patterns from observed emissions, not just theory
2. **Handles sparse data**: Tensor methods impute missing values
3. **Continuous weights**: Proportions rather than binary mappings
4. **Composition potential**: Goes beyond classification to characterization
5. **Updatable**: New E-PRTR data → re-decompose → updated weights

## Feasibility Assessment: Facility-Level vs IED-Level

### Data Sparsity Reality Check (Jan 2026 analysis)

**Overall facility-level coverage is sparse:**
- Median pollutants per facility: **1** (air only, recent data)
- 54% of facilities report only 1 pollutant
- Most facilities can't be "fingerprinted" by emissions

**But some IED activities have good facility-level data:**

| IED | Activity | Air only | Air+Water | Facility-level viable? |
|-----|----------|----------|-----------|----------------------|
| 3(c)(i) | Cement clinker | 74% | 75% | **Yes** |
| 6(a) | Pulp/paper | 59% | **74%** | **Yes** |
| 1(a) | Combustion >50MW | 67% | 72% | **Yes** |
| 2(b) | Steel production | 51% | 55% | **Yes** |
| 2(e)(i) | Non-ferrous | 40% | 41% | Marginal |
| 1(c) | Combustion <50MW | 25% | 28% | No |
| Most others | - | <25% | - | No - IED-level only |

*"X%" = % of facilities with 5+ pollutants reported*

### Steel Case Study: Process Differentiation Works

For IED 2(b) steel facilities with sufficient data, emissions clearly distinguish routes:

| Metric | High CO2 (BF/BOF) | Low CO2 (EAF) | Interpretation |
|--------|-------------------|---------------|----------------|
| Facilities | 19 | 55 | - |
| CO2 emissions | 3.9 Mt | 114 kt | 34x difference |
| CO emissions | 62 Mt | 0.9 Mt | 70x difference |
| SO2 emissions | 2.9 Mt | 69 kt | 42x difference |

**This maps to different waste profiles:**

| Route | Identifying emissions | Expected wastes |
|-------|----------------------|-----------------|
| BF/BOF (integrated) | Very high CO2, CO, SO2 | BF slag 180-350 kg/t, BOF slag, low-Zn dust (1-3%) |
| EAF (mini-mill) | Lower CO2, variable Zn | EAF slag 120-170 kg/t, high-Zn dust (15-48%) |

**Validated examples:**
- High CO2 cluster: voestalpine, Salzgitter, ArcelorMittal, Tata Steel (known integrated works)
- Low CO2 cluster: Acería Compacta, CMC Poland, Industeel (known EAF mills)

### Value of Water Emissions

Water emissions add coverage, especially for:
- **Pulp/paper**: +15% facilities with 5+ pollutants
- **Heavy metals**: Zn, Ni, Cr, Pb, As, Cu in water distinguish metal processing sub-types

Water pollutants most useful for steel:
- Zinc, Nickel, Chromium, Lead (process-specific)
- Fluorides, Cyanides (surface treatment indicators)

### Recommended Approach: Tiered System

```
Facility allocation logic:

IF facility has 5+ pollutants (air+water combined):
    → Use emission fingerprint to classify sub-process
    → Apply sub-process-specific waste profile (e.g., EAF vs BF/BOF)

ELSE:
    → Fall back to IED-level average waste profile
    → Use available emissions (CO2, NOx) as quantity proxy only
```

**Expected coverage:**
- ~20-30% of facilities: Facility-specific waste profiles (for data-rich IEDs)
- ~70-80% of facilities: IED-level average profiles

## Open Questions

- What rank R to use for decomposition? (trade-off: interpretability vs fit)
- Should we cluster facilities within IEDs or just use simple thresholds (e.g., CO2 > 1Mt)?
- Can we validate sub-process assignments against company reports or industry databases?
- What level of waste composition detail is achievable from BREFs?

## Case Study: Iron & Steel Production Waste Characterization

### Waste Types and Quantities (per tonne of steel)

| Waste Stream | Quantity (kg/t steel) | Process Source |
|--------------|----------------------|----------------|
| BF Slag | 180-350 | Blast furnace (pig iron) |
| BOF Slag | 150-200 | Basic oxygen furnace |
| EAF Slag | 120-170 | Electric arc furnace |
| EAF Dust | 15-20 | EAF off-gas treatment |
| BOF Dust | 7-15 | BOF off-gas treatment |
| Mill Scale | ~20 (2% of output) | Hot rolling |
| Rolling Sludge | Variable | Rolling mill water treatment |

**Total co-products**: 200 kg (EAF route) to 400-600 kg (BF/BOF route) per tonne steel

### Composition Data

#### Blast Furnace Slag
| Component | Range (%) |
|-----------|-----------|
| CaO | 30-50 |
| SiO2 | 28-38 |
| Al2O3 | 8-24 |
| MgO | 1-18 |
| MnO | 1-10 |
| FeO | trace |

*Basicity (CaO/SiO2) typically ~1.1; four major oxides make up ~96% of slag*

#### BOF Slag
| Component | Range (%) |
|-----------|-----------|
| CaO | 34-55 |
| SiO2 | 8-20 |
| Fe2O3 | 14-32 |
| MgO | 1-10 |
| Al2O3 | 1-7 |

*Higher CaO and free CaO content than BF slag; contains hydraulic silicate minerals*

#### EAF Dust (EAFD)
| Component | Typical Range |
|-----------|---------------|
| Fe (as oxides) | 20-40% |
| Zn | 15-48% |
| CaO | 5-15% |
| SiO2 | 2-8% |
| Pb | 1-5% |
| Cd | 0.1-0.5% |

*Zn primarily as franklinite (ZnFe2O4) and zincite (ZnO); classified as hazardous waste*
*Zn content >15% required for economic recovery*

#### BOF Dust
| Component | Range |
|-----------|-------|
| Fe | 54-70% |
| Zn | 1.4-3.2% |

*Lower Zn than EAF dust; often recycled to sinter plant*

#### Mill Scale
| Component | Typical |
|-----------|---------|
| Fe (as FeO, Fe3O4) | ~70% |
| Oil/grease | 0.1-10% |
| Moisture | variable |

*High iron content makes it valuable for recycling to BF/sinter*

#### Rolling Sludge
| Component | Range |
|-----------|-------|
| Fe | 30-60% |
| Oil | 1.5-30% |
| Moisture | 20-50% |

### Emission-Waste Linkages for Steel

Based on this data, expected emission → waste correlations:

| E-PRTR Emissions | Indicative Waste Stream | Composition Signal |
|------------------|------------------------|-------------------|
| High Zn, Pb, Cd | EAF dust | High Zn (15-48%), hazardous |
| High SO2, PM10 | BF/BOF slag, dust | High Caite, ite |
| High CO, CO2 | Combustion residues | Mineral content |
| High Fe (water) | Mill scale, sludge | High Fe (30-70%) |
| High fluorides | Certain alloy processes | Flux residues |

### Potential for Process-Specific Waste Fingerprints

Different steel routes have distinct emission AND waste profiles:

| Route | Key Emissions | Key Wastes |
|-------|---------------|------------|
| BF/BOF (integrated) | High CO2, SO2, PM10 | BF slag (high), BOF slag, low-Zn dust |
| EAF (scrap-based) | Lower CO2, higher Zn | EAF slag, high-Zn dust (if galvanized scrap) |
| Secondary metallurgy | Cr, Ni, alloy metals | Alloy-specific dusts/sludges |

This differentiation could allow tensor-derived regimes to distinguish not just IED activities but sub-processes within steel production.

## Case Study: Pulp & Paper Production Waste Characterization

### Three Main Process Regimes

| Regime                | Key Emissions                  | Waste (kg/t) | Characteristic Wastes                  |
| --------------------- | ------------------------------ | ------------ | -------------------------------------- |
| **Kraft (chemical)**  | High SO2, AOX                  | ~100         | Dregs, grits, lime mud, black liquor   |
| **Mechanical**        | Low SO2, high electricity      | ~60          | Wood residues, biological sludge       |
| **Recycled/deinking** | Low SO2, mineral-rich effluent | 150-600      | Deinking sludge (clay, kaolin, fibers) |

**Key insight**: Recycled paper generates **3-10x more sludge** than virgin pulp, with high mineral content from paper fillers.

### Kraft Process Wastes

| Waste Stream | Composition | Quantity |
|--------------|-------------|----------|
| Green liquor dregs | Ca, Na, sulfides, carbon | Largest inorganic waste |
| Lime mud | CaCOite (~95%) | Similar to commercial calcium carbonate |
| Slaker grits | Un-reacted lime, impurities | Variable by mill |
| Black liquor | Lignin, organics, Na2S | ~1.7-1.8 t/t pulp (recovered for energy) |
| Biological sludge | High C/N ratio, organics | From wastewater treatment |

*Kraft mills produce ~100 kg solid residuals per tonne of pulp*

### Recycled Paper / Deinking Sludge

| Component | Typical Content |
|-----------|-----------------|
| Cellulose fibers | 30-50% |
| Clay/kaolin | 20-40% |
| CaCO3 (calcite) | 10-30% |
| Ink residues | 1-5% |
| TiO2, talc | Variable |

*11 million tonnes of waste produced yearly by EU pulp/paper industry, 70% from recycled paper production*

### Emission-Based Process Discrimination

From E-PRTR data analysis (2020+, 61 data-rich facilities):

| Emission | Kraft | Mechanical | Recycled |
|----------|-------|------------|----------|
| SO2 | **High** | Low | Low |
| AOX (water) | High (Cl bleach) | Low | Medium |
| TOC (water) | High | Medium | Medium |
| CO2 | High (recovery boiler) | Lower | Lower |

**Validated examples of high-SO2 facilities** (likely integrated Kraft mills):
- Domsjö Fabriker AB (Sweden) - SO2=0.5kt
- Navigator Pulp Cacia (Portugal) - SO2=0.5kt
- Nymölla bruk (Sweden) - SO2=0.5kt
- Metsä Fibre Oy, Joutseno (Finland) - SO2=0.4kt

### Waste Type Implications

| Process Route      | Identifiable by                | Expected Waste Profile                      |
| ------------------ | ------------------------------ | ------------------------------------------- |
| Kraft (integrated) | High SO2, high CO2             | Dregs, lime mud, grits, biosludge           |
| Mechanical         | Low SO2, lower CO2             | Wood rejects, biosludge only                |
| Recycled/deinking  | Low SO2, high mineral effluent | High-volume deinking sludge (clays, fibers) |

### Transfer-Based Process Discrimination (Jan 2027 analysis)

Transfers data (F3) provides direct waste characterization signals for paper/pulp:

**AOX as Kraft signature** (chlorine bleaching):
- 26 facilities report AOX transfers in sector 6
- High AOX (>10t/yr): 6 facilities → likely Kraft chemical pulp
- Low/no AOX: 20 facilities → likely mechanical or recycled

**Comparison of transfer profiles**:

| Pollutant | High AOX (Kraft) | Low AOX (Other) | Ratio |
|-----------|------------------|-----------------|-------|
| TOC | 1,940,000 kg | 354,000 kg | 5.5x |
| Total P | 26,650 kg | 10,800 kg | 2.5x |
| AOX | 47,500 kg | 1,370 kg | 35x |

**Validated high-AOX facilities** (likely Kraft):
- Zellstoff Pöls AG (Austria) - AOX: 117,500 kg
- Navigator Pulp Cacia (Portugal) - AOX: 60,100 kg
- PAPELERA GUIPUZCOANA DE ZICUÑAGA (Spain) - AOX: 33,500 kg

**Recycled paper candidates** (no AOX, elevated Zn/phenols from deinking):
- CARTONSTRONG ITALIA SRL - Zn: 214 kg, Phenols: 838 kg
- Stabilimento di Tolmezzo - Zn: 241 kg, Phenols: 85 kg

**Conclusion**: Transfers data strongly complements emissions for process discrimination. AOX alone provides 35x separation between Kraft and other processes.

### Data Sources

- [PMC - Pulp and paper mill wastes](https://pmc.ncbi.nlm.nih.gov/articles/PMC10991416/)
- [Springer - Generation of Waste in Pulp and Paper Mills](https://link.springer.com/chapter/10.1007/978-3-319-11788-1_2)
- [MDPI - Inorganic Waste in Kraft Pulp Mills](https://www.mdpi.com/2076-3417/10/7/2317)
- **BREF Document**: `docs/references/BREF:BAT/PP_revised_BREF_2015.pdf` (contains detailed BAT-associated emission levels and waste data)

### Data Sources

- [World Steel Association - Steel industry co-products](https://worldsteel.org/wp-content/uploads/Fact-sheet-Steel-industry-co-products.pdf)
- [Jernkontoret - Steel production residues](https://www.jernkontoret.se/en/the-steel-industry/production-utilisation-recycling/steel-production-residues/)
- [IspatGuru - Blast Furnace Slag](https://www.ispatguru.com/blast-furnace-slag/)
- [MDPI Encyclopedia - BOF Slag Properties](https://encyclopedia.pub/entry/43979)
- [ScienceDirect - EAF Dust overview](https://www.sciencedirect.com/topics/engineering/electric-arc-furnace-dust)
- [Wikipedia - Mill Scale](https://en.wikipedia.org/wiki/Mill_scale)
- [ScienceDirect - Utilization of slag and sludge](https://www.sciencedirect.com/science/article/abs/pii/S0921344906001297)

## References

- E-PRTR data: `data/raw/F1_4_Air_Releases_Facilities.csv`, `F2_4_Water_Releases_Facilities.csv`, `F3_2_Transfers_Facilities.csv`
- Current IED-waste mapping: `src/mappings/ied_ewc_stat.py`
- BREF documents: https://bureau-industrial-transformation.jrc.ec.europa.eu/reference/iron-and-steel-production
- Iron & Steel BREF (2012): [PDF](https://bureau-industrial-transformation.jrc.ec.europa.eu/sites/default/files/2019-11/IS_Adopted_03_2012.pdf)

---

*Status: Conceptual - feasibility confirmed for tensor approach, steel sector waste data compiled*
