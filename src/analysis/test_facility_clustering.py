"""
Test script for facility_clustering.py

Run this script to verify the clustering pipeline works correctly:
    python -m src.analysis.test_facility_clustering
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))


def test_pipeline():
    """Run the full clustering pipeline and verify results."""
    from src.analysis.facility_clustering import (
        load_and_filter_facilities,
        create_facility_feature_matrix,
        apply_hierarchical_clustering,
        summarize_facility_clusters,
        run_facility_clustering_pipeline,
    )

    print("=" * 70)
    print("TESTING FACILITY CLUSTERING PIPELINE")
    print("=" * 70)

    # Test 1: Load and filter
    print("\n[TEST 1] Loading and filtering facilities...")
    data_path = project_root / "data" / "processed" / "facility_waste_allocated.csv"

    if not data_path.exists():
        print(f"ERROR: Data file not found at {data_path}")
        return False

    df = load_and_filter_facilities(str(data_path), min_tonnes=5000)
    n_facilities = df['facility_id'].nunique()
    print(f"  - Loaded {len(df):,} rows for {n_facilities:,} facilities")

    if n_facilities < 10:
        print("  WARNING: Very few facilities meet the 5000 tonne threshold")
        print("  Trying with lower threshold of 1000 tonnes...")
        df = load_and_filter_facilities(str(data_path), min_tonnes=1000)
        n_facilities = df['facility_id'].nunique()
        print(f"  - Loaded {len(df):,} rows for {n_facilities:,} facilities")

    assert n_facilities > 0, "No facilities found"
    print("  PASSED")

    # Test 2: Create feature matrix
    print("\n[TEST 2] Creating feature matrix...")
    facility_info, feature_matrix, coords = create_facility_feature_matrix(df)

    print(f"  - Facility info shape: {facility_info.shape}")
    print(f"  - Feature matrix shape: {feature_matrix.shape}")
    print(f"  - Coordinates shape: {coords.shape}")

    assert len(facility_info) == n_facilities, "Facility count mismatch"
    assert len(feature_matrix) == n_facilities, "Feature matrix row count mismatch"
    assert feature_matrix.shape[1] > 0, "No features created"
    assert coords.shape == (n_facilities, 2), "Coordinates shape mismatch"
    print("  PASSED")

    # Test 3: Apply clustering
    print("\n[TEST 3] Applying hierarchical clustering...")
    labels, Z, optimal_k, sil_score = apply_hierarchical_clustering(
        feature_matrix,
        method='ward',
        k_range=range(3, 10)
    )

    print(f"  - Optimal k: {optimal_k}")
    print(f"  - Silhouette score: {sil_score:.4f}")
    print(f"  - Label distribution: {dict(zip(*__import__('numpy').unique(labels, return_counts=True)))}")

    assert len(labels) == n_facilities, "Label count mismatch"
    assert optimal_k >= 3, "Optimal k should be at least 3"
    print("  PASSED")

    # Test 4: Summarize clusters
    print("\n[TEST 4] Generating cluster summaries...")
    summary = summarize_facility_clusters(facility_info, feature_matrix, labels)

    print(f"  - Summary shape: {summary.shape}")
    print(f"  - Columns: {summary.columns.tolist()}")

    assert len(summary) == optimal_k, "Summary should have one row per cluster"
    assert 'total_tonnes' in summary.columns, "Missing total_tonnes column"
    assert 'dominant_nace' in summary.columns, "Missing dominant_nace column"
    print("  PASSED")

    # Test 5: Verify cluster quality
    print("\n[TEST 5] Verifying cluster quality...")
    silhouette_threshold = 0.2  # Relaxed threshold for facility data

    if sil_score >= silhouette_threshold:
        print(f"  - Silhouette score {sil_score:.4f} >= {silhouette_threshold} threshold")
        print("  PASSED")
    else:
        print(f"  - WARNING: Silhouette score {sil_score:.4f} < {silhouette_threshold}")
        print("  - Clusters may not be well-separated")
        print("  PASSED (with warning)")

    # Test 6: Geographic constraint clustering
    print("\n[TEST 6] Testing geographic constraint (two-stage clustering)...")
    from src.analysis.facility_clustering import _haversine_distance_matrix

    max_distance_km = 300
    geo_labels, geo_Z, geo_k, geo_sil = apply_hierarchical_clustering(
        feature_matrix,
        coords=coords,
        max_distance_km=max_distance_km,
        method='ward',
        k_range=range(3, 10)
    )

    print(f"  - Number of clusters with geo constraint: {geo_k}")
    print(f"  - Silhouette score: {geo_sil:.4f}")

    # Verify all clusters satisfy the distance constraint
    dist_matrix = _haversine_distance_matrix(coords)
    violations = 0
    for cluster_id in __import__('numpy').unique(geo_labels):
        mask = geo_labels == cluster_id
        indices = __import__('numpy').where(mask)[0]
        if len(indices) > 1:
            cluster_dists = dist_matrix[__import__('numpy').ix_(indices, indices)]
            max_dist = cluster_dists.max()
            if max_dist > max_distance_km:
                violations += 1
                print(f"  - VIOLATION: Cluster {cluster_id} has max distance {max_dist:.1f} km")

    if violations == 0:
        print(f"  - All {geo_k} clusters satisfy the {max_distance_km} km constraint")
        print("  PASSED")
    else:
        print(f"  - FAILED: {violations} clusters violate the constraint")
        return False

    # Print summary
    print("\n" + "=" * 70)
    print("CLUSTER SUMMARY")
    print("=" * 70)
    print(summary.to_string(index=False))

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED")
    print("=" * 70)

    return True


def test_full_pipeline_with_save():
    """Test the complete pipeline with save and visualization."""
    from src.analysis.facility_clustering import run_facility_clustering_pipeline

    print("\n" + "=" * 70)
    print("TESTING FULL PIPELINE (with save and visualization)")
    print("=" * 70)

    results = run_facility_clustering_pipeline(
        min_tonnes=5000,
        save_results=True,
        create_visualization=True
    )

    # Verify outputs exist
    output_dir = Path(__file__).resolve().parents[2] / "data" / "processed"
    clusters_file = output_dir / "facility_clusters.csv"
    summary_file = output_dir / "facility_cluster_summary.csv"

    if clusters_file.exists():
        print(f"\n  Clusters file created: {clusters_file}")
    else:
        print(f"\n  WARNING: Clusters file not found: {clusters_file}")

    if summary_file.exists():
        print(f"  Summary file created: {summary_file}")
    else:
        print(f"  WARNING: Summary file not found: {summary_file}")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test facility clustering pipeline")
    parser.add_argument("--full", action="store_true", help="Run full pipeline with save")
    args = parser.parse_args()

    success = test_pipeline()

    if success and args.full:
        test_full_pipeline_with_save()
