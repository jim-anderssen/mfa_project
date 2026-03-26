"""
Run the facility hierarchical clustering pipeline.

Usage:
    python run_facility_clustering.py [options]

Options:
    --geo-mode MODE         Clustering mode: 'none', 'geo_first', 'features_first' (default: none)
    --max-distance KM       Maximum distance in km for geographic constraints
    --min-tonnes TONNES     Minimum tonnes threshold for individual facilities (default: 5000)
    --min-cluster-tonnes T  Minimum total tonnes for a cluster to be retained
    --no-visualization      Skip creating visualization plots
    --no-save               Skip saving results to CSV

Examples:
    # Unconstrained clustering (best silhouette)
    python run_facility_clustering.py --geo-mode none

    # Geographic-first clustering (geographically actionable groups)
    python run_facility_clustering.py --geo-mode geo_first --max-distance 300

    # Features-first with geographic subgroups
    python run_facility_clustering.py --geo-mode features_first --max-distance 300

    # Filter out small clusters
    python run_facility_clustering.py --min-cluster-tonnes 100000
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.analysis.facility_clustering import run_facility_clustering_pipeline


def main():
    parser = argparse.ArgumentParser(
        description='Run facility hierarchical clustering pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Geographic Modes:
  none           Unconstrained clustering by features only (best silhouette)
  geo_first      Geography first, then features (geographically actionable groups)
  features_first Features first, then geographic sub-groups (preserve cluster identity)
        """
    )

    parser.add_argument(
        '--geo-mode',
        type=str,
        choices=['none', 'geo_first', 'features_first'],
        default='none',
        help="Geographic clustering mode (default: none)"
    )
    parser.add_argument(
        '--max-distance',
        type=float,
        default=None,
        help="Maximum distance in km for geographic constraints (required for geo_first/features_first)"
    )
    parser.add_argument(
        '--min-tonnes',
        type=float,
        default=5000,
        help="Minimum tonnes threshold for including individual facilities (default: 5000)"
    )
    parser.add_argument(
        '--min-cluster-tonnes',
        type=float,
        default=None,
        help="Minimum total tonnes for a cluster to be retained"
    )
    parser.add_argument(
        '--method',
        type=str,
        default='ward',
        choices=['ward', 'complete', 'average'],
        help="Linkage method for hierarchical clustering (default: ward)"
    )
    parser.add_argument(
        '--no-visualization',
        action='store_true',
        help="Skip creating visualization plots"
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help="Skip saving results to CSV files"
    )
    parser.add_argument(
        '--data-path',
        type=str,
        default=None,
        help="Path to facility waste data (auto-detects wide/long format)"
    )

    args = parser.parse_args()

    # Validate that max_distance is provided for geographic modes
    if args.geo_mode in ('geo_first', 'features_first') and args.max_distance is None:
        parser.error(f"--max-distance is required when --geo-mode is '{args.geo_mode}'")

    print("Running facility clustering pipeline...\n")

    results = run_facility_clustering_pipeline(
        data_path=args.data_path,
        min_tonnes=args.min_tonnes,
        max_distance_km=args.max_distance,
        geo_mode=args.geo_mode,
        min_cluster_tonnes=args.min_cluster_tonnes,
        method=args.method,
        k_range=range(3, 13),
        save_results=not args.no_save,
        create_visualization=not args.no_visualization
    )

    print(f"\nResults summary:")
    print(f"  - Geographic mode: {results['geo_mode']}")
    print(f"  - Optimal k: {results['optimal_k']}")
    print(f"  - Silhouette score: {results['silhouette_score']:.4f}")
    print(f"  - Facilities clustered: {len(results['facility_info'])}")

    if results['discarded_clusters']:
        print(f"  - Discarded clusters: {len(results['discarded_clusters'])}")

    if results['geo_subgroups'] is not None:
        n_subgroups = len(set(results['geo_subgroups']))
        print(f"  - Geographic subgroups: {n_subgroups}")


if __name__ == "__main__":
    main()
