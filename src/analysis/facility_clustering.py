"""
facility_clustering.py

Hierarchical clustering of facility-level waste data to identify
major hotspots of similar waste production based on NACE2, IED activity,
and waste code dimensions.
"""

from pathlib import Path

import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
from scipy.spatial.distance import squareform

from ..loaders.io import PROCESSED_DIR
from ..mappings.ied_nace import get_nace_description, get_ied_description
from ..mappings.ewc_stat import get_ewc_description


def _detect_data_format(df: pd.DataFrame) -> str:
    """Detect whether DataFrame is wide or long format."""
    has_alloc_cols = any(c.startswith('alloc_') and c.endswith('_tonnes') for c in df.columns)
    has_long_cols = 'waste_type' in df.columns and 'allocated_tonnes' in df.columns

    if has_alloc_cols and not has_long_cols:
        return 'wide'
    elif has_long_cols:
        return 'long'
    raise ValueError("Unknown format: missing alloc_*_tonnes or waste_type/allocated_tonnes")


def _convert_wide_to_long(df: pd.DataFrame, include_zero: bool = False) -> pd.DataFrame:
    """Convert wide-format classified data to long format."""
    alloc_cols = [c for c in df.columns if c.startswith('alloc_') and c.endswith('_tonnes')]

    id_vars = ['facility_id', 'facility_name', 'country', 'lat', 'lon']
    if 'ied_code' in df.columns:
        id_vars.append('ied_code')
    if 'nace_primary' in df.columns:
        id_vars.append('nace_primary')
    if 'recovery_maturity_indicator' in df.columns:
        id_vars.append('recovery_maturity_indicator')

    long_df = df.melt(
        id_vars=id_vars,
        value_vars=alloc_cols,
        var_name='waste_col',
        value_name='allocated_tonnes'
    )

    # Extract waste_type: alloc_W011_tonnes -> W011
    long_df['waste_type'] = long_df['waste_col'].str.replace('alloc_', '').str.replace('_tonnes', '')
    long_df = long_df.drop(columns=['waste_col'])

    # Rename columns to match expected schema
    long_df = long_df.rename(columns={'ied_code': 'ied_activity', 'nace_primary': 'nace'})

    # Convert nace to string format (handles float values like 24.1)
    if 'nace' in long_df.columns:
        long_df['nace'] = long_df['nace'].apply(
            lambda x: f"C{x:.1f}".replace('.0', '') if pd.notna(x) else 'unknown'
        )

    # Convert ied_activity to string format
    if 'ied_activity' in long_df.columns:
        long_df['ied_activity'] = long_df['ied_activity'].fillna('unknown').astype(str)

    if not include_zero:
        long_df = long_df[long_df['allocated_tonnes'] > 0]

    return long_df


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
        Distance matrix of shape (n, n) in km
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


def load_and_filter_facilities(
    data_path: Optional[str] = None,
    min_tonnes: float = 5000
) -> pd.DataFrame:
    """
    Load facility data and filter to facilities with >= min_tonnes allocated waste.

    Parameters
    ----------
    data_path : str, optional
        Path to facility_waste_allocated.csv. Defaults to standard processed location.
    min_tonnes : float
        Minimum total allocated tonnes to include facility (default 5000)

    Returns
    -------
    pd.DataFrame
        Filtered facility data (all rows for facilities meeting threshold)
    """
    if data_path is None:
        data_path = PROCESSED_DIR / "facility_waste_allocated.csv"

    df = pd.read_csv(data_path)

    # Detect format and convert if needed
    data_format = _detect_data_format(df)
    if data_format == 'wide':
        print(f"Detected wide format, converting to long format...")
        df = _convert_wide_to_long(df)
        print(f"Converted to {len(df):,} rows")

    # Calculate total allocated tonnes per facility
    facility_totals = df.groupby('facility_id')['allocated_tonnes'].sum()
    qualifying_facilities = facility_totals[facility_totals >= min_tonnes].index

    # Filter to qualifying facilities
    filtered = df[df['facility_id'].isin(qualifying_facilities)].copy()

    # Remove facilities with missing coordinates (required for geographic clustering)
    missing_coords = filtered.groupby('facility_id')[['lat', 'lon']].first()
    missing_coords_ids = missing_coords[missing_coords['lat'].isna() | missing_coords['lon'].isna()].index
    if len(missing_coords_ids) > 0:
        filtered = filtered[~filtered['facility_id'].isin(missing_coords_ids)]
        print(f"Removed {len(missing_coords_ids)} facilities with missing coordinates")

    n_original = df['facility_id'].nunique()
    n_filtered = filtered['facility_id'].nunique()
    print(f"Filtered from {n_original:,} to {n_filtered:,} facilities (>= {min_tonnes:,.0f} tonnes)")

    return filtered


def _extract_ied_major_category(ied_activity: str) -> str:
    """
    Extract major IED category (1.x, 2.x, etc.) from IED activity code.

    Parameters
    ----------
    ied_activity : str
        Full IED activity code like '6.6(a)', '1.1', '2.5(b)'

    Returns
    -------
    str
        Major category like 'IED_1', 'IED_2', 'IED_6'
    """
    if pd.isna(ied_activity):
        return 'IED_unknown'

    ied_str = str(ied_activity).strip()
    if not ied_str or ied_str == '':
        return 'IED_unknown'

    # Extract first number before any decimal or parenthesis
    first_char = ied_str[0]
    if first_char.isdigit():
        return f'IED_{first_char}'

    return 'IED_unknown'


