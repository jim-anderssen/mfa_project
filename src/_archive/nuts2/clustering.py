"""
clustering.py

Functions for clustering NUTS-2 regions by waste profiles
to identify hotspot tiers.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score


def prepare_clustering_features(
    regional_waste: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
    log_transform: bool = True,
) -> Tuple[pd.DataFrame, np.ndarray, StandardScaler]:
    """
    Prepare features for clustering from regional waste data.

    Parameters
    ----------
    regional_waste : pd.DataFrame
        Allocated waste data with economic potential
    feature_cols : list, optional
        Columns to use as features. Defaults to waste/economic/recycling potential.
    log_transform : bool
        Whether to log-transform waste and economic columns

    Returns
    -------
    tuple
        (prepared_df, scaled_features, scaler)
    """
    df = regional_waste.copy()

    # Aggregate to unique Region × NACE × Waste combinations
    df = (
        df.groupby(
            [
                "nuts2_region",
                "nuts2_name",
                "country_code",
                "nace_r2",
                "nace_activity",
                "waste",
                "waste_description",
            ]
        )
        .agg(
            {
                "allocated_waste_tonnes": "sum",
                "economic_potential_eur": "sum",
                "recycling_potential_eur_t": "first",
            }
        )
        .reset_index()
    )

    # Log-transform to handle skewed distributions
    if log_transform:
        df["log_waste"] = np.log10(df["allocated_waste_tonnes"] + 1)
        df["log_econ"] = np.log10(df["economic_potential_eur"] + 1)

    # Default feature columns
    if feature_cols is None:
        if log_transform:
            feature_cols = ["log_waste", "log_econ", "recycling_potential_eur_t"]
        else:
            feature_cols = [
                "allocated_waste_tonnes",
                "economic_potential_eur",
                "recycling_potential_eur_t",
            ]

    X = df[feature_cols].values

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return df, X_scaled, scaler


def find_optimal_clusters(
    X_scaled: np.ndarray,
    k_range: range = range(2, 12),
    sample_size: int = 10000,
    random_state: int = 42,
) -> Tuple[int, List[float], List[float]]:
    """
    Find optimal number of clusters using elbow method and silhouette score.

    Parameters
    ----------
    X_scaled : np.ndarray
        Scaled feature matrix
    k_range : range
        Range of k values to test
    sample_size : int
        Sample size for silhouette calculation (for large datasets)
    random_state : int
        Random seed for reproducibility

    Returns
    -------
    tuple
        (best_k, silhouettes, inertias)
    """
    silhouettes = []
    inertias = []

    # Subsample for faster silhouette calculation
    np.random.seed(random_state)
    n_samples = min(sample_size, len(X_scaled))
    sample_idx = np.random.choice(len(X_scaled), size=n_samples, replace=False)
    X_sample = X_scaled[sample_idx]

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)

        # Calculate silhouette on subsample
        sample_labels = km.predict(X_sample)
        silhouettes.append(silhouette_score(X_sample, sample_labels))

    best_k = list(k_range)[np.argmax(silhouettes)]

    return best_k, silhouettes, inertias


def apply_clustering(
    df: pd.DataFrame,
    X_scaled: np.ndarray,
    n_clusters: int = 5,
    sort_by_value: bool = True,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, KMeans]:
    """
    Apply K-means clustering and optionally sort clusters by economic value.

    Parameters
    ----------
    df : pd.DataFrame
        Data prepared by prepare_clustering_features()
    X_scaled : np.ndarray
        Scaled feature matrix
    n_clusters : int
        Number of clusters
    sort_by_value : bool
        If True, renumber clusters so higher = higher value
    random_state : int
        Random seed

    Returns
    -------
    tuple
        (df_with_clusters, kmeans_model)
    """
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    df = df.copy()
    df["cluster"] = kmeans.fit_predict(X_scaled)

    # Sort clusters by mean economic potential
    if sort_by_value:
        cluster_means = (
            df.groupby("cluster")["economic_potential_eur"].mean().sort_values()
        )
        cluster_rank_map = {old: new for new, old in enumerate(cluster_means.index)}
        df["cluster"] = df["cluster"].map(cluster_rank_map)

    return df, kmeans


def apply_pca(X_scaled: np.ndarray, n_components: int = 2) -> Tuple[np.ndarray, PCA]:
    """
    Apply PCA for visualization.

    Returns
    -------
    tuple
        (transformed_data, pca_model)
    """
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)
    return X_pca, pca


def get_cluster_profiles(
    df: pd.DataFrame, n_clusters: int, top_n: int = 5
) -> Dict[int, Dict]:
    """
    Generate summary profiles for each cluster.

    Parameters
    ----------
    df : pd.DataFrame
        Clustered data
    n_clusters : int
        Number of clusters
    top_n : int
        Number of top items per category

    Returns
    -------
    dict
        Cluster profiles with summary statistics
    """
    profiles = {}

    for c in range(n_clusters):
        subset = df[df["cluster"] == c]

        profiles[c] = {
            "count": len(subset),
            "total_waste_tonnes": subset["allocated_waste_tonnes"].sum(),
            "total_economic_eur": subset["economic_potential_eur"].sum(),
            "avg_waste_tonnes": subset["allocated_waste_tonnes"].mean(),
            "avg_economic_eur": subset["economic_potential_eur"].mean(),
            "top_regions": (
                subset.groupby("nuts2_region")["economic_potential_eur"]
                .sum()
                .nlargest(top_n)
                .to_dict()
            ),
            "top_nace": (
                subset.groupby("nace_r2")["economic_potential_eur"]
                .sum()
                .nlargest(top_n)
                .to_dict()
            ),
            "top_waste": (
                subset.groupby("waste")["economic_potential_eur"]
                .sum()
                .nlargest(top_n)
                .to_dict()
            ),
        }

    return profiles


def get_high_value_regions(
    df: pd.DataFrame, cluster_threshold: int, n_clusters: int
) -> pd.DataFrame:
    """
    Get regions with high-value hotspot combinations.

    Parameters
    ----------
    df : pd.DataFrame
        Clustered data
    cluster_threshold : int
        Minimum cluster number to consider "high value"
    n_clusters : int
        Total number of clusters (for context)

    Returns
    -------
    pd.DataFrame
        Summary by region with hotspot counts
    """
    high_value = df[df["cluster"] >= cluster_threshold]

    return (
        high_value.groupby(["nuts2_region", "nuts2_name", "country_code"])
        .agg(
            {
                "nace_r2": "nunique",
                "waste": "nunique",
                "allocated_waste_tonnes": "sum",
                "economic_potential_eur": "sum",
                "cluster": "count",
            }
        )
        .rename(
            columns={
                "nace_r2": "n_nace_activities",
                "waste": "n_waste_types",
                "cluster": "n_hotspot_combos",
            }
        )
        .reset_index()
        .sort_values("economic_potential_eur", ascending=False)
    )


# =============================================================================
# Waste Composition Profile Clustering (PCA-based alternative approach)
# =============================================================================


def get_redundant_waste_types() -> List[str]:
    """
    Return waste type codes to drop due to hierarchy/redundancy.

    These are identified through correlation analysis - waste types that
    are near-duplicates of others (e.g., parent categories that sum their children).

    Returns
    -------
    list
        Waste type codes to exclude from composition analysis
    """
    return [
        "W09",  # Parent of W091_092 (correlation 0.9994)
    ]


def create_waste_composition_matrix(
    df: pd.DataFrame,
    value_col: str = "allocated_waste_tonnes",
    as_proportions: bool = True,
    include_total: bool = True,
    drop_redundant: bool = True,
) -> pd.DataFrame:
    """
    Pivot data to (nuts2, nace_r2) x waste_types matrix.

    Creates a wide-format matrix where each row is a region-industry combination
    and each column is a waste type. Optionally converts to proportions and
    includes total volume as an additional feature.

    Parameters
    ----------
    df : pd.DataFrame
        Allocated waste data with nuts2_region, nace_r2, waste columns
    value_col : str
        Column to aggregate (e.g., 'allocated_waste_tonnes')
    as_proportions : bool
        If True, convert waste types to row-wise proportions (sum to 1)
    include_total : bool
        If True, add log-transformed total volume as additional feature
    drop_redundant : bool
        If True, drop redundant waste types identified by get_redundant_waste_types()

    Returns
    -------
    pd.DataFrame
        Matrix with (nuts2_region, nace_r2) as index and waste types as columns.
        If include_total=True, includes 'log_total_volume' column.
    """
    # Aggregate by region, nace, and waste type
    agg = (
        df.groupby(["nuts2_region", "nace_r2", "waste_description"])[value_col]
        .sum()
        .reset_index()
    )

    # Drop redundant waste types
    if drop_redundant:
        redundant = get_redundant_waste_types()
        agg = agg[~agg["waste_description"].isin(redundant)]

    # Pivot to wide format
    matrix = agg.pivot_table(
        index=["nuts2_region", "nace_r2"],
        columns="waste_description",
        values=value_col,
        fill_value=0,
    )

    # Calculate total before converting to proportions
    row_totals = matrix.sum(axis=1)

    # Convert to proportions if requested
    if as_proportions:
        # Avoid division by zero
        matrix = matrix.div(row_totals.replace(0, 1), axis=0)

    # Add log-transformed total volume as feature
    if include_total:
        matrix["log_total_volume"] = np.log10(row_totals + 1)

    return matrix


def apply_composition_pca(
    composition_matrix: pd.DataFrame,
    n_components: Optional[int] = None,
    variance_threshold: float = 0.90,
) -> Tuple[np.ndarray, PCA, pd.DataFrame, StandardScaler]:
    """
    Apply PCA to waste composition matrix.

    Standardizes features and applies PCA, either with a fixed number of
    components or automatically selecting enough to explain the variance threshold.

    Parameters
    ----------
    composition_matrix : pd.DataFrame
        Matrix from create_waste_composition_matrix()
    n_components : int, optional
        Fixed number of components. If None, auto-select based on variance_threshold.
    variance_threshold : float
        Cumulative variance to retain (default 90%). Only used if n_components is None.

    Returns
    -------
    tuple
        - X_pca: np.ndarray - Transformed data (n_samples, n_components)
        - pca: PCA - Fitted PCA model
        - loadings_df: pd.DataFrame - Component loadings (waste types x components)
        - scaler: StandardScaler - Fitted scaler for reference
    """
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(composition_matrix.values)

    if n_components is None:
        # First fit full PCA to determine component count
        pca_full = PCA()
        pca_full.fit(X_scaled)

        # Find number of components for variance threshold
        cumvar = np.cumsum(pca_full.explained_variance_ratio_)
        n_components = np.argmax(cumvar >= variance_threshold) + 1
        n_components = max(2, n_components)  # At least 2 for visualization

    # Fit PCA with selected number of components
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(X_scaled)

    # Create loadings dataframe
    loadings_df = pd.DataFrame(
        pca.components_.T,
        index=composition_matrix.columns,
        columns=[f"PC{i + 1}" for i in range(n_components)],
    )

    return X_pca, pca, loadings_df, scaler


def cluster_waste_profiles(
    X_pca: np.ndarray, k_range: range = range(2, 10), random_state: int = 42
) -> Tuple[np.ndarray, int, KMeans, List[float]]:
    """
    Apply K-means clustering to PCA-transformed waste profiles.

    Finds optimal k using silhouette score and returns cluster assignments.

    Parameters
    ----------
    X_pca : np.ndarray
        PCA-transformed data from apply_composition_pca()
    k_range : range
        Range of k values to test
    random_state : int
        Random seed for reproducibility

    Returns
    -------
    tuple
        - labels: np.ndarray - Cluster assignments
        - best_k: int - Optimal number of clusters
        - kmeans: KMeans - Fitted model with best k
        - silhouettes: List[float] - Silhouette scores for each k
    """
    silhouettes = []

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = km.fit_predict(X_pca)
        silhouettes.append(silhouette_score(X_pca, labels))

    # Find best k
    best_k = list(k_range)[np.argmax(silhouettes)]

    # Refit with best k
    kmeans = KMeans(n_clusters=best_k, random_state=random_state, n_init=10)
    labels = kmeans.fit_predict(X_pca)

    return labels, best_k, kmeans, silhouettes


def summarize_cluster_compositions(
    composition_matrix: pd.DataFrame, labels: np.ndarray, top_n: int = 5
) -> pd.DataFrame:
    """
    Summarize mean waste composition for each cluster.

    Parameters
    ----------
    composition_matrix : pd.DataFrame
        Original composition matrix (proportions)
    labels : np.ndarray
        Cluster assignments
    top_n : int
        Number of top waste types to highlight per cluster

    Returns
    -------
    pd.DataFrame
        Mean proportion of each waste type per cluster
    """
    df = composition_matrix.copy()
    df["cluster"] = labels

    # Calculate mean composition per cluster
    cluster_means = df.groupby("cluster").mean()

    return cluster_means


def get_top_waste_types_per_cluster(
    cluster_means: pd.DataFrame, top_n: int = 5
) -> Dict[int, List[Tuple[str, float]]]:
    """
    Get the top waste types that characterize each cluster.

    Parameters
    ----------
    cluster_means : pd.DataFrame
        Output from summarize_cluster_compositions()
    top_n : int
        Number of top waste types per cluster

    Returns
    -------
    dict
        Mapping of cluster -> list of (waste_type, proportion) tuples
    """
    result = {}

    # Exclude log_total_volume if present
    waste_cols = [c for c in cluster_means.columns if c != "log_total_volume"]

    for cluster in cluster_means.index:
        row = cluster_means.loc[cluster, waste_cols]
        top = row.nlargest(top_n)
        result[cluster] = list(zip(top.index, top.values))

    return result
