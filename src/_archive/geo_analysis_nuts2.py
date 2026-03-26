"""
geo_analysis.py

Functions for geographical hotspot analysis - identifying spatial clusters
where multiple high-value NUTS-2 regions are geographically concentrated.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import pdist, squareform

from ..io_file import RAW_DIR, PROCESSED_DIR


# NUTS2 centroid coordinates (approximate lat/lon)
# Source: Eurostat GISCO NUTS 2021 centroids
NUTS2_CENTROIDS = {
    # Austria
    'AT11': (47.50, 16.50), 'AT12': (48.20, 15.75), 'AT13': (48.20, 16.37),
    'AT21': (46.90, 14.50), 'AT22': (47.10, 15.40), 'AT31': (48.30, 14.25),
    'AT32': (47.30, 11.50), 'AT33': (47.10, 10.00), 'AT34': (47.10, 13.10),
    # Belgium
    'BE10': (50.85, 4.35), 'BE21': (51.00, 4.40), 'BE22': (51.00, 3.70),
    'BE23': (51.10, 5.00), 'BE24': (50.90, 5.30), 'BE25': (50.70, 5.60),
    'BE31': (50.35, 3.80), 'BE32': (50.40, 4.40), 'BE33': (50.20, 5.00),
    'BE34': (49.80, 5.40), 'BE35': (50.05, 5.70),
    # Bulgaria
    'BG31': (43.00, 25.50), 'BG32': (43.20, 27.90), 'BG33': (43.70, 26.30),
    'BG34': (43.40, 24.00), 'BG41': (42.70, 23.35), 'BG42': (42.15, 24.75),
    # Croatia
    'HR02': (45.55, 15.65), 'HR03': (45.00, 15.00), 'HR05': (45.80, 16.00),
    'HR06': (45.35, 17.70),
    # Cyprus
    'CY00': (35.00, 33.00),
    # Czechia
    'CZ01': (50.08, 14.45), 'CZ02': (49.75, 13.40), 'CZ03': (49.45, 17.70),
    'CZ04': (50.45, 13.80), 'CZ05': (50.50, 15.70), 'CZ06': (49.20, 16.60),
    'CZ07': (49.60, 17.25), 'CZ08': (49.80, 18.25),
    # Denmark
    'DK01': (55.70, 12.55), 'DK02': (55.40, 10.40), 'DK03': (55.50, 9.50),
    'DK04': (56.50, 9.50), 'DK05': (55.00, 11.80),
    # Estonia
    'EE00': (58.80, 25.00),
    # Finland
    'FI19': (61.00, 25.00), 'FI1B': (60.80, 23.20), 'FI1C': (62.50, 26.00),
    'FI1D': (65.00, 26.00), 'FI20': (60.10, 19.95),
    # France
    'FR10': (48.85, 2.35), 'FRB0': (47.30, 2.50), 'FRC1': (47.30, 5.00),
    'FRC2': (47.70, 7.00), 'FRD1': (48.10, -1.70), 'FRD2': (48.60, -2.80),
    'FRE1': (50.40, 2.90), 'FRE2': (49.90, 4.40), 'FRF1': (48.60, 7.70),
    'FRF2': (47.20, 6.00), 'FRF3': (48.90, 6.20), 'FRG0': (47.50, -0.50),
    'FRH0': (48.00, -3.00), 'FRI1': (46.50, -0.50), 'FRI2': (45.00, -0.50),
    'FRI3': (44.50, 0.50), 'FRJ1': (43.60, 3.90), 'FRJ2': (43.00, 6.00),
    'FRK1': (45.80, 4.80), 'FRK2': (45.00, 5.00), 'FRL0': (41.90, 8.80),
    # Germany
    'DE11': (48.80, 9.20), 'DE12': (49.00, 8.50), 'DE13': (48.70, 9.90),
    'DE14': (48.50, 9.00), 'DE21': (48.15, 11.55), 'DE22': (48.90, 11.40),
    'DE23': (49.45, 11.10), 'DE24': (49.80, 10.90), 'DE25': (49.30, 10.00),
    'DE26': (49.80, 9.95), 'DE27': (48.40, 10.00), 'DE30': (52.52, 13.40),
    'DE40': (52.40, 13.00), 'DE50': (53.55, 10.00), 'DE60': (53.55, 10.00),
    'DE71': (50.10, 8.70), 'DE72': (50.35, 9.00), 'DE73': (50.95, 9.80),
    'DE80': (53.85, 11.40), 'DE91': (52.40, 9.75), 'DE92': (53.10, 8.80),
    'DE93': (52.95, 7.60), 'DE94': (53.20, 7.30), 'DEA1': (51.45, 7.00),
    'DEA2': (51.20, 6.80), 'DEA3': (51.00, 7.50), 'DEA4': (50.95, 6.95),
    'DEA5': (51.75, 8.75), 'DEB1': (49.45, 7.75), 'DEB2': (50.35, 7.60),
    'DEB3': (49.90, 6.65), 'DEC0': (49.35, 7.00), 'DED2': (50.85, 12.90),
    'DED4': (51.05, 13.70), 'DED5': (51.35, 12.35), 'DEE0': (52.00, 11.60),
    'DEF0': (54.30, 9.80), 'DEG0': (50.85, 11.00),
    # Greece
    'EL30': (37.98, 23.73), 'EL41': (41.00, 24.00), 'EL42': (40.60, 22.95),
    'EL43': (39.60, 22.40), 'EL51': (41.10, 25.00), 'EL52': (40.00, 21.50),
    'EL53': (39.00, 22.00), 'EL54': (39.60, 20.85), 'EL61': (38.30, 21.80),
    'EL62': (38.00, 23.80), 'EL63': (37.50, 22.50), 'EL64': (37.00, 22.10),
    'EL65': (38.00, 26.00),
    # Hungary
    'HU11': (47.50, 19.05), 'HU12': (47.60, 18.30), 'HU21': (47.40, 16.90),
    'HU22': (46.80, 17.65), 'HU23': (46.50, 20.15), 'HU31': (47.90, 20.40),
    'HU32': (48.00, 21.70), 'HU33': (46.90, 19.70),
    # Ireland
    'IE04': (53.35, -6.25), 'IE05': (52.65, -8.65), 'IE06': (53.65, -8.00),
    # Italy
    'ITC1': (45.50, 8.50), 'ITC2': (45.50, 9.50), 'ITC3': (44.40, 8.90),
    'ITC4': (45.45, 9.20), 'ITF1': (42.35, 13.40), 'ITF2': (41.50, 15.50),
    'ITF3': (40.85, 14.25), 'ITF4': (40.50, 17.00), 'ITF5': (40.00, 16.50),
    'ITF6': (38.90, 16.60), 'ITG1': (37.50, 14.00), 'ITG2': (39.22, 9.12),
    'ITH1': (46.50, 11.35), 'ITH2': (46.00, 11.50), 'ITH3': (45.75, 12.30),
    'ITH4': (45.90, 13.20), 'ITH5': (44.50, 11.35), 'ITI1': (43.80, 11.25),
    'ITI2': (43.10, 12.40), 'ITI3': (43.60, 13.50), 'ITI4': (41.90, 12.50),
    # Latvia
    'LV00': (56.95, 24.10),
    # Lithuania
    'LT01': (54.68, 25.28), 'LT02': (55.70, 24.00),
    # Luxembourg
    'LU00': (49.61, 6.13),
    # Malta
    'MT00': (35.90, 14.45),
    # Netherlands
    'NL11': (53.20, 6.55), 'NL12': (53.00, 5.55), 'NL13': (52.75, 6.60),
    'NL21': (52.50, 6.10), 'NL22': (52.05, 5.10), 'NL23': (52.60, 4.75),
    'NL31': (52.10, 4.30), 'NL32': (51.95, 4.50), 'NL33': (52.40, 4.90),
    'NL34': (52.25, 5.20), 'NL41': (51.45, 5.50), 'NL42': (51.40, 6.00),
    # Norway
    'NO01': (59.90, 10.75), 'NO02': (60.40, 5.30), 'NO03': (62.50, 9.00),
    'NO04': (69.00, 19.00), 'NO05': (59.00, 6.00), 'NO06': (63.40, 10.40),
    # Poland
    'PL21': (50.05, 19.95), 'PL22': (50.25, 19.00), 'PL41': (52.40, 16.90),
    'PL42': (53.45, 14.55), 'PL43': (51.95, 15.50), 'PL51': (51.10, 17.00),
    'PL52': (50.80, 16.00), 'PL61': (53.00, 18.60), 'PL62': (53.80, 20.50),
    'PL63': (54.35, 18.65), 'PL71': (51.75, 19.45), 'PL72': (51.40, 21.15),
    'PL81': (51.25, 22.55), 'PL82': (50.05, 22.00), 'PL84': (53.15, 23.15),
    'PL91': (52.20, 21.00), 'PL92': (52.40, 20.70),
    # Portugal
    'PT11': (41.20, -8.60), 'PT15': (38.75, -27.10), 'PT16': (40.00, -7.90),
    'PT17': (38.75, -9.15), 'PT18': (38.00, -7.90), 'PT20': (32.65, -16.90),
    # Romania
    'RO11': (46.75, 23.60), 'RO12': (46.25, 25.00), 'RO21': (47.15, 27.60),
    'RO22': (46.55, 27.00), 'RO31': (44.45, 26.10), 'RO32': (44.45, 26.10),
    'RO41': (44.20, 28.65), 'RO42': (44.40, 23.80),
    # Slovakia
    'SK01': (48.15, 17.10), 'SK02': (48.30, 17.90), 'SK03': (49.00, 19.30),
    'SK04': (48.70, 21.25),
    # Slovenia
    'SI03': (46.05, 14.50), 'SI04': (46.40, 15.60),
    # Spain
    'ES11': (42.90, -8.55), 'ES12': (43.30, -5.90), 'ES13': (43.15, -3.00),
    'ES21': (42.85, -2.70), 'ES22': (42.80, -1.65), 'ES23': (42.20, -0.90),
    'ES24': (41.65, -0.90), 'ES30': (40.40, -3.70), 'ES41': (42.00, -3.70),
    'ES42': (39.85, -4.05), 'ES43': (39.00, -6.00), 'ES51': (41.40, 2.17),
    'ES52': (38.35, -0.50), 'ES53': (39.60, 2.65), 'ES61': (36.70, -4.40),
    'ES62': (37.60, -1.00), 'ES63': (35.90, -5.30), 'ES64': (35.28, -2.95),
    'ES70': (28.15, -15.45),
    # Sweden
    'SE11': (59.33, 18.07), 'SE12': (58.80, 16.00), 'SE21': (56.05, 12.70),
    'SE22': (57.70, 12.00), 'SE23': (56.90, 15.60), 'SE31': (63.00, 17.00),
    'SE32': (60.70, 17.15), 'SE33': (66.50, 20.00),
    # United Kingdom (pre-Brexit reference)
    'UKC1': (55.00, -1.60), 'UKC2': (54.60, -1.25), 'UKD1': (54.00, -2.80),
    'UKD3': (53.45, -2.25), 'UKD4': (53.85, -2.30), 'UKD6': (53.25, -2.90),
    'UKD7': (53.00, -2.20), 'UKE1': (53.80, -1.55), 'UKE2': (53.55, -1.10),
    'UKE3': (54.00, -0.95), 'UKE4': (53.50, -1.60), 'UKF1': (52.95, -1.15),
    'UKF2': (52.65, -1.15), 'UKF3': (52.45, -0.55), 'UKG1': (52.50, -2.10),
    'UKG2': (52.50, -1.85), 'UKG3': (52.20, -1.55), 'UKH1': (52.20, 0.12),
    'UKH2': (52.00, 1.00), 'UKH3': (51.75, 0.45), 'UKI3': (51.50, -0.13),
    'UKI4': (51.45, -0.35), 'UKI5': (51.50, -0.05), 'UKI6': (51.35, 0.20),
    'UKI7': (51.30, -0.50), 'UKJ1': (51.75, -1.25), 'UKJ2': (51.05, -1.30),
    'UKJ3': (51.10, -0.35), 'UKJ4': (50.85, -0.95), 'UKK1': (51.45, -2.60),
    'UKK2': (51.10, -3.00), 'UKK3': (50.40, -4.40), 'UKK4': (50.75, -3.50),
    'UKL1': (51.60, -3.45), 'UKL2': (52.45, -3.50), 'UKM5': (55.95, -3.20),
    'UKM6': (57.50, -4.50), 'UKM7': (56.00, -3.40), 'UKM8': (56.00, -5.00),
    'UKM9': (55.85, -4.25), 'UKN0': (54.60, -6.65),
}


def load_nuts2_centroids(
    custom_centroids: Optional[Dict[str, Tuple[float, float]]] = None
) -> pd.DataFrame:
    """
    Load NUTS2 region centroids (latitude, longitude).

    Parameters
    ----------
    custom_centroids : dict, optional
        Custom centroid mappings to add/override defaults

    Returns
    -------
    pd.DataFrame
        Columns: nuts2_region, lat, lon
    """
    centroids = NUTS2_CENTROIDS.copy()

    if custom_centroids:
        centroids.update(custom_centroids)

    records = [
        {'nuts2_region': code, 'lat': lat, 'lon': lon}
        for code, (lat, lon) in centroids.items()
    ]

    return pd.DataFrame(records)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points in km.
    """
    R = 6371  # Earth radius in km

    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))

    return R * c