def create_facility_feature_matrix(
    df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    """
    Create feature matrix for facility clustering.

    Aggregates waste data by facility and creates features for:
    - Waste type proportions (one column per waste type)
    - One-hot encoded NACE codes
    - One-hot encoded IED major categories
    - Log-transformed total volume

    Parameters
    ----------
    df : pd.DataFrame
        Facility waste data from load_and_filter_facilities()

    Returns
    -------
    tuple
        (facility_info_df, feature_matrix_df, coords)
        - facility_info_df: Facility metadata (id, name, country, lat, lon, total_tonnes)
        - feature_matrix_df: Feature matrix indexed by facility_id
        - coords: Array of shape (n_facilities, 2) with [lat, lon] for geographic constraints
    """
    # Aggregate total tonnes per facility
    facility_totals = df.groupby('facility_id')['allocated_tonnes'].sum().rename('total_tonnes')

    # Get facility info (first row per facility for metadata)
    agg_dict = {
        'facility_name': 'first',
        'country': 'first',
        'lat': 'first',
        'lon': 'first',
        'nace': 'first',  # Primary NACE
        'ied_activity': 'first',  # Primary IED
    }
    if 'recovery_maturity_indicator' in df.columns:
        agg_dict['recovery_maturity_indicator'] = 'first'
    facility_info = df.groupby('facility_id').agg(agg_dict).reset_index()

    facility_info = facility_info.merge(facility_totals, on='facility_id')

    # Create waste type proportions
    waste_pivot = df.pivot_table(
        index='facility_id',
        columns='waste_type',
        values='allocated_tonnes',
        aggfunc='sum',
        fill_value=0
    )

    # Convert to proportions (sum to 1 per facility)
    waste_proportions = waste_pivot.div(waste_pivot.sum(axis=1), axis=0)
    waste_proportions.columns = [f'waste_{col}' for col in waste_proportions.columns]

    # One-hot encode NACE codes
    nace_dummies = pd.get_dummies(
        df.groupby('facility_id')['nace'].first(),
        prefix='nace'
    )

    # One-hot encode IED major categories
    df_with_ied_cat = df.copy()
    df_with_ied_cat['ied_major'] = df_with_ied_cat['ied_activity'].apply(_extract_ied_major_category)

    ied_dummies = pd.get_dummies(
        df_with_ied_cat.groupby('facility_id')['ied_major'].first(),
        prefix='ied'
    )

    # Log-transformed total volume
    log_volume = np.log10(facility_totals + 1).rename('log_total_volume')

    # Combine all features
    feature_matrix = waste_proportions.join(nace_dummies).join(ied_dummies).join(log_volume)

    # Fill any NaN with 0 (shouldn't happen but defensive)
    feature_matrix = feature_matrix.fillna(0)

    print(f"Feature matrix shape: {feature_matrix.shape}")
    print(f"  - Waste type features: {len([c for c in feature_matrix.columns if c.startswith('waste_')])}")
    print(f"  - NACE features: {len([c for c in feature_matrix.columns if c.startswith('nace_')])}")
    print(f"  - IED features: {len([c for c in feature_matrix.columns if c.startswith('ied_')])}")
    print(f"  - Volume feature: 1")

    # Extract coordinates for geographic constraints (ordered by facility_id to match feature_matrix index)
    facility_info_indexed = facility_info.set_index('facility_id').loc[feature_matrix.index]
    coords = facility_info_indexed[['lat', 'lon']].values

    return facility_info, feature_matrix, coords


def apply_hierarchical_clustering(
    features: pd.DataFrame,
    coords: Optional[np.ndarray] = None,
    max_distance_km: Optional[float] = None,
    geo_mode: str = 'none',
    method: str = 'ward',
    k_range: range = range(3, 13),
    random_state: int = 42
) -> Tuple[np.ndarray, Optional[np.ndarray], int, float, Optional[np.ndarray]]:
    """
    Apply agglomerative hierarchical clustering with automatic k selection.

    Supports three geographic modes:
    - 'none': Unconstrained clustering by features only (best silhouette)
    - 'geo_first': Geography → Features (current implementation, geographically actionable)
    - 'features_first': Features → Geographic sub-groups (preserve cluster identity + geo context)

    Parameters
    ----------
    features : pd.DataFrame
        Feature matrix from create_facility_feature_matrix()
    coords : np.ndarray, optional
        Array of shape (n, 2) with [lat, lon] for geographic constraints
    max_distance_km : float, optional
        Maximum distance in km between facilities in the same cluster.
        Required for 'geo_first' and 'features_first' modes.
    geo_mode : str
        Geographic clustering mode: 'none', 'geo_first', or 'features_first'
    method : str
        Linkage method for hierarchical clustering ('ward', 'complete', 'average')
    k_range : range
        Range of cluster counts to evaluate
    random_state : int
        Random seed for reproducibility

    Returns
    -------
    tuple
        (labels, linkage_matrix, optimal_k, silhouette_score, geo_subgroups)
        - labels: Cluster assignments (0-indexed)
        - linkage_matrix: Scipy linkage matrix for dendrogram
        - optimal_k: Best number of clusters found
        - silhouette_score: Silhouette score for optimal clustering
        - geo_subgroups: Geographic subgroup labels (only for 'features_first' mode, else None)
    """
    # Validate geo_mode
    valid_modes = ('none', 'geo_first', 'features_first')
    if geo_mode not in valid_modes:
        raise ValueError(f"geo_mode must be one of {valid_modes}, got '{geo_mode}'")

    # Check requirements for geographic modes
    if geo_mode in ('geo_first', 'features_first'):
        if coords is None or max_distance_km is None:
            raise ValueError(f"geo_mode='{geo_mode}' requires both coords and max_distance_km")

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features.values)

    geo_subgroups = None  # Only populated for features_first mode

    if geo_mode == 'geo_first':
        # TWO-STAGE CLUSTERING: Geography first, then features
        # This GUARANTEES max distance within any cluster <= max_distance_km

        print(f"Mode: geo_first - Geographic constraint: max {max_distance_km} km between facilities")

        # STAGE 1: Geographic clustering with complete linkage
        # Complete linkage ensures max pairwise distance = cut threshold
        dist_matrix = _haversine_distance_matrix(coords)
        condensed_dist = squareform(dist_matrix)
        Z_geo = linkage(condensed_dist, method='complete')

        # Cut dendrogram at max_distance_km - this GUARANTEES max diameter
        geo_labels = fcluster(Z_geo, t=max_distance_km, criterion='distance') - 1

        n_geo_clusters = len(np.unique(geo_labels))
        print(f"Geographic clustering: {n_geo_clusters} regions (max diameter {max_distance_km} km)")

        # STAGE 2: Feature-based sub-clustering within each geographic region
        final_labels = np.zeros(len(features), dtype=int)
        cluster_offset = 0

        for geo_id in np.unique(geo_labels):
            geo_mask = geo_labels == geo_id
            n_in_region = geo_mask.sum()

            if n_in_region == 1:
                # Single facility - assign unique cluster
                final_labels[geo_mask] = cluster_offset
                cluster_offset += 1
            else:
                # Sub-cluster by features within this region
                X_region = X_scaled[geo_mask]

                # Determine k range for this region (proportional to size)
                max_k = min(n_in_region - 1, max(k_range))
                min_k = min(k_range)
                region_k_range = range(min_k, min(max_k + 1, n_in_region))

                if len(region_k_range) < 2:
                    # Too small to sub-cluster meaningfully
                    final_labels[geo_mask] = cluster_offset
                    cluster_offset += 1
                else:
                    # Find optimal k for this region using silhouette score
                    best_k, best_score = min_k, -1
                    for k in region_k_range:
                        model = AgglomerativeClustering(n_clusters=k, linkage='ward')
                        sub_labels = model.fit_predict(X_region)
                        if len(np.unique(sub_labels)) > 1:
                            score = silhouette_score(X_region, sub_labels)
                            if score > best_score:
                                best_k, best_score = k, score

                    model = AgglomerativeClustering(n_clusters=best_k, linkage='ward')
                    sub_labels = model.fit_predict(X_region)

                    # Assign with offset to ensure unique cluster IDs
                    final_labels[geo_mask] = sub_labels + cluster_offset
                    cluster_offset += len(np.unique(sub_labels))

        labels = final_labels
        optimal_k = len(np.unique(labels))

        # Calculate overall silhouette score
        if optimal_k > 1:
            sil_score = silhouette_score(X_scaled, labels)
        else:
            sil_score = 0.0

        # Generate linkage matrix for visualization (on features, without constraints)
        Z = linkage(X_scaled, method=method)

        print(f"Two-stage clustering result: {optimal_k} final clusters")
        print(f"Overall silhouette score: {sil_score:.3f}")

        # Verify geographic constraint is satisfied
        _verify_cluster_distances(coords, labels, max_distance_km)

    elif geo_mode == 'features_first':
        # TWO-STAGE CLUSTERING: Features first, then geographic sub-groups
        # Preserves cluster identity (good silhouette) + adds geographic context

        print(f"Mode: features_first - Unconstrained clustering, then geographic sub-grouping")

        # STAGE 1: Unconstrained feature-based clustering (for best silhouette)
        Z = linkage(X_scaled, method=method)

        # Evaluate different k values
        silhouettes = []
        for k in k_range:
            temp_labels = fcluster(Z, t=k, criterion='maxclust') - 1

            if len(np.unique(temp_labels)) > 1:
                score = silhouette_score(X_scaled, temp_labels)
            else:
                score = -1

            silhouettes.append(score)

        # Find optimal k
        best_idx = np.argmax(silhouettes)
        optimal_k = list(k_range)[best_idx]
        sil_score = silhouettes[best_idx]

        # Get final labels with optimal k
        labels = fcluster(Z, t=optimal_k, criterion='maxclust') - 1

        print(f"Feature clustering: k={optimal_k} with silhouette score={sil_score:.3f}")
        print(f"Silhouette scores by k: {dict(zip(k_range, [f'{s:.3f}' for s in silhouettes]))}")

        # STAGE 2: Geographic sub-grouping within each feature cluster
        # Use complete linkage on geographic distances, cut at max_distance_km
        dist_matrix = _haversine_distance_matrix(coords)
        geo_subgroups = np.zeros(len(features), dtype=object)

        print(f"\nApplying geographic sub-grouping within each cluster (max {max_distance_km} km):")
        for cluster_id in np.unique(labels):
            cluster_mask = labels == cluster_id
            cluster_indices = np.where(cluster_mask)[0]
            n_in_cluster = len(cluster_indices)

            if n_in_cluster == 1:
                # Single facility - one sub-group
                geo_subgroups[cluster_mask] = f"{cluster_id}a"
            else:
                # Get geographic distances within this cluster
                cluster_dists = dist_matrix[np.ix_(cluster_indices, cluster_indices)]
                condensed_dist = squareform(cluster_dists)

                # Complete linkage ensures max pairwise distance in sub-group
                Z_geo = linkage(condensed_dist, method='complete')

                # Cut at max_distance_km
                sub_labels = fcluster(Z_geo, t=max_distance_km, criterion='distance') - 1
                n_subgroups = len(np.unique(sub_labels))

                # Assign sub-group labels like "3a", "3b", "3c"
                for i, idx in enumerate(cluster_indices):
                    subgroup_letter = chr(ord('a') + sub_labels[i])
                    geo_subgroups[idx] = f"{cluster_id}{subgroup_letter}"

                if n_subgroups > 1:
                    print(f"  Cluster {cluster_id}: {n_in_cluster} facilities -> {n_subgroups} sub-groups")

    else:  # geo_mode == 'none'
        # STANDARD CLUSTERING: No geographic constraints
        print("Mode: none - Unconstrained feature-based clustering")

        Z = linkage(X_scaled, method=method)

        # Evaluate different k values
        silhouettes = []
        for k in k_range:
            temp_labels = fcluster(Z, t=k, criterion='maxclust') - 1  # 0-indexed

            if len(np.unique(temp_labels)) > 1:
                score = silhouette_score(X_scaled, temp_labels)
            else:
                score = -1

            silhouettes.append(score)

        # Find optimal k
        best_idx = np.argmax(silhouettes)
        optimal_k = list(k_range)[best_idx]
        sil_score = silhouettes[best_idx]

        # Get final labels with optimal k
        labels = fcluster(Z, t=optimal_k, criterion='maxclust') - 1  # 0-indexed

        print(f"Optimal k={optimal_k} with silhouette score={sil_score:.3f}")
        print(f"Silhouette scores by k: {dict(zip(k_range, [f'{s:.3f}' for s in silhouettes]))}")

    return labels, Z, optimal_k, sil_score, geo_subgroups


