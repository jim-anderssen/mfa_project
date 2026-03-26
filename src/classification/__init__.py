"""
Classification module for identifying technology regimes from emissions data.

Provides:
- TensorTechnologyClassifier: Unsupervised CP decomposition of emission tensors
- RulesBasedClassifier: Threshold-based classification using CO/CO2 intensities
- classify_technology: Hybrid classifier (rules primary + tensor fallback)
"""

from .tensor_technology_classifier import (
    identify_technologies,
    assign_technologies,
    decompose_tensor,
    preprocess_tensor,
    save_technology_assignments,
)
from .rules_based_technology_classifier import (
    classify_regime_from_emissions,
    calculate_regime_accuracy,
)
from .emissions_based_technology_classifier import (
    classify_technology,
    TechnologyClassifier,
)

__all__ = [
    # Tensor-based classifier
    "identify_technologies",
    "assign_technologies",
    "decompose_tensor",
    "preprocess_tensor",
    "save_technology_assignments",
    # Rules-based classifier
    "classify_regime_from_emissions",
    "calculate_regime_accuracy",
    # Hybrid classifier
    "classify_technology",
    "TechnologyClassifier",
]