def _haversine_distance_matrix(coords: np.ndarray) -> np.ndarray:
    """
    Compute pairwise haversine distances in km between coordinates.

    Parameters
    ----------
    coords : np.ndarray
        Array of shape (n, 2) with [lat, lon] in degrees

    Returns
    -------
    np.ndarray
        Distance matrix in km
    """
    n = len(coords)
    R = 6371  # Earth radius in km

    # Convert to radians
    coords_rad = np.radians(coords)
    lat = coords_rad[:, 0]
    lon = coords_rad[:, 1]

    # Compute pairwise differences
    dlat = lat[:, np.newaxis] - lat[np.newaxis, :]
    dlon = lon[:, np.newaxis] - lon[np.newaxis, :]

    # Haversine formula
    a = np.sin(dlat / 2) ** 2 + np.cos(lat[:, np.newaxis]) * np.cos(lat[np.newaxis, :]) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))

    return R * c


def find_geographical_hotspots(
    clustered_data: pd.DataFrame,
    min_cluster: int,
    max_diameter_km: float = 400,
    min_regions: int = 3,
    aggregate_by: str = 'region',
    method: str = 'hierarchical'
) -> pd.DataFrame:
    """
    Find geographical concentrations of high-value regions.

    Uses hierarchical clustering with complete linkage to ensure all regions
    within a cluster are within max_diameter_km of each other (no chaining).

    Parameters
    ----------
    clustered_data : pd.DataFrame
        Data from apply_clustering() with cluster assignments
    min_cluster : int
        Minimum cluster number to consider as "high value"
    max_diameter_km : float
        Maximum distance (km) between ANY two regions in a cluster.
        This prevents the chaining problem of DBSCAN.
    min_regions : int
        Minimum number of regions to form a geographical cluster
    aggregate_by : str
        'region' to aggregate by NUTS2, 'combo' to keep Region×NACE×Waste detail
    method : str
        'hierarchical' (recommended) or 'dbscan'

    Returns
    -------
    pd.DataFrame
        Data with geo_cluster column (-1 = isolated/small cluster)
    """
    centroids_df = load_nuts2_centroids()

    # Filter to high-value items
    high_value = clustered_data[clustered_data['cluster'] >= min_cluster].copy()

    if aggregate_by == 'region':
        # Aggregate to region level
        region_data = high_value.groupby(['nuts2_region', 'nuts2_name', 'country_code']).agg({
            'allocated_waste_tonnes': 'sum',
            'economic_potential_eur': 'sum',
            'nace_r2': 'nunique',
            'waste': 'nunique',
            'cluster': ['count', 'max']
        }).reset_index()
        region_data.columns = [
            'nuts2_region', 'nuts2_name', 'country_code',
            'total_waste_tonnes', 'total_economic_eur',
            'n_nace', 'n_waste', 'n_hotspot_combos', 'max_cluster'
        ]
        data_to_cluster = region_data
        combo_mode = False
    else:
        # For 'combo' mode, we cluster unique regions then map back to all combos
        # This avoids memory explosion from computing distances between identical coords
        combo_mode = True
        combo_data = high_value.copy()

        # Get unique regions for clustering
        region_data = high_value.groupby(['nuts2_region', 'nuts2_name', 'country_code']).agg({
            'allocated_waste_tonnes': 'sum',
            'economic_potential_eur': 'sum',
        }).reset_index()
        data_to_cluster = region_data

    # Merge with centroids
    data_with_coords = data_to_cluster.merge(
        centroids_df,
        on='nuts2_region',
        how='left'
    )

    # Drop regions without coordinates
    missing_coords = data_with_coords['lat'].isna()
    if missing_coords.any():
        missing = data_with_coords[missing_coords]['nuts2_region'].unique()
        print(f"Warning: {len(missing)} regions without coordinates: {list(missing)[:10]}...")
        data_with_coords = data_with_coords[~missing_coords].copy()

    if len(data_with_coords) < min_regions:
        print(f"Warning: Only {len(data_with_coords)} regions with coordinates, cannot cluster")
        data_with_coords['geo_cluster'] = -1
        if combo_mode:
            # Map back to combo data
            region_to_cluster = data_with_coords.set_index('nuts2_region')['geo_cluster']
            combo_data['geo_cluster'] = combo_data['nuts2_region'].map(region_to_cluster)
            return combo_data
        return data_with_coords

    coords = data_with_coords[['lat', 'lon']].values

    if method == 'hierarchical':
        # Compute haversine distance matrix
        dist_matrix = _haversine_distance_matrix(coords)

        # Hierarchical clustering with complete linkage
        # Complete linkage ensures max distance within cluster <= threshold
        condensed_dist = squareform(dist_matrix)
        Z = linkage(condensed_dist, method='complete')

        # Cut tree at max_diameter_km
        labels = fcluster(Z, t=max_diameter_km, criterion='distance')

        # Convert to 0-indexed, mark small clusters as -1
        cluster_counts = pd.Series(labels).value_counts()
        small_clusters = cluster_counts[cluster_counts < min_regions].index

        final_labels = []
        cluster_mapping = {}
        next_cluster = 0

        for label in labels:
            if label in small_clusters:
                final_labels.append(-1)
            else:
                if label not in cluster_mapping:
                    cluster_mapping[label] = next_cluster
                    next_cluster += 1
                final_labels.append(cluster_mapping[label])

        data_with_coords['geo_cluster'] = final_labels

    else:  # dbscan
        coords_rad = np.radians(coords)
        eps_rad = max_diameter_km / 2 / 6371.0  # Use half diameter as eps

        dbscan = DBSCAN(eps=eps_rad, min_samples=min_regions, metric='haversine')
        data_with_coords['geo_cluster'] = dbscan.fit_predict(coords_rad)

    n_clusters = len(set(data_with_coords['geo_cluster'])) - (1 if -1 in data_with_coords['geo_cluster'].values else 0)
    n_noise = (data_with_coords['geo_cluster'] == -1).sum()

    print(f"Found {n_clusters} geographical clusters, {n_noise} isolated/small-cluster regions")

    if combo_mode:
        # Map geo_cluster from regions back to all combos
        region_to_cluster = data_with_coords.set_index('nuts2_region')['geo_cluster']
        combo_data['geo_cluster'] = combo_data['nuts2_region'].map(region_to_cluster)
        # Fill any missing (regions dropped for missing coords) with -1
        combo_data['geo_cluster'] = combo_data['geo_cluster'].fillna(-1).astype(int)
        print(f"Mapped geo_clusters to {len(combo_data):,} region×NACE×waste combinations")
        return combo_data

    return data_with_coords


