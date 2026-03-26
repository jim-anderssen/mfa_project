"""
Tensor-based Technology Classifier using CP Decomposition.

Identifies distinct technology regimes within IED activity categories
by decomposing facility × pollutant × medium emission tensors.

Uses CP (CANDECOMP/PARAFAC) decomposition to find latent factors that
represent different technologies (e.g., BF/BOF vs EAF in steel).
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, List, Dict, Optional
import tensorly as tl
from tensorly.decomposition import parafac, non_negative_parafac


def preprocess_tensor(
    tensor: np.ndarray,
    log_transform: bool = True,
    normalize: bool = True
) -> np.ndarray:
    """
    Preprocess tensor for decomposition.

    Parameters
    ----------
    tensor : np.ndarray
        Raw emission tensor (facilities × pollutants × media)
    log_transform : bool
        Apply log(1 + x) transform to handle scale differences
    normalize : bool
        Normalize each pollutant to [0, 1] range

    Returns
    -------
    np.ndarray
        Preprocessed tensor
    """
    X = tensor.copy().astype(np.float64)

    if log_transform:
        X = np.log1p(X)

    if normalize:
        pollutant_max = X.max(axis=(0, 2), keepdims=True)
        pollutant_max[pollutant_max == 0] = 1
        X = X / pollutant_max

    return X


def decompose_tensor(
    tensor: np.ndarray,
    rank: int = 3,
    n_iter_max: int = 100,
    non_negative: bool = True,
    random_state: int = 42
) -> Tuple[np.ndarray, List[np.ndarray]]:
    """
    Perform CP decomposition on emission tensor.

    Parameters
    ----------
    tensor : np.ndarray
        Preprocessed tensor (facilities × pollutants × media)
    rank : int
        Number of components (technology regimes to find)
    n_iter_max : int
        Maximum iterations for ALS algorithm
    non_negative : bool
        Use non-negative CP (more interpretable for emissions)
    random_state : int
        Random seed for reproducibility

    Returns
    -------
    weights : np.ndarray
        Component weights (length = rank)
    factors : list of np.ndarray
        Factor matrices:
        - factors[0]: facility loadings (n_facilities × rank)
        - factors[1]: pollutant loadings (n_pollutants × rank)
        - factors[2]: medium loadings (n_media × rank)
    """
    tl.set_backend('numpy')

    if non_negative:
        weights, factors = non_negative_parafac(
            tensor,
            rank=rank,
            n_iter_max=n_iter_max,
            init='random',
            random_state=random_state
        )
    else:
        weights, factors = parafac(
            tensor,
            rank=rank,
            n_iter_max=n_iter_max,
            init='random',
            random_state=random_state
        )

    return weights, factors


def interpret_factors(
    factors: List[np.ndarray],
    pollutant_names: List[str],
    media_names: List[str],
    top_n: int = 10
) -> List[Dict]:
    """
    Interpret factor loadings to identify technology signatures.

    Parameters
    ----------
    factors : list of np.ndarray
        Factor matrices from decomposition
    pollutant_names : list
        Names of pollutants (axis 1)
    media_names : list
        Names of media (axis 2)
    top_n : int
        Number of top pollutants to show per factor

    Returns
    -------
    list of dict
        Interpretation for each factor with top pollutants and media profile
    """
    facility_factors, pollutant_factors, media_factors = factors

    interpretations = []

    for r in range(pollutant_factors.shape[1]):
        pol_loadings = pollutant_factors[:, r]
        sorted_idx = np.argsort(pol_loadings)[::-1]

        top_pollutants = [
            (pollutant_names[i], pol_loadings[i])
            for i in sorted_idx[:top_n]
            if pol_loadings[i] > 0.01
        ]

        med_loadings = media_factors[:, r]
        media_profile = {
            media_names[i]: med_loadings[i]
            for i in range(len(media_names))
        }

        fac_loadings = facility_factors[:, r]
        n_significant = np.sum(fac_loadings > 0.5)

        interpretations.append({
            'factor_id': r,
            'top_pollutants': top_pollutants,
            'media_profile': media_profile,
            'n_significant_facilities': n_significant,
            'facility_loading_stats': {
                'mean': float(fac_loadings.mean()),
                'max': float(fac_loadings.max()),
                'std': float(fac_loadings.std())
            }
        })

    return interpretations


def assign_technologies(
    facility_factors: np.ndarray,
    facility_ids: List[str],
    method: str = 'dominant'
) -> pd.DataFrame:
    """
    Assign technology regime to each facility based on factor loadings.

    Parameters
    ----------
    facility_factors : np.ndarray
        Facility loadings matrix (n_facilities × rank)
    facility_ids : list
        Facility IDs corresponding to rows
    method : str
        Assignment method:
        - 'dominant': Assign to factor with highest loading
        - 'threshold': Assign to all factors above threshold
        - 'proportional': Return proportion of each factor

    Returns
    -------
    pd.DataFrame
        Facility assignments with columns:
        - facility_id
        - technology_regime (if dominant)
        - factor_0, factor_1, ... (loadings for each factor)
    """
    n_facilities, rank = facility_factors.shape

    df = pd.DataFrame({
        'facility_id': facility_ids
    })

    for r in range(rank):
        df[f'factor_{r}'] = facility_factors[:, r]

    if method == 'dominant':
        df['technology_regime'] = facility_factors.argmax(axis=1)
        max_loadings = facility_factors.max(axis=1)
        sum_loadings = facility_factors.sum(axis=1)
        sum_loadings[sum_loadings == 0] = 1
        df['assignment_confidence'] = max_loadings / sum_loadings

    return df


def map_factors_to_regimes(
    interpretations: List[Dict],
    regime_signatures: Optional[Dict[str, List[str]]] = None
) -> Dict[int, str]:
    """
    Map tensor factors to named technology regimes based on pollutant signatures.

    For steel (IED 2.x), typical signatures:
    - BF_BOF: High CO2, CO, SOX, PM10, NOX (combustion-intensive)
    - EAF: High dust, Zn, Pb, Cr, Ni (metal-rich dust from scrap)

    Parameters
    ----------
    interpretations : list of dict
        Factor interpretations from interpret_factors()
    regime_signatures : dict, optional
        Mapping of regime names to characteristic pollutants.
        Default uses steel signatures.

    Returns
    -------
    dict
        Mapping of factor_id to regime name
    """
    if regime_signatures is None:
        # Default: steel signatures
        regime_signatures = {
            'BF_BOF': ['Carbon dioxide', 'CO2', 'Carbon monoxide', 'CO', 'SOX', 'SO2', 'NOX'],
            'EAF': ['Zinc', 'Zn', 'Lead', 'Pb', 'Chromium', 'Cr', 'Nickel', 'Ni', 'Dust']
        }

    factor_to_regime = {}

    for interp in interpretations:
        fid = interp['factor_id']
        top_pols = [p.lower() for p, _ in interp['top_pollutants'][:5]]

        # Score each regime
        scores = {}
        for regime, sig_pols in regime_signatures.items():
            score = sum(1 for sp in sig_pols if any(sp.lower() in tp for tp in top_pols))
            scores[regime] = score

        # Assign to highest scoring regime
        best_regime = max(scores, key=scores.get) if max(scores.values()) > 0 else 'UNKNOWN'
        factor_to_regime[fid] = best_regime

    return factor_to_regime


def identify_technologies(
    emissions_df: pd.DataFrame,
    ied_filter: str,
    rank: int = 3,
    verbose: bool = True
) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Main function: Identify technology regimes for facilities in an IED category.

    Parameters
    ----------
    emissions_df : pd.DataFrame
        Combined emissions from load_all_emissions()
    ied_filter : str
        IED activity prefix to analyze (e.g., '2.b' for iron/steel)
    rank : int
        Number of technology regimes to identify
    verbose : bool
        Print interpretation details

    Returns
    -------
    assignments : pd.DataFrame
        Facility technology assignments
    interpretations : list
        Factor interpretations (pollutant signatures)
    """
    from src.loaders.eprtr_emissions import (
        build_emission_tensor,
        get_facility_metadata
    )

    tensor, facility_ids, pollutants, media = build_emission_tensor(
        emissions_df, ied_filter=ied_filter
    )

    if verbose:
        print(f"\nAnalyzing IED {ied_filter}")
        print(f"  Facilities: {len(facility_ids)}")
        print(f"  Pollutants: {len(pollutants)}")
        print(f"  Media: {media}")

    tensor_prep = preprocess_tensor(tensor, log_transform=True, normalize=True)

    if verbose:
        print(f"\nRunning CP decomposition with rank={rank}...")

    weights, factors = decompose_tensor(
        tensor_prep,
        rank=rank,
        non_negative=True
    )

    interpretations = interpret_factors(
        factors, pollutants, media, top_n=10
    )

    if verbose:
        print("\n" + "="*60)
        print("FACTOR INTERPRETATIONS (Technology Signatures)")
        print("="*60)

        for interp in interpretations:
            print(f"\n--- Factor {interp['factor_id']} ---")
            print(f"Facilities with significant loading: {interp['n_significant_facilities']}")

            print("\nTop pollutants:")
            for pol, loading in interp['top_pollutants'][:7]:
                print(f"  {loading:.3f}  {pol}")

            print("\nMedia profile:")
            for med, loading in interp['media_profile'].items():
                print(f"  {loading:.3f}  {med}")

    facility_factors = factors[0]
    assignments = assign_technologies(facility_factors, facility_ids)

    metadata = get_facility_metadata(emissions_df, ied_filter=ied_filter)
    assignments = assignments.merge(
        metadata[['facility_id', 'facility_name', 'country', 'ied_code']],
        on='facility_id',
        how='left'
    )

    if verbose:
        print("\n" + "="*60)
        print("TECHNOLOGY REGIME DISTRIBUTION")
        print("="*60)
        print(assignments['technology_regime'].value_counts())

    return assignments, interpretations


