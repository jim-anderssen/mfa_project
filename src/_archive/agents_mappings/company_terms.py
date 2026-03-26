"""
Mapping from company-reported waste terms to EWC-Stat codes.

Companies often use different terminology in their sustainability reports.
This module provides mappings to standardize these terms.
"""

from typing import Optional, Tuple

# Common company waste terms to EWC-Stat mapping
COMPANY_TERM_MAPPING = {
    # Metal wastes
    'scrap metal': 'W061',
    'metal scrap': 'W061',
    'steel scrap': 'W061',
    'iron scrap': 'W061',
    'ferrous scrap': 'W061',
    'ferrous metal': 'W061',
    'ferrous waste': 'W061',
    'cast iron scrap': 'W061',
    'mill scale': 'W061',
    'grinding dust': 'W061',
    'metal shavings': 'W061',
    'turnings': 'W061',

    'aluminum scrap': 'W062',
    'aluminium scrap': 'W062',
    'copper scrap': 'W062',
    'copper waste': 'W062',
    'brass scrap': 'W062',
    'zinc waste': 'W062',
    'non-ferrous': 'W062',
    'non ferrous': 'W062',
    'nonferrous': 'W062',

    'mixed metal': 'W063',
    'mixed metals': 'W063',

    # Industrial residues
    'slag': 'W12A',
    'blast furnace slag': 'W12A',
    'steel slag': 'W12A',
    'foundry slag': 'W12A',
    'fly ash': 'W124',
    'bottom ash': 'W124',
    'boiler ash': 'W124',
    'incinerator ash': 'W124',
    'foundry sand': 'W12B',
    'spent foundry sand': 'W12B',
    'refractory waste': 'W12B',

    # Paper/cardboard
    'paper waste': 'W072',
    'waste paper': 'W072',
    'cardboard': 'W072',
    'cardboard waste': 'W072',
    'packaging paper': 'W072',
    'paper packaging': 'W072',

    # Plastics
    'plastic waste': 'W074',
    'plastics waste': 'W074',
    'packaging plastic': 'W074',
    'plastic packaging': 'W074',
    'polymer waste': 'W074',
    'plastic film': 'W074',

    # Wood
    'wood waste': 'W075',
    'timber waste': 'W075',
    'wood pallets': 'W075',
    'sawdust': 'W075',
    'wood chips': 'W075',

    # Glass
    'glass waste': 'W071',
    'cullet': 'W071',
    'broken glass': 'W071',

    # Textiles
    'textile waste': 'W076',
    'fabric waste': 'W076',
    'cloth waste': 'W076',

    # Rubber
    'rubber waste': 'W073',
    'tire waste': 'W073',
    'tyre waste': 'W073',

    # Electronics
    'electronic waste': 'W08A',
    'e-waste': 'W08A',
    'weee': 'W08A',
    'electrical waste': 'W08A',
    'electronic equipment': 'W08A',

    # Vehicles
    'end-of-life vehicles': 'W081',
    'elv': 'W081',
    'vehicle waste': 'W081',
    'automotive waste': 'W081',

    # Organic/food
    'food waste': 'W091',
    'organic waste': 'W091',
    'kitchen waste': 'W091',
    'catering waste': 'W091',
    'green waste': 'W092',
    'garden waste': 'W092',
    'vegetal waste': 'W092',
    'plant waste': 'W092',

    # Sludges
    'sludge': 'W11',
    'sewage sludge': 'W11',
    'wastewater sludge': 'W11',
    'treatment sludge': 'W11',

    # Construction
    'construction waste': 'W121',
    'demolition waste': 'W121',
    'c&d waste': 'W121',
    'concrete waste': 'W121',
    'brick waste': 'W121',

    # Hazardous
    'hazardous waste': 'W01-05',
    'dangerous waste': 'W01-05',
    'special waste': 'W01-05',
    'chemical waste': 'W02A',
    'used oil': 'W013',
    'waste oil': 'W013',
    'spent oil': 'W013',
    'lubricant waste': 'W013',
    'spent solvent': 'W011',
    'solvent waste': 'W011',

    # Mixed/general
    'mixed waste': 'W102',
    'general waste': 'W102',
    'residual waste': 'W102',
    'non-recyclable': 'W102',
    'sorting residue': 'W103',
    'reject': 'W103',
    'rejects': 'W103',
}


def map_company_term(term: str, context: str = '') -> Tuple[Optional[str], float]:
    """
    Map a company waste term to EWC-Stat code.

    Parameters
    ----------
    term : str
        Waste term from company report
    context : str
        Additional context (e.g., NACE sector)

    Returns
    -------
    tuple
        (ewc_code or None, confidence score 0-1)
    """
    term_lower = term.lower().strip()

    # Direct match
    if term_lower in COMPANY_TERM_MAPPING:
        return COMPANY_TERM_MAPPING[term_lower], 0.95

    # Partial match
    for key, code in COMPANY_TERM_MAPPING.items():
        if key in term_lower:
            return code, 0.8
        if term_lower in key:
            return code, 0.7

    # No match found
    return None, 0.0
