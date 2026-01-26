"""
Allocation module for distributing national waste generation to facilities.

Provides emissions-based allocation using E-PRTR pollutant data as proxy.
"""

from .emissions_based_allocator import EmissionsAllocator

__all__ = ['EmissionsAllocator']