def _verify_cluster_distances(
    coords: np.ndarray,
    labels: np.ndarray,
    max_distance_km: float
) -> None:
    """
    Verify that all facilities within each cluster are within max_distance_km of each other.
    Prints a warning if any cluster violates the constraint.
    """
    dist_matrix = _haversine_distance_matrix(coords)
    violations = []

    for cluster_id in np.unique(labels):
        cluster_mask = labels == cluster_id
        cluster_indices = np.where(cluster_mask)[0]

        if len(cluster_indices) > 1:
            # Get max distance within this cluster
            cluster_dists = dist_matrix[np.ix_(cluster_indices, cluster_indices)]
            max_dist = cluster_dists.max()

            if max_dist > max_distance_km:
                violations.append((cluster_id, max_dist, len(cluster_indices)))

    if violations:
        print(f"Warning: {len(violations)} clusters exceed max_distance_km constraint:")
        for cluster_id, max_dist, n_facilities in violations[:5]:  # Show first 5
            print(f"  Cluster {cluster_id}: max distance {max_dist:.1f} km ({n_facilities} facilities)")
    else:
        print(f"All clusters satisfy the {max_distance_km} km distance constraint")


def filter_clusters_by_tonnage(
    labels: np.ndarray,
    facility_info: pd.DataFrame,
    min_cluster_tonnes: float,
    geo_subgroups: Optional[np.ndarray] = None
) -> Tuple[np.ndarray, pd.DataFrame, List[int], Optional[np.ndarray]]:
    """
    Remove clusters below minimum tonnage threshold.

    Parameters
    ----------
    labels : np.ndarray
        Cluster assignments (0-indexed)
    facility_info : pd.DataFrame
        Facility info dataframe with 'total_tonnes' column (indexed or with 'facility_id')
    min_cluster_tonnes : float
        Minimum total tonnes for a cluster to be retained
    geo_subgroups : np.ndarray, optional
        Geographic subgroup labels (for features_first mode)

    Returns
    -------
    tuple
        (filtered_labels, filtered_facility_info, discarded_cluster_ids, filtered_geo_subgroups)
        - filtered_labels: Renumbered cluster assignments (contiguous 0, 1, 2, ...)
        - filtered_facility_info: Facility info with discarded facilities removed
        - discarded_cluster_ids: List of original cluster IDs that were removed
        - filtered_geo_subgroups: Updated geo_subgroups (or None if input was None)
    """
    # Ensure we have facility_id as a column for consistent handling
    if 'facility_id' not in facility_info.columns:
        facility_df = facility_info.reset_index()
    else:
        facility_df = facility_info.copy()

    # Add cluster labels
    facility_df['cluster'] = labels
    if geo_subgroups is not None:
        facility_df['geo_subgroup'] = geo_subgroups

    # Calculate total tonnes per cluster
    cluster_tonnes = facility_df.groupby('cluster')['total_tonnes'].sum()

    # Identify clusters to keep and discard
    clusters_to_keep = cluster_tonnes[cluster_tonnes >= min_cluster_tonnes].index.tolist()
    discarded_clusters = cluster_tonnes[cluster_tonnes < min_cluster_tonnes].index.tolist()

    if discarded_clusters:
        discarded_tonnes = cluster_tonnes[discarded_clusters].sum()
        n_discarded_facilities = facility_df[facility_df['cluster'].isin(discarded_clusters)].shape[0]
        print(f"Filtering clusters below {min_cluster_tonnes:,.0f} tonnes:")
        print(f"  Discarding {len(discarded_clusters)} clusters ({n_discarded_facilities} facilities, {discarded_tonnes:,.0f} tonnes)")
        print(f"  Keeping {len(clusters_to_keep)} clusters")

    # Filter to kept clusters
    filtered_df = facility_df[facility_df['cluster'].isin(clusters_to_keep)].copy()

    # Renumber clusters to be contiguous (0, 1, 2, ...)
    old_to_new = {old_id: new_id for new_id, old_id in enumerate(sorted(clusters_to_keep))}
    filtered_df['cluster'] = filtered_df['cluster'].map(old_to_new)

    # Update geo_subgroups if present (replace old cluster ID with new one)
    filtered_geo_subgroups = None
    if geo_subgroups is not None:
        # Update subgroup labels like "3a" -> "1a" based on cluster renumbering
        def update_subgroup_label(label):
            if label is None:
                return None
            # Extract cluster number and letter
            for i, c in enumerate(label):
                if c.isalpha():
                    old_cluster = int(label[:i])
                    letter = label[i:]
                    if old_cluster in old_to_new:
                        return f"{old_to_new[old_cluster]}{letter}"
                    return None
            return label

        filtered_df['geo_subgroup'] = filtered_df['geo_subgroup'].apply(update_subgroup_label)
        filtered_geo_subgroups = filtered_df['geo_subgroup'].values

    # Extract arrays
    filtered_labels = filtered_df['cluster'].values

    # Remove temporary columns for return
    cols_to_drop = ['cluster']
    if 'geo_subgroup' in filtered_df.columns:
        cols_to_drop.append('geo_subgroup')
    filtered_facility_info = filtered_df.drop(columns=cols_to_drop)

    return filtered_labels, filtered_facility_info, discarded_clusters, filtered_geo_subgroups


