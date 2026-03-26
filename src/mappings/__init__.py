"""
Classification mappings and taxonomies.

Modules:
- ewc_stat: EWC-Stat waste classification codes
- prodcom_waste: PRODCOM to waste mapping
- ied_nace: IED to NACE to PRODCOM mapping
- eprtr_ied: EPRTR Annex I to IED Annex I mapping
- eprtr_nace: Direct EPRTR Annex I to NACE mapping
- bat_ewc_stat: BAT to EWC-Stat waste mapping
- ied_ewc_stat: Direct IED to EWC-Stat waste mapping
- company_terms: Company terminology mapping
- translations: Multi-language translations
"""

from .ewc_stat import EWC_STAT_CODES, get_ewc_description, NACE_TYPICAL_WASTES
from .prodcom_waste import (
    PRODCOM_TO_EWC,
    NACE_WASTE_GENERATION_FACTORS,
    get_ewc_for_prodcom,
    get_waste_factor_for_nace,
)
from .ied_nace import IED_TO_NACE, get_nace_for_ied
from .eprtr_ied import EPRTR_TO_IED, eprtr_to_ied
from .eprtr_nace import (
    EPRTR_TO_NACE,
    get_nace_for_eprtr,
    get_eprtr_description,
    get_nace_section_for_eprtr,
    get_eprtr_codes_for_nace_section,
)
from .bat_ewc_stat import (
    BAT_TO_EWC_STAT,
    get_primary_waste_for_bat,
    get_excluded_waste_for_bat,
    get_all_probable_waste_for_bat,
    get_bat_for_ewc_stat,
    get_bat_description,
    get_valid_bat_codes,
    is_waste_valid_for_bat,
    get_valid_waste_matrix,
)
from .ied_ewc_stat import (
    IED_TO_EWC_STAT,
    get_waste_for_ied,
    get_primary_waste_for_ied,
    is_waste_valid_for_ied,
    get_ied_waste_matrix,
    get_valid_ied_codes,
    generate_lookup_table_csv,
)

__all__ = [
    'EWC_STAT_CODES',
    'get_ewc_description',
    'NACE_TYPICAL_WASTES',
    'PRODCOM_TO_EWC',
    'NACE_WASTE_GENERATION_FACTORS',
    'get_ewc_for_prodcom',
    'get_waste_factor_for_nace',
    'IED_TO_NACE',
    'get_nace_for_ied',
    'EPRTR_TO_IED',
    'eprtr_to_ied',
    'EPRTR_TO_NACE',
    'get_nace_for_eprtr',
    'get_eprtr_description',
    'get_nace_section_for_eprtr',
    'get_eprtr_codes_for_nace_section',
    'BAT_TO_EWC_STAT',
    'get_primary_waste_for_bat',
    'get_excluded_waste_for_bat',
    'get_all_probable_waste_for_bat',
    'get_bat_for_ewc_stat',
    'get_bat_description',
    'get_valid_bat_codes',
    'is_waste_valid_for_bat',
    'get_valid_waste_matrix',
    # IED to EWC-Stat direct mapping
    'IED_TO_EWC_STAT',
    'get_waste_for_ied',
    'get_primary_waste_for_ied',
    'is_waste_valid_for_ied',
    'get_ied_waste_matrix',
    'get_valid_ied_codes',
    'generate_lookup_table_csv',
]
