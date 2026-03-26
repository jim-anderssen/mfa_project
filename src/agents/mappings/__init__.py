"""
Mappings for waste classification codes and translations.

This module re-exports from src.mappings for backwards compatibility.
"""

from src.mappings.ewc_stat import EWC_STAT_CODES, get_ewc_description
from src.mappings.company_terms import COMPANY_TERM_MAPPING, map_company_term
from src.mappings.translations import translate_waste_term, TRANSLATIONS

__all__ = [
    'EWC_STAT_CODES', 'get_ewc_description',
    'COMPANY_TERM_MAPPING', 'map_company_term',
    'translate_waste_term', 'TRANSLATIONS'
]