def summarize_facility_clusters(
    facility_df: pd.DataFrame,
    feature_matrix: pd.DataFrame,
    labels: np.ndarray,
    top_n: int = 3
) -> pd.DataFrame:
    """
    Generate summary profiles for each facility cluster.

    Parameters
    ----------
    facility_df : pd.DataFrame
        Facility info from create_facility_feature_matrix()
    feature_matrix : pd.DataFrame
        Feature matrix (to identify dominant waste types)
    labels : np.ndarray
        Cluster assignments from apply_hierarchical_clustering()
    top_n : int
        Number of top items to report per category

    Returns
    -------
    pd.DataFrame
        Cluster summary with columns:
        - cluster: Cluster ID
        - n_facilities: Number of facilities
        - total_tonnes: Total allocated waste
        - dominant_nace: Most common NACE code(s)
        - nace_description: Human-readable NACE sector descriptions
        - dominant_ied: Most common IED category
        - ied_description: Human-readable IED activity descriptions
        - top_waste_types: Top waste types by proportion
        - waste_description: Human-readable EWC-Stat waste type descriptions
        - countries: Countries represented
        - centroid_lat, centroid_lon: Geographic centroid
    """
    # Add cluster labels to facility info
    facility_with_clusters = facility_df.set_index('facility_id').copy()
    facility_with_clusters['cluster'] = labels

    summaries = []

    for cluster_id in sorted(np.unique(labels)):
        cluster_facilities = facility_with_clusters[facility_with_clusters['cluster'] == cluster_id]
        cluster_features = feature_matrix.loc[cluster_facilities.index]

        # Basic stats
        n_facilities = len(cluster_facilities)
        total_tonnes = cluster_facilities['total_tonnes'].sum()

        # Dominant NACE (mode)
        nace_counts = cluster_facilities['nace'].value_counts()
        dominant_nace_codes = nace_counts.head(top_n).index.tolist()
        dominant_nace = ', '.join(dominant_nace_codes)

        # NACE descriptions
        nace_descriptions = [get_nace_description(code) for code in dominant_nace_codes]
        nace_description = '; '.join(nace_descriptions)

        # Dominant IED
        ied_categories = cluster_facilities['ied_activity'].apply(_extract_ied_major_category)
        ied_counts = ied_categories.value_counts()
        dominant_ied_codes = ied_counts.head(top_n).index.tolist()
        dominant_ied = ', '.join(dominant_ied_codes)

        # IED descriptions (from major category to chapter description)
        ied_chapter_names = {
            'IED_1': 'Energy industries',
            'IED_2': 'Metals production/processing',
            'IED_3': 'Mineral industry',
            'IED_4': 'Chemical industry',
            'IED_5': 'Waste management',
            'IED_6': 'Other activities (pulp, food, textiles)',
            'IED_unknown': 'Unknown/not classified',
        }
        ied_descriptions = [ied_chapter_names.get(code, code) for code in dominant_ied_codes]
        ied_description = '; '.join(ied_descriptions)

        # Top waste types (by mean proportion in cluster)
        waste_cols = [c for c in cluster_features.columns if c.startswith('waste_')]
        if waste_cols:
            mean_waste = cluster_features[waste_cols].mean()
            top_waste = mean_waste.nlargest(top_n)
            top_waste_types = ', '.join([
                f"{col.replace('waste_', '')}({val:.1%})"
                for col, val in top_waste.items()
            ])
            # Waste descriptions
            waste_codes = [col.replace('waste_', '') for col in top_waste.index]
            waste_descriptions = [get_ewc_description(code) for code in waste_codes]
            waste_description = '; '.join(waste_descriptions)
        else:
            top_waste_types = ''
            waste_description = ''

        # Countries
        countries = ', '.join(sorted(cluster_facilities['country'].unique()))

        # Geographic centroid
        centroid_lat = cluster_facilities['lat'].mean()
        centroid_lon = cluster_facilities['lon'].mean()

        summaries.append({
            'cluster': cluster_id,
            'n_facilities': n_facilities,
            'total_tonnes': total_tonnes,
            'dominant_nace': dominant_nace,
            'nace_description': nace_description,
            'dominant_ied': dominant_ied,
            'ied_description': ied_description,
            'top_waste_types': top_waste_types,
            'waste_description': waste_description,
            'countries': countries,
            'centroid_lat': centroid_lat,
            'centroid_lon': centroid_lon,
        })

    summary_df = pd.DataFrame(summaries)
    summary_df = summary_df.sort_values('total_tonnes', ascending=False)

    return summary_df