def get_hotspot_summary(
    geo_clustered: pd.DataFrame,
    include_isolated: bool = False
) -> pd.DataFrame:
    """
    Summarize geographical hotspot clusters.

    Parameters
    ----------
    geo_clustered : pd.DataFrame
        Output from find_geographical_hotspots()
    include_isolated : bool
        Whether to include isolated regions (geo_cluster=-1)

    Returns
    -------
    pd.DataFrame
        Summary by geographical cluster
    """
    if not include_isolated:
        data = geo_clustered[geo_clustered['geo_cluster'] >= 0]
    else:
        data = geo_clustered

    # Determine which columns exist
    value_col = 'total_economic_eur' if 'total_economic_eur' in data.columns else 'economic_potential_eur'
    waste_col = 'total_waste_tonnes' if 'total_waste_tonnes' in data.columns else 'allocated_waste_tonnes'

    summary = data.groupby('geo_cluster').agg({
        'nuts2_region': ['count', lambda x: ', '.join(sorted(x))],
        'country_code': lambda x: ', '.join(sorted(x.unique())),
        value_col: 'sum',
        waste_col: 'sum',
        'lat': 'mean',
        'lon': 'mean',
    }).reset_index()

    summary.columns = [
        'geo_cluster', 'n_regions', 'regions', 'countries',
        'total_economic_eur', 'total_waste_tonnes',
        'centroid_lat', 'centroid_lon'
    ]

    return summary.sort_values('total_economic_eur', ascending=False)


