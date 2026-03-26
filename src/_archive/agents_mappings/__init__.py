"""
Mappings for waste classification codes and translations.
"""

from src.agents.mappings.ewc_stat_codes import EWC_STAT_CODES, get_ewc_description
from src.agents.mappings.company_terms import COMPANY_TERM_MAPPING, map_company_term
from src.agents.mappings.translations import translate_waste_term, TRANSLATIONS

__all__ = [
    'EWC_STAT_CODES', 'get_ewc_description',
    'COMPANY_TERM_MAPPING', 'map_company_term',
    'translate_waste_term', 'TRANSLATIONS'
]