def save_clustering_results(
    facility_df: pd.DataFrame,
    labels: np.ndarray,
    summary_df: pd.DataFrame,
    output_dir: Optional[str] = None,
    geo_subgroups: Optional[np.ndarray] = None
) -> Tuple[str, str]:
    """
    Save clustering results to CSV files.

    Parameters
    ----------
    facility_df : pd.DataFrame
        Facility info dataframe
    labels : np.ndarray
        Cluster assignments
    summary_df : pd.DataFrame
        Cluster summary dataframe
    output_dir : str, optional
        Output directory. Defaults to processed data directory.
    geo_subgroups : np.ndarray, optional
        Geographic subgroup labels (e.g., "3a", "3b") for features_first mode

    Returns
    -------
    tuple
        (clusters_path, summary_path) - Paths to saved files
    """
    if output_dir is None:
        output_dir = PROCESSED_DIR

    # Add cluster labels to facility data
    facility_with_clusters = facility_df.copy()
    facility_with_clusters['cluster'] = labels

    # Add geo_subgroup column if provided
    if geo_subgroups is not None:
        facility_with_clusters['geo_subgroup'] = geo_subgroups

    # Add NACE description
    facility_with_clusters['nace_description'] = facility_with_clusters['nace'].apply(get_nace_description)

    # Add IED description
    ied_chapter_names = {
        'IED_1': 'Energy industries',
        'IED_2': 'Metals production/processing',
        'IED_3': 'Mineral industry',
        'IED_4': 'Chemical industry',
        'IED_5': 'Waste management',
        'IED_6': 'Other activities (pulp, food, textiles)',
        'IED_unknown': 'Unknown/not classified',
    }
    facility_with_clusters['ied_major'] = facility_with_clusters['ied_activity'].apply(_extract_ied_major_category)
    facility_with_clusters['ied_description'] = facility_with_clusters['ied_major'].map(ied_chapter_names)
    facility_with_clusters = facility_with_clusters.drop(columns=['ied_major'])

    clusters_path = output_dir / "facility_clusters.csv"
    summary_path = output_dir / "facility_cluster_summary.csv"

    facility_with_clusters.to_csv(clusters_path, index=False)
    summary_df.to_csv(summary_path, index=False)

    print(f"Saved facility clusters to: {clusters_path}")
    print(f"Saved cluster summary to: {summary_path}")

    return str(clusters_path), str(summary_path)