def get_cross_border_hotspots(
    geo_clustered: pd.DataFrame,
    min_countries: int = 2
) -> pd.DataFrame:
    """
    Identify geographical hotspots that span multiple countries.

    Parameters
    ----------
    geo_clustered : pd.DataFrame
        Output from find_geographical_hotspots()
    min_countries : int
        Minimum number of countries to qualify as cross-border

    Returns
    -------
    pd.DataFrame
        Cross-border hotspot clusters
    """
    # Get clusters (excluding noise)
    clusters = geo_clustered[geo_clustered['geo_cluster'] >= 0]

    # Count countries per cluster
    country_counts = clusters.groupby('geo_cluster')['country_code'].nunique()

    # Filter to cross-border
    cross_border_clusters = country_counts[country_counts >= min_countries].index

    return clusters[clusters['geo_cluster'].isin(cross_border_clusters)].copy()


def calculate_cluster_density(
    geo_clustered: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate economic density (EUR per km^2) for each geographical cluster.

    Returns DataFrame with density metrics per cluster.
    """
    summaries = []

    for cluster_id in geo_clustered['geo_cluster'].unique():
        if cluster_id == -1:
            continue

        cluster_data = geo_clustered[geo_clustered['geo_cluster'] == cluster_id]

        # Calculate approximate area using bounding box
        lat_range = cluster_data['lat'].max() - cluster_data['lat'].min()
        lon_range = cluster_data['lon'].max() - cluster_data['lon'].min()

        # Convert to approximate km (rough approximation)
        lat_km = lat_range * 111  # 1 degree lat ~ 111 km
        avg_lat = cluster_data['lat'].mean()
        lon_km = lon_range * 111 * np.cos(np.radians(avg_lat))

        # Area with minimum of 100 km^2
        area_km2 = max(lat_km * lon_km, 100)

        value_col = 'total_economic_eur' if 'total_economic_eur' in cluster_data.columns else 'economic_potential_eur'
        total_value = cluster_data[value_col].sum()

        summaries.append({
            'geo_cluster': cluster_id,
            'n_regions': len(cluster_data),
            'area_km2': area_km2,
            'total_economic_eur': total_value,
            'density_eur_per_km2': total_value / area_km2,
        })

    return pd.DataFrame(summaries).sort_values('density_eur_per_km2', ascending=False)
