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

from ..loaders.io import PROCESSED_DIR


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

    # Calculate total allocated tonnes per facility
    facility_totals = df.groupby('facility_id')['allocated_tonnes'].sum()
    qualifying_facilities = facility_totals[facility_totals >= min_tonnes].index

    # Filter to qualifying facilities
    filtered = df[df['facility_id'].isin(qualifying_facilities)].copy()

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
) -> Tuple[pd.DataFrame, pd.DataFrame]:
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
        (facility_info_df, feature_matrix_df)
        - facility_info_df: Facility metadata (id, name, country, lat, lon, total_tonnes)
        - feature_matrix_df: Feature matrix indexed by facility_id
    """
    # Aggregate total tonnes per facility
    facility_totals = df.groupby('facility_id')['allocated_tonnes'].sum().rename('total_tonnes')

    # Get facility info (first row per facility for metadata)
    facility_info = df.groupby('facility_id').agg({
        'facility_name': 'first',
        'country': 'first',
        'lat': 'first',
        'lon': 'first',
        'nace': 'first',  # Primary NACE
        'ied_activity': 'first',  # Primary IED
    }).reset_index()

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

    return facility_info, feature_matrix


def apply_hierarchical_clustering(
    features: pd.DataFrame,
    method: str = 'ward',
    k_range: range = range(3, 13),
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, int, float]:
    """
    Apply agglomerative hierarchical clustering with automatic k selection.

    Parameters
    ----------
    features : pd.DataFrame
        Feature matrix from create_facility_feature_matrix()
    method : str
        Linkage method for hierarchical clustering ('ward', 'complete', 'average')
    k_range : range
        Range of cluster counts to evaluate
    random_state : int
        Random seed for reproducibility

    Returns
    -------
    tuple
        (labels, linkage_matrix, optimal_k, silhouette_score)
        - labels: Cluster assignments (0-indexed)
        - linkage_matrix: Scipy linkage matrix for dendrogram
        - optimal_k: Best number of clusters found
        - silhouette_score: Silhouette score for optimal clustering
    """
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features.values)

    # Compute linkage matrix for dendrogram
    Z = linkage(X_scaled, method=method)

    # Evaluate different k values
    silhouettes = []

    for k in k_range:
        # Use scipy fcluster for hierarchical cut
        temp_labels = fcluster(Z, t=k, criterion='maxclust') - 1  # 0-indexed

        if len(np.unique(temp_labels)) > 1:
            score = silhouette_score(X_scaled, temp_labels)
        else:
            score = -1  # Invalid if only one cluster

        silhouettes.append(score)

    # Find optimal k
    best_idx = np.argmax(silhouettes)
    optimal_k = list(k_range)[best_idx]
    best_silhouette = silhouettes[best_idx]

    # Get final labels with optimal k
    labels = fcluster(Z, t=optimal_k, criterion='maxclust') - 1  # 0-indexed

    print(f"Optimal k={optimal_k} with silhouette score={best_silhouette:.3f}")
    print(f"Silhouette scores by k: {dict(zip(k_range, [f'{s:.3f}' for s in silhouettes]))}")

    return labels, Z, optimal_k, best_silhouette


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
        - dominant_ied: Most common IED category
        - top_waste_types: Top waste types by proportion
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
        dominant_nace = ', '.join(nace_counts.head(top_n).index.tolist())

        # Dominant IED
        ied_categories = cluster_facilities['ied_activity'].apply(_extract_ied_major_category)
        ied_counts = ied_categories.value_counts()
        dominant_ied = ', '.join(ied_counts.head(top_n).index.tolist())

        # Top waste types (by mean proportion in cluster)
        waste_cols = [c for c in cluster_features.columns if c.startswith('waste_')]
        if waste_cols:
            mean_waste = cluster_features[waste_cols].mean()
            top_waste = mean_waste.nlargest(top_n)
            top_waste_types = ', '.join([
                f"{col.replace('waste_', '')}({val:.1%})"
                for col, val in top_waste.items()
            ])
        else:
            top_waste_types = ''

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
            'dominant_ied': dominant_ied,
            'top_waste_types': top_waste_types,
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
    output_dir: Optional[str] = None
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
    linkage_matrix: np.ndarray,
    summary_df: pd.DataFrame,
    output_path: Optional[str] = None
):
    """
    Create visualization of facility clustering results.

    Produces a figure with three subplots:
    1. Dendrogram showing hierarchical structure
    2. Geographic scatter plot of facilities colored by cluster
    3. Cluster composition bar chart

    Parameters
    ----------
    facility_df : pd.DataFrame
        Facility info dataframe
    labels : np.ndarray
        Cluster assignments
    linkage_matrix : np.ndarray
        Scipy linkage matrix from apply_hierarchical_clustering()
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


def run_facility_clustering_pipeline(
    data_path: Optional[str] = None,
    min_tonnes: float = 5000,
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
        Minimum tonnes threshold for including facilities
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
        - labels: Cluster assignments
        - linkage_matrix: Scipy linkage matrix
        - optimal_k: Best cluster count
        - silhouette_score: Clustering quality metric
        - summary: Cluster summary dataframe
        - figure: Matplotlib figure (if create_visualization=True)
    """
    print("=" * 60)
    print("FACILITY HIERARCHICAL CLUSTERING PIPELINE")
    print("=" * 60)

    # Step 1: Load and filter
    print("\n1. Loading and filtering facilities...")
    filtered_data = load_and_filter_facilities(data_path, min_tonnes)

    # Step 2: Create features
    print("\n2. Creating feature matrix...")
    facility_info, feature_matrix = create_facility_feature_matrix(filtered_data)

    # Step 3: Cluster
    print("\n3. Applying hierarchical clustering...")
    labels, Z, optimal_k, sil_score = apply_hierarchical_clustering(
        feature_matrix, method=method, k_range=k_range
    )

    # Step 4: Summarize
    print("\n4. Generating cluster summaries...")
    summary = summarize_facility_clusters(facility_info, feature_matrix, labels)

    print("\nCluster Summary:")
    print(summary.to_string(index=False))

    # Step 5: Save (optional)
    if save_results:
        print("\n5. Saving results...")
        save_clustering_results(facility_info, labels, summary)

    results = {
        'filtered_data': filtered_data,
        'facility_info': facility_info,
        'feature_matrix': feature_matrix,
        'labels': labels,
        'linkage_matrix': Z,
        'optimal_k': optimal_k,
        'silhouette_score': sil_score,
        'summary': summary,
    }

    # Step 6: Visualize (optional)
    if create_visualization:
        print("\n6. Creating visualization...")
        fig = plot_facility_clusters(facility_info, labels, Z, summary)
        results['figure'] = fig

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)

    return results