def plot_facility_clusters(
    facility_df: pd.DataFrame,
    labels: np.ndarray,
    linkage_matrix: Optional[np.ndarray],
    summary_df: pd.DataFrame,
    output_path: Optional[str] = None
):
    """
    Create visualization of facility clustering results.

    Produces a figure with four subplots:
    1. Dendrogram showing hierarchical structure (or note if using connectivity constraints)
    2. Geographic scatter plot of facilities colored by cluster
    3. Cluster composition bar chart
    4. Total waste by cluster

    Parameters
    ----------
    facility_df : pd.DataFrame
        Facility info dataframe
    labels : np.ndarray
        Cluster assignments
    linkage_matrix : np.ndarray, optional
        Scipy linkage matrix from apply_hierarchical_clustering().
        May be None if connectivity constraints were used.
    summary_df : pd.DataFrame
        Cluster summary from summarize_facility_clusters()
    output_path : str, optional
        Path to save figure. Defaults to reports/figures/facility_clustering_results.png

    Returns
    -------
    matplotlib.figure.Figure
        The generated figure
    """
    import matplotlib.pyplot as plt
    from scipy.cluster.hierarchy import dendrogram

    if output_path is None:
        output_path = PROCESSED_DIR.parent.parent / "reports" / "figures" / "facility_clustering_results.png"

    # Prepare data
    facility_with_clusters = facility_df.copy()
    facility_with_clusters['cluster'] = labels
    n_clusters = len(np.unique(labels))

    # Create figure with subplots
    fig = plt.figure(figsize=(16, 12))

    # Subplot 1: Dendrogram
    ax1 = fig.add_subplot(2, 2, 1)
    if linkage_matrix is not None:
        dendrogram(
            linkage_matrix,
            truncate_mode='lastp',
            p=30,  # Show only last 30 merges
            leaf_rotation=90,
            leaf_font_size=8,
            ax=ax1
        )
        ax1.set_title('Hierarchical Clustering Dendrogram', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Cluster Size')
        ax1.set_ylabel('Distance')
    else:
        ax1.text(0.5, 0.5, 'Dendrogram not available\n(connectivity-constrained clustering)',
                 ha='center', va='center', fontsize=12, transform=ax1.transAxes)
        ax1.set_title('Dendrogram', fontsize=12, fontweight='bold')
        ax1.axis('off')

    # Subplot 2: Geographic scatter plot
    ax2 = fig.add_subplot(2, 2, 2)
    colors = plt.cm.tab10(np.linspace(0, 1, n_clusters))

    for cluster_id in sorted(np.unique(labels)):
        cluster_data = facility_with_clusters[facility_with_clusters['cluster'] == cluster_id]
        ax2.scatter(
            cluster_data['lon'],
            cluster_data['lat'],
            c=[colors[cluster_id]],
            label=f'Cluster {cluster_id}',
            alpha=0.7,
            s=50
        )

    ax2.set_xlabel('Longitude')
    ax2.set_ylabel('Latitude')
    ax2.set_title('Facility Locations by Cluster', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper left', fontsize=8)
    ax2.grid(True, alpha=0.3)

    # Subplot 3: Cluster composition - number of facilities
    ax3 = fig.add_subplot(2, 2, 3)
    cluster_counts = facility_with_clusters.groupby('cluster').size()
    bars = ax3.bar(
        cluster_counts.index,
        cluster_counts.values,
        color=[colors[i] for i in cluster_counts.index]
    )
    ax3.set_xlabel('Cluster')
    ax3.set_ylabel('Number of Facilities')
    ax3.set_title('Facilities per Cluster', fontsize=12, fontweight='bold')
    ax3.set_xticks(range(n_clusters))

    # Add count labels on bars
    for bar, count in zip(bars, cluster_counts.values):
        ax3.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            str(count),
            ha='center',
            va='bottom',
            fontsize=9
        )

    # Subplot 4: Total tonnes by cluster
    ax4 = fig.add_subplot(2, 2, 4)
    cluster_tonnes = facility_with_clusters.groupby('cluster')['total_tonnes'].sum()
    bars = ax4.bar(
        cluster_tonnes.index,
        cluster_tonnes.values / 1e6,  # Convert to millions
        color=[colors[i] for i in cluster_tonnes.index]
    )
    ax4.set_xlabel('Cluster')
    ax4.set_ylabel('Total Waste (Million Tonnes)')
    ax4.set_title('Total Waste by Cluster', fontsize=12, fontweight='bold')
    ax4.set_xticks(range(n_clusters))

    # Add value labels on bars
    for bar, tonnes in zip(bars, cluster_tonnes.values):
        ax4.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.02 * max(cluster_tonnes.values / 1e6),
            f'{tonnes / 1e6:.2f}M',
            ha='center',
            va='bottom',
            fontsize=9
        )

    plt.tight_layout()

    # Save figure
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved visualization to: {output_path}")

    return fig


