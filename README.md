# MFA Project

Material Flow Analysis of European industrial waste — generation, treatment, and transboundary shipments — to support data-driven investment decisions in recycling/recovery technology.

## Capabilities

- **Facility-level waste allocation** — distributes national Eurostat waste statistics to individual E-PRTR facilities using emissions-based or GVA-based proxies
- **Technology classification** — classifies steel/metal facilities by production route (BF_BOF, EAF, MIXED) using IED/PRODCOM data
- **Facility clustering** — groups facilities by waste profile with geographic distance constraints
- **AI extraction agents** — extracts and maps waste data from company sustainability reports to EWC-Stat codes
- **Interactive dashboard** — Streamlit map for exploring facility waste profiles and cluster assignments

## Data Sources

| Source | Content |
|--------|---------|
| Eurostat | Waste generation (NACE2), NUTS2 regional statistics |
| E-PRTR | Facility emissions and waste transfers |
| IED installations | Industrial activity classifications |
| PRODCOM | Production statistics for waste coefficient estimation |
| Company reports | Sustainability/environmental reports (via AI agents) |

## Project Structure

```
├── app/                    # Streamlit dashboard
├── data/
│   ├── raw/                # Immutable source data
│   ├── interim/            # Intermediate transforms
│   └── processed/          # Final outputs (one subdirectory per category)
├── docs/                   # Analysis reports and brainstorming
├── notebooks/              # Jupyter notebooks
├── prompts/                # AI agent prompt templates
├── src/
│   ├── agents/             # LLM-based waste data extraction
│   ├── allocation/         # Emissions-based and GVA-based allocators
│   ├── analysis/           # Clustering and validation
│   ├── classification/     # Technology classification
│   ├── integration/        # IED/PRODCOM linkers
│   ├── loaders/            # Data loaders (Eurostat, E-PRTR, NUTS2)
│   ├── mappings/           # EWC-Stat, NACE, IED taxonomies
│   └── utils/              # Shared helpers
└── classify_tech_generate_and_allocate_waste.py  # Main pipeline
```

## Main Pipeline

`classify_tech_generate_and_allocate_waste.py` runs the end-to-end pipeline:
1. Load and classify facilities by technology type
2. Allocate national waste generation to facilities
3. Output facility-level waste estimates to `data/processed/`

## Running

```bash
# Install dependencies
uv sync

# Run main pipeline
uv run classify_tech_generate_and_allocate_waste.py

# Launch dashboard
uv run streamlit run app/app.py
```

## Key Outputs (`data/processed/`)

| File | Description |
|------|-------------|
| `facility_waste_allocated.csv` | Facility-level waste allocations |
| `facility_waste_classified_all_*.csv` | Facilities with technology classification |
| `facility_clusters.csv` | Cluster assignments |
| `gva_allocation/` | GVA-based allocation results |