def save_technology_assignments(
    assignments: pd.DataFrame,
    interpretations: List[Dict],
    output_dir: Path,
    ied_code: str
):
    """Save technology assignments and interpretations to files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    assignments_path = output_dir / f'technology_assignments_{ied_code.replace(".", "_")}.csv'
    assignments.to_csv(assignments_path, index=False)
    print(f"Saved assignments to: {assignments_path}")

    interp_rows = []
    for interp in interpretations:
        row = {
            'factor_id': interp['factor_id'],
            'n_significant_facilities': interp['n_significant_facilities'],
            'top_pollutants': '; '.join([
                f"{pol}:{loading:.3f}" for pol, loading in interp['top_pollutants']
            ]),
            **{f'media_{k}': v for k, v in interp['media_profile'].items()}
        }
        interp_rows.append(row)

    interp_df = pd.DataFrame(interp_rows)
    interp_path = output_dir / f'technology_factors_{ied_code.replace(".", "_")}.csv'
    interp_df.to_csv(interp_path, index=False)
    print(f"Saved interpretations to: {interp_path}")


if __name__ == '__main__':
    from src.loaders.eprtr_emissions import load_all_emissions
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent
    raw_dir = project_root / 'data' / 'raw'
    output_dir = project_root / 'data' / 'processed'

    print("Loading emissions data...")
    emissions = load_all_emissions(raw_dir)

    assignments, interpretations = identify_technologies(
        emissions,
        ied_filter='2.b',
        rank=3,
        verbose=True
    )

    save_technology_assignments(assignments, interpretations, output_dir, '2.b')