def plot_features_first_subgroups(
    facility_df: pd.DataFrame,
    labels: np.ndarray,
    geo_subgroups: np.ndarray,
    summary_df: pd.DataFrame,
    min_subgroup_tonnes: float = 100000,
    output_path: Optional[str] = None
) -> 'Figure':
    """
    Create map visualization of features_first clustering subgroups.

    Shows actionable geographic hotspots where concentrated waste streams
    exist within 300km regions. Each subgroup marker represents the centroid
    of facilities in that subgroup.

    Parameters
    ----------
    facility_df : pd.DataFrame
        Facility info dataframe with columns: facility_id, lat, lon, total_tonnes
    labels : np.ndarray
        Cluster assignments (0-indexed)
    geo_subgroups : np.ndarray
        Geographic subgroup labels (e.g., "0a", "1b", "3c") from features_first mode
    summary_df : pd.DataFrame
        Cluster summary with 'cluster' and 'top_waste_types' columns for legend
    min_subgroup_tonnes : float
        Only annotate subgroups with total tonnes >= this threshold
    output_path : str, optional
        Path to save figure. Defaults to reports/figures/features_first_subgroups.png

    Returns
    -------
    matplotlib.figure.Figure
        The generated figure
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    from matplotlib.lines import Line2D
    import matplotlib.patches as mpatches

    if output_path is None:
        output_path = PROCESSED_DIR.parent.parent / "reports" / "figures" / "features_first_subgroups.png"

    # Prepare facility data with clustering info
    facility_with_clusters = facility_df.copy()
    facility_with_clusters['cluster'] = labels
    facility_with_clusters['geo_subgroup'] = geo_subgroups

    # Aggregate facilities to subgroup level
    subgroup_agg = facility_with_clusters.groupby('geo_subgroup').agg({
        'lat': 'mean',  # Centroid
        'lon': 'mean',  # Centroid
        'total_tonnes': 'sum',
        'cluster': 'first',  # All facilities in subgroup share cluster
        'facility_id': 'count'  # Number of facilities
    }).rename(columns={'facility_id': 'n_facilities'}).reset_index()

    n_clusters = len(np.unique(labels))

    # Create distinct 12-color palette
    distinct_colors = [
        '#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231',
        '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe',
        '#008080', '#e6beff'
    ]
    # Extend if needed
    while len(distinct_colors) < n_clusters:
        distinct_colors.extend(distinct_colors)
    colors = distinct_colors[:n_clusters]

    # Size scaling: map tonnes to marker size (50-400 range)
    min_size, max_size = 50, 400
    tonnes_min = subgroup_agg['total_tonnes'].min()
    tonnes_max = subgroup_agg['total_tonnes'].max()

    def scale_size(tonnes):
        if tonnes_max == tonnes_min:
            return (min_size + max_size) / 2
        # Log scale for better visual distinction
        log_tonnes = np.log10(tonnes + 1)
        log_min = np.log10(tonnes_min + 1)
        log_max = np.log10(tonnes_max + 1)
        normalized = (log_tonnes - log_min) / (log_max - log_min)
        return min_size + normalized * (max_size - min_size)

    subgroup_agg['marker_size'] = subgroup_agg['total_tonnes'].apply(scale_size)

    # Try to use cartopy for proper map projection
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        use_cartopy = True
    except ImportError:
        use_cartopy = False
        print("Cartopy not available, using plain scatter plot fallback")

    # Create figure
    fig = plt.figure(figsize=(14, 10))

    if use_cartopy:
        # EPSG:3035 is ETRS89-extended / LAEA Europe
        proj = ccrs.epsg(3035)
        ax = fig.add_subplot(1, 1, 1, projection=proj)

        # Set extent to cover Europe (in lat/lon, transformed internally)
        ax.set_extent([-12, 35, 34, 72], crs=ccrs.PlateCarree())

        # Add map features
        ax.add_feature(cfeature.LAND, facecolor='#f0f0f0', zorder=0)
        ax.add_feature(cfeature.OCEAN, facecolor='#d0e4f0', zorder=0)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5, edgecolor='gray', zorder=1)
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor='darkgray', zorder=1)

        # Plot each subgroup marker
        for _, row in subgroup_agg.iterrows():
            cluster_id = int(row['cluster'])
            ax.scatter(
                row['lon'], row['lat'],
                c=[colors[cluster_id]],
                s=row['marker_size'],
                alpha=0.7,
                edgecolors='black',
                linewidth=0.5,
                transform=ccrs.PlateCarree(),
                zorder=2
            )
    else:
        # Fallback to plain scatter plot
        ax = fig.add_subplot(1, 1, 1)

        # Plot each subgroup marker
        for _, row in subgroup_agg.iterrows():
            cluster_id = int(row['cluster'])
            ax.scatter(
                row['lon'], row['lat'],
                c=[colors[cluster_id]],
                s=row['marker_size'],
                alpha=0.7,
                edgecolors='black',
                linewidth=0.5,
                zorder=2
            )

        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.grid(True, alpha=0.3)

    # Identify top 10 subgroups by tonnage for highlighting
    top_10 = subgroup_agg.nlargest(10, 'total_tonnes')

    # Draw highlight circles around top 10 subgroups
    for _, row in top_10.iterrows():
        if use_cartopy:
            # Transform coordinates to projection
            x, y = proj.transform_point(row['lon'], row['lat'], ccrs.PlateCarree())
            # Draw circle in projected coordinates (radius ~50km in projection units)
            circle = Circle(
                (x, y), radius=80000,  # ~80km radius in EPSG:3035 units (meters)
                fill=False, edgecolor='red', linewidth=2, linestyle='--',
                zorder=3
            )
            ax.add_patch(circle)
        else:
            # Approximate circle in lat/lon (rough, ~1 degree ≈ 100km at mid-latitudes)
            circle = Circle(
                (row['lon'], row['lat']), radius=0.8,
                fill=False, edgecolor='red', linewidth=2, linestyle='--',
                zorder=3
            )
            ax.add_patch(circle)

    # Add annotations for subgroups above threshold
    large_subgroups = subgroup_agg[subgroup_agg['total_tonnes'] >= min_subgroup_tonnes]

    for _, row in large_subgroups.iterrows():
        tonnes_formatted = f"{row['total_tonnes'] / 1e6:.1f}M" if row['total_tonnes'] >= 1e6 else f"{row['total_tonnes'] / 1e3:.0f}K"
        label = f"{row['geo_subgroup']}: {tonnes_formatted}"

        if use_cartopy:
            ax.annotate(
                label,
                xy=(row['lon'], row['lat']),
                xycoords=ccrs.PlateCarree()._as_mpl_transform(ax),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8,
                fontweight='bold',
                color='black',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8, edgecolor='gray'),
                zorder=5
            )
        else:
            ax.annotate(
                label,
                xy=(row['lon'], row['lat']),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8,
                fontweight='bold',
                color='black',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8, edgecolor='gray'),
                zorder=5
            )

    # Build cluster labels from summary_df
    cluster_labels = {}
    for _, row in summary_df.iterrows():
        cluster_id = int(row['cluster'])
        waste_types = row.get('top_waste_types', '')
        if waste_types:
            # Extract first waste type (before the percentage)
            first_type = waste_types.split(',')[0].split('(')[0].strip()
            cluster_labels[cluster_id] = f"Cluster {cluster_id}: {first_type}"
        else:
            cluster_labels[cluster_id] = f"Cluster {cluster_id}"

    # Create legend for cluster colors
    legend_handles = []
    for cluster_id in sorted(np.unique(labels)):
        label = cluster_labels.get(cluster_id, f"Cluster {cluster_id}")
        handle = mpatches.Patch(color=colors[cluster_id], label=label)
        legend_handles.append(handle)

    # Add size scale reference to legend
    size_refs = [
        (100000, "100K tonnes"),
        (500000, "500K tonnes"),
        (1000000, "1M+ tonnes")
    ]
    for tonnes, label in size_refs:
        size = scale_size(tonnes)
        handle = Line2D(
            [0], [0], marker='o', color='w',
            markerfacecolor='gray', markersize=np.sqrt(size),
            label=label, markeredgecolor='black', markeredgewidth=0.5
        )
        legend_handles.append(handle)

    # Add legend for highlight circles
    highlight_handle = Line2D(
        [0], [0], marker='o', color='w',
        markerfacecolor='none', markersize=12,
        markeredgecolor='red', markeredgewidth=2, linestyle='--',
        label='Top 10 hotspots'
    )
    legend_handles.append(highlight_handle)

    ax.legend(
        handles=legend_handles,
        loc='lower left',
        fontsize=8,
        framealpha=0.9,
        title='Cluster (by waste profile)',
        title_fontsize=9
    )

    # Title
    total_subgroups = len(subgroup_agg)
    total_facilities = facility_with_clusters['facility_id'].nunique() if 'facility_id' in facility_with_clusters.columns else len(facility_with_clusters)
    ax.set_title(
        f'Features-First Clustering: {total_subgroups} Geographic Subgroups from {n_clusters} Clusters\n'
        f'({total_facilities} facilities, labels for subgroups ≥{min_subgroup_tonnes / 1e3:.0f}K tonnes)',
        fontsize=12,
        fontweight='bold'
    )

    plt.tight_layout()

    # Save figure
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved features_first subgroups visualization to: {output_path}")

    return fig


def run_facility_clustering_pipeline(
    data_path: Optional[str] = None,
    min_tonnes: float = 5000,
    max_distance_km: Optional[float] = None,
    geo_mode: str = 'none',
    min_cluster_tonnes: Optional[float] = None,
    method: str = 'ward',
    k_range: range = range(3, 13),
    save_results: bool = True,
    create_visualization: bool = True
) -> Dict:
    """
    Run the complete facility clustering pipeline.

    Parameters
    ----------
    data_path : str, optional
        Path to facility_waste_allocated.csv
    min_tonnes : float
        Minimum tonnes threshold for including individual facilities
    max_distance_km : float, optional
        Maximum distance in km between facilities in the same cluster.
        Required for geo_mode='geo_first' or 'features_first'.
    geo_mode : str
        Geographic clustering mode:
        - 'none': Unconstrained clustering by features only (best silhouette)
        - 'geo_first': Geography → Features (geographically actionable groups)
        - 'features_first': Features → Geographic sub-groups (preserve cluster identity)
    min_cluster_tonnes : float, optional
        Minimum total tonnes for a cluster to be retained. Clusters below this
        threshold are discarded from the final output.
    method : str
        Hierarchical clustering linkage method
    k_range : range
        Range of k values to evaluate
    save_results : bool
        Whether to save results to CSV files
    create_visualization : bool
        Whether to create and save visualization plots

    Returns
    -------
    dict
        Pipeline results containing:
        - filtered_data: Filtered facility data
        - facility_info: Facility metadata
        - feature_matrix: Clustering features
        - coords: Geographic coordinates array
        - labels: Cluster assignments
        - linkage_matrix: Scipy linkage matrix
        - optimal_k: Best cluster count
        - silhouette_score: Clustering quality metric
        - geo_mode: The geographic mode used
        - geo_subgroups: Geographic subgroup labels (for features_first mode)
        - discarded_clusters: List of discarded cluster IDs (if tonnage filter applied)
        - summary: Cluster summary dataframe
        - figure: Matplotlib figure (if create_visualization=True)
    """
    print("=" * 60)
    print("FACILITY HIERARCHICAL CLUSTERING PIPELINE")
    print(f"Geographic mode: {geo_mode}")
    if max_distance_km and geo_mode != 'none':
        print(f"Max distance constraint: {max_distance_km} km")
    if min_cluster_tonnes:
        print(f"Minimum cluster tonnage: {min_cluster_tonnes:,.0f} tonnes")
    print("=" * 60)

    # Step 1: Load and filter
    print("\n1. Loading and filtering facilities...")
    filtered_data = load_and_filter_facilities(data_path, min_tonnes)

    # Step 2: Create features
    print("\n2. Creating feature matrix...")
    facility_info, feature_matrix, coords = create_facility_feature_matrix(filtered_data)

    # Step 3: Cluster
    print("\n3. Applying hierarchical clustering...")
    labels, Z, optimal_k, sil_score, geo_subgroups = apply_hierarchical_clustering(
        feature_matrix,
        coords=coords,
        max_distance_km=max_distance_km,
        geo_mode=geo_mode,
        method=method,
        k_range=k_range
    )

    # Step 3b: Filter clusters by tonnage (optional)
    discarded_clusters = []
    if min_cluster_tonnes is not None:
        print(f"\n3b. Filtering clusters by minimum tonnage ({min_cluster_tonnes:,.0f} tonnes)...")
        labels, facility_info, discarded_clusters, geo_subgroups = filter_clusters_by_tonnage(
            labels, facility_info, min_cluster_tonnes, geo_subgroups
        )
        optimal_k = len(np.unique(labels))

        # Recompute feature_matrix to match filtered facility_info
        feature_matrix = feature_matrix.loc[facility_info['facility_id']]
        coords = facility_info[['lat', 'lon']].values

    # Step 4: Summarize
    print("\n4. Generating cluster summaries...")
    summary = summarize_facility_clusters(facility_info, feature_matrix, labels)

    print("\nCluster Summary:")
    print(summary.to_string(index=False))

    # Step 5: Save (optional)
    if save_results:
        print("\n5. Saving results...")
        save_clustering_results(facility_info, labels, summary, geo_subgroups=geo_subgroups)

    results = {
        'filtered_data': filtered_data,
        'facility_info': facility_info,
        'feature_matrix': feature_matrix,
        'coords': coords,
        'labels': labels,
        'linkage_matrix': Z,
        'optimal_k': optimal_k,
        'silhouette_score': sil_score,
        'max_distance_km': max_distance_km,
        'geo_mode': geo_mode,
        'geo_subgroups': geo_subgroups,
        'discarded_clusters': discarded_clusters,
        'summary': summary,
    }

    # Step 6: Visualize (optional)
    if create_visualization:
        print("\n6. Creating visualization...")
        fig = plot_facility_clusters(facility_info, labels, Z, summary)
        results['figure'] = fig

        # Additional visualization for features_first mode
        if geo_mode == 'features_first' and geo_subgroups is not None:
            print("\n6b. Creating features_first subgroups map...")
            fig_subgroups = plot_features_first_subgroups(
                facility_info, labels, geo_subgroups, summary
            )
            results['figure_subgroups'] = fig_subgroups

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)

    return results
