"""
External data integration modules.

Modules:
- ied_linker: IED facility to PRODCOM linking
- prodcom_linker: PRODCOM to waste stream linking
"""

from .ied_linker import (
    load_ied_installations,
    allocate_prodcom_to_facilities,
)
from .prodcom_linker import (
    fetch_prodcom_data,
    batch_map_prodcom_to_waste,
    track_material_flows,
)

__all__ = [
    'load_ied_installations',
    'allocate_prodcom_to_facilities',
    'fetch_prodcom_data',
    'batch_map_prodcom_to_waste',
    'track_material_flows',
]
