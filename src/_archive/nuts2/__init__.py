"""
NUTS2 Regional Waste Hotspot Analysis

Modules for allocating waste to NUTS2 regions, clustering by waste profiles,
and identifying geographical hotspots.
"""

from .data_loader import (
    load_waste_generation,
    load_sbs_employment,
    load_nuts2_names,
    load_recycling_potential,
    get_sbs_nuts2_employment,
    COUNTRY_MAP,
)
from .allocation import (
    get_regional_shares,
    allocate_waste_to_regions,
    add_economic_potential,
    NACE_EXPANSION,
)
from .clustering import (
    prepare_clustering_features,
    find_optimal_clusters,
    apply_clustering,
    get_cluster_profiles,
    apply_pca,
    # Waste composition profile clustering
    get_redundant_waste_types,
    create_waste_composition_matrix,
    apply_composition_pca,
    cluster_waste_profiles,
    summarize_cluster_compositions,
    get_top_waste_types_per_cluster,
)
from .geo_analysis import (
    load_nuts2_centroids,
    find_geographical_hotspots,
    get_hotspot_summary,
    get_cross_border_hotspots,
    calculate_cluster_density,
)
