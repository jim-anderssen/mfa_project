"""
Allocation module for distributing national waste generation to facilities/companies.

Provides:
- EmissionsAllocator: Facility-level allocation using E-PRTR emissions as proxy
- GVAAllocator: Company-level allocation using turnover as GVA proxy
- Waste generation estimation using BREF factors
"""

from .emissions_based_allocator import EmissionsAllocator
from .gva_based_allocator import (
    GVAAllocator,
    load_gva_allocator,
    run_gva_allocation_pipeline,
)
from .emissions_based_waste_generation import (
    estimate_production_from_co2,
    estimate_waste_generation,
    generate_waste_estimates,
    load_bref_factors,
)

__all__ = [
    "EmissionsAllocator",
    "GVAAllocator",
    "load_gva_allocator",
    "run_gva_allocation_pipeline",
    # Waste generation estimation
    "estimate_production_from_co2",
    "estimate_waste_generation",
    "generate_waste_estimates",
    "load_bref_factors",
]
