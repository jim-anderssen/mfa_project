# Notebooks

This directory contains Jupyter notebooks for analyzing European waste flows and identifying regional hotspots for waste recovery.

## Notebooks

### 1. Example study.ipynb

**Introduction to the MFA methodology**

A walk-through showing public datasets on waste, and how these fragmented datasets contain the possibility to fuse them into a coherent material flow picture. This notebook demonstrates:

- Overview of available datasets: waste generation (env_wasgen), waste treatment (env_wastrt), waste facilities (env_wasfac), waste shipments, trade in recyclable materials (env_trdrrm), material flow accounts (env_ac_mfa), and WEEE data
- Integration of waste generation, treatment, trade, and facility data from Eurostat
- Brief case study: Tracking metallic waste flows in Poland (NACE C24/C25 - metal manufacturing)
- Economic allocation of waste to NUTS-2 regions using SBS employment data
- Analysis of waste treatment operations and cross-border flows of secondary raw materials


**Key insight**: No publicly available source currently provides facility-, material-, and flow-resolved views of secondary raw materials. This notebook shows how such questions can be approached by re-engineering data into a single material flow system.

---

### 2. NUTS2_Regional_Hotspot_Analysis.ipynb

**Regional waste allocation and clustering analysis**

Allocates national waste generation to NUTS-2 regions using SBS employment data as a proxy, then applies clustering to identify regional hotspots for waste recovery.

**Methodology**:
1. Load waste generation by country, NACE activity, and EWC-Stat waste type
2. Use SBS employment data to calculate regional shares per NACE activity
3. Allocate national waste to NUTS-2 regions proportionally to employment
4. Calculate economic potential using recycling value indices
5. Apply K-means clustering on Region x NACE x Waste combinations
6. Identify hotspot tiers (low to high value)

**Outputs**:
- `nuts2_waste_allocated_detail.csv` - Detailed allocation by Region x NACE x Waste with cluster assignments
- `nuts2_regional_hotspots.csv` - Regional summary with hotspot counts
- `nuts2_region_waste_matrix.csv` - Pivot table of regions by waste type
- `nuts2_region_nace_matrix.csv` - Pivot table of regions by NACE activity

---

### 3. NUTS2_Geographical_Hotspots.ipynb

**Spatial clustering of high-value regions**

Builds on the regional hotspot analysis to identify geographical concentrations where multiple high-value NUTS-2 regions are spatially close to each other. This helps identify optimal locations for waste recovery infrastructure and cross-border cooperation opportunities.

**Methodology**:
1. Load waste data and allocate to NUTS-2 regions (reuses functions from regional analysis)
2. Apply K-means clustering to identify high-value Region x NACE x Waste combinations
3. Load NUTS-2 centroid coordinates
4. Apply hierarchical clustering (complete linkage) on high-value regions to find geographical clusters
5. Identify cross-border hotspots spanning multiple countries

**Key parameters**:
- `max_diameter_km`: Maximum distance between any two regions in a cluster (default: 400km)
- `min_regions`: Minimum regions required to form a geographical cluster (default: 3)

**Outputs**:
- `nuts2_geographical_hotspots.csv` - Regions with geographical cluster assignments
- `nuts2_geo_hotspot_summary.csv` - Summary statistics per geographical cluster
- `nuts2_high_value_with_geo.csv` - High-value combinations with geo-cluster assignments
- `nuts2_geographical_hotspots.png` - Map visualization of geographical clusters

---

## Data Dependencies

These notebooks rely on:
- Eurostat datasets (fetched via the `eurostat` package)
- Processed data in `data/interim/` and `data/raw/`
- Custom modules in `src/` (io_file, features, utils, nuts2)

## Requirements

```
pandas
numpy
matplotlib
seaborn
scikit-learn
eurostat
cartopy (optional, for map visualization)
```