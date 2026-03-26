# MFA Project Schema

Material Flow Analysis of European waste generation, treatment, and transboundary shipments.

## Domain Concepts
- **NACE**: Industry codes (C24=Basic metals, C25=Fabricated metals)
- **EWC-Stat/LoW**: Waste classification codes
- **IED**: Industrial Emissions Directive facility identifiers
- **E-PRTR**: European Pollutant Release and Transfer Register

## Directory Structure

```
├── app/              # Streamlit dashboard
├── data/
│   ├── raw/          # Immutable source files (Eurostat, E-PRTR, IED)
│   ├── interim/      # Intermediate transforms
│   └── processed/    # Final outputs
├── notebooks/        # Analysis notebooks
├── src/
│   ├── loaders/      # Data loading (Eurostat API, E-PRTR, Swedish companies)
│   ├── mappings/     # Classification systems (EWC-Stat, NACE, IED, PRODCOM)
│   ├── allocation/   # Waste allocation algorithms
│   ├── analysis/     # Clustering and validation
│   ├── integration/  # IED/PRODCOM linkers
│   ├── validation/   # Ground-truth validation
│   ├── agents/       # LLM-based extraction agents
│   ├── modeling/     # ML training/prediction
│   └── utils/        # Helpers
└── run_*.py          # Entry point scripts
```

## Core Data Flow

```
Eurostat API / E-PRTR / Company Data
         ↓
    Loaders (load, normalize)
         ↓
    Mappings (classify: NACE, EWC-Stat, IED)
         ↓
    Allocation (distribute national → facility/company)
         ↓
    Analysis (cluster, validate)
         ↓
    Outputs (CSVs, visualizations)
```

## Key Modules

| Module | Purpose | Key Files |
|--------|---------|-----------|
| loaders | Data I/O | eurostat.py, eprtr.py, nuts2.py, retriever.py |
| mappings | Taxonomies | ewc_stat.py, ied_nace.py, ied_ewc_stat.py, prodcom_waste.py |
| allocation | Distribution | emissions_based_allocator.py, gva_based_allocator.py |
| analysis | Clustering | facility_clustering.py, validation_correlation.py |
| integration | Linkers | ied_linker.py, prodcom_linker.py |
| validation | Ground-truth | steel_tracker.py |
| agents | LLM extraction | waste_extraction_agent.py, subagents.py |

## Entry Points

- `app/app.py` - Streamlit dashboard
- `run_facility_clustering.py` - Clustering pipeline
- `notebooks/` - Interactive analysis

## Key Output Files

| File | Purpose |
|------|---------|
| facility_waste_allocated.csv | Facility-level waste allocations |
| facility_clusters.csv | Cluster assignments |
| facility_cluster_summary.csv | Cluster statistics |
| nuts2_waste_allocated.csv | Regional allocations |
| validated_company_waste.csv | Validation results |
| correlation_report.csv | Allocation accuracy metrics |
