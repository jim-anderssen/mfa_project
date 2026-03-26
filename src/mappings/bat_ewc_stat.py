"""
BAT (Best Available Techniques) to EWC-Stat waste classification mapping.

Maps BAT conclusion codes to probable waste types (EWC-Stat codes) to enable
sector-specific waste allocation to industrial installations. An IS (Iron & Steel)
installation won't produce non-ferrous waste but will produce ferrous waste.

References:
- BAT Reference Documents (BREFs): https://eippcb.jrc.ec.europa.eu/reference
- EWC-Stat waste classification: Eurostat waste statistics regulation
"""

from typing import TypedDict

from .ewc_stat import EWC_STAT_CODES


class BATWasteMapping(TypedDict):
    """Type definition for BAT waste mapping entries."""
    primary_waste: list[str]
    secondary_waste: list[str]
    excluded_waste: list[str]
    description: str


# BAT code to EWC-Stat waste mapping
# primary_waste: Most probable EWC-Stat codes (high confidence)
# secondary_waste: Possible but less likely waste types
# excluded_waste: Waste types this installation would NOT produce
BAT_TO_EWC_STAT: dict[str, BATWasteMapping] = {
    # === METALS PROCESSING ===
    'IS': {
        'primary_waste': ['W061', 'W124', 'W12A'],
        'secondary_waste': ['W032', 'W033'],
        'excluded_waste': ['W062', 'W091', 'W092', 'W093', 'W075'],
        'description': 'Iron and Steel: ferrous metal wastes, combustion wastes, slags',
    },
    'FMP': {
        'primary_waste': ['W061', 'W12A'],
        'secondary_waste': ['W032', 'W013'],
        'excluded_waste': ['W062', 'W091', 'W092', 'W093'],
        'description': 'Ferrous Metals Processing: ferrous wastes, processing slags',
    },
    'NFM': {
        'primary_waste': ['W062', 'W12A'],
        'secondary_waste': ['W032', 'W033'],
        'excluded_waste': ['W061', 'W091', 'W092', 'W093'],
        'description': 'Non-ferrous Metals: non-ferrous wastes, slags, sludges',
    },
    'SF': {
        'primary_waste': ['W061', 'W062', 'W12A'],
        'secondary_waste': ['W032'],
        'excluded_waste': ['W091', 'W092', 'W093'],
        'description': 'Smitheries/Foundries: ferrous and non-ferrous wastes, foundry sand',
    },
    'STM': {
        'primary_waste': ['W012', 'W032', 'W061', 'W062'],
        'secondary_waste': ['W013', 'W02A'],
        'excluded_waste': ['W091', 'W092', 'W093'],
        'description': 'Surface Treatment of Metals: acid/alkaline wastes, sludges, metal wastes',
    },

    # === MINERALS INDUSTRY ===
    'CLM': {
        'primary_waste': ['W12B', 'W124'],
        'secondary_waste': ['W121'],
        'excluded_waste': ['W061', 'W062', 'W091', 'W092', 'W093'],
        'description': 'Cement, Lime, MgO: mineral wastes, kiln dust, combustion residues',
    },
    'GLS': {
        'primary_waste': ['W071', 'W124'],
        'secondary_waste': ['W12B'],
        'excluded_waste': ['W061', 'W062', 'W091', 'W092', 'W093'],
        'description': 'Glass Manufacturing: glass cullet, furnace residues',
    },
    'CER': {
        'primary_waste': ['W12B', 'W121'],
        'secondary_waste': ['W124'],
        'excluded_waste': ['W061', 'W062', 'W091', 'W092', 'W093'],
        'description': 'Ceramics: broken ceramics, kiln wastes, mineral residues',
    },

    # === CHEMICAL INDUSTRY ===
    'LVOC': {
        'primary_waste': ['W011', 'W02A'],
        'secondary_waste': ['W032', 'W033'],
        'excluded_waste': ['W061', 'W062', 'W091', 'W092', 'W093'],
        'description': 'Large Volume Organic Chemicals: spent solvents, chemical wastes',
    },
    'LVIC': {
        'primary_waste': ['W012', 'W02A'],
        'secondary_waste': ['W032', 'W124'],
        'excluded_waste': ['W061', 'W091', 'W092', 'W093'],
        'description': 'Large Volume Inorganic Chemicals: acid/alkaline wastes, chemical residues',
    },
    'CAK': {
        'primary_waste': ['W012', 'W02A', 'W032'],
        'secondary_waste': ['W124'],
        'excluded_waste': ['W061', 'W091', 'W092', 'W093'],
        'description': 'Chlor-alkali: brine sludges, mercury wastes, chemical residues',
    },
    'OFC': {
        'primary_waste': ['W011', 'W02A'],
        'secondary_waste': ['W05'],
        'excluded_waste': ['W061', 'W062'],
        'description': 'Speciality/Fine Chemicals: solvents, pharmaceutical/chemical wastes',
    },
    'POL': {
        'primary_waste': ['W074', 'W02A'],
        'secondary_waste': ['W011'],
        'excluded_waste': ['W061', 'W091', 'W092', 'W093'],
        'description': 'Polymers Production: plastic wastes, off-spec materials, catalyst wastes',
    },

    # === FOOD & AGRICULTURE ===
    'FDM': {
        'primary_waste': ['W091', 'W092', 'W11'],
        'secondary_waste': ['W072'],
        'excluded_waste': ['W061', 'W062', 'W01-05'],
        'description': 'Food, Drink, Milk: organic wastes, sludges, packaging waste',
    },
    'SA': {
        'primary_waste': ['W091', 'W05'],
        'secondary_waste': ['W093'],
        'excluded_waste': ['W061', 'W062'],
        'description': 'Slaughterhouses: animal by-products, biological wastes',
    },
    'IRPP': {
        'primary_waste': ['W093', 'W091'],
        'secondary_waste': [],
        'excluded_waste': ['W061', 'W062', 'W01-05'],
        'description': 'Intensive Rearing Poultry/Pigs: manure, animal wastes',
    },

    # === ENERGY ===
    'LCP': {
        'primary_waste': ['W124', 'W12A'],
        'secondary_waste': ['W033'],
        'excluded_waste': ['W061', 'W062', 'W091', 'W092', 'W093'],
        'description': 'Large Combustion Plants: ash, FGD gypsum, combustion residues',
    },
    'REF': {
        'primary_waste': ['W013', 'W02A', 'W124'],
        'secondary_waste': ['W032', 'W033'],
        'excluded_waste': ['W061', 'W091', 'W092', 'W093'],
        'description': 'Refining: used oils, chemical wastes, catalyst residues',
    },

    # === WASTE MANAGEMENT ===
    'WT': {
        'primary_waste': [],  # Input-dependent
        'secondary_waste': ['W033', 'W12A', 'W103'],
        'excluded_waste': [],  # Can handle any waste type
        'description': 'Waste Treatment: output depends on input, produces treatment residues',
    },
    'WI': {
        'primary_waste': ['W124', 'W12A', 'W13'],
        'secondary_waste': ['W033'],
        'excluded_waste': ['W091', 'W092', 'W093'],
        'description': 'Waste Incineration: bottom ash, fly ash, stabilised wastes',
    },

    # === PAPER & WOOD ===
    'PP': {
        'primary_waste': ['W072', 'W11', 'W075'],
        'secondary_waste': ['W092'],
        'excluded_waste': ['W061', 'W062'],
        'description': 'Pulp and Paper: paper rejects, sludges, bark/wood residues',
    },
    'WBP': {
        'primary_waste': ['W075', 'W092'],
        'secondary_waste': ['W124'],
        'excluded_waste': ['W061', 'W062'],
        'description': 'Wood-based Panels: wood residues, dust, bark',
    },

    # === OTHER INDUSTRIES ===
    'TXT': {
        'primary_waste': ['W076', 'W011'],
        'secondary_waste': ['W02A'],
        'excluded_waste': ['W061', 'W091', 'W092', 'W093'],
        'description': 'Textiles: textile wastes, dye residues, solvents',
    },
    'TAN': {
        'primary_waste': ['W032', 'W091'],
        'secondary_waste': ['W02A'],
        'excluded_waste': ['W062', 'W075'],
        'description': 'Tanning: chrome sludges, animal trimmings, chemical wastes',
    },
    'STS': {
        'primary_waste': ['W011', 'W02A'],
        'secondary_waste': ['W032'],
        'excluded_waste': ['W091', 'W092', 'W093'],
        'description': 'Surface Treatment with Solvents: spent solvents, paint residues',
    },
    'CCS': {
        'primary_waste': ['W02A'],
        'secondary_waste': ['W032'],
        'excluded_waste': ['W061', 'W091', 'W092', 'W093'],
        'description': 'CO2 Capture and Storage: amine wastes, chemical residues',
    },
    'WPC': {
        'primary_waste': ['W075', 'W02A'],
        'secondary_waste': ['W011'],
        'excluded_waste': ['W061', 'W062', 'W091'],
        'description': 'Wood Preservation: treated wood, chemical residues',
    },
    'CWW': {
        'primary_waste': ['W11', 'W033'],
        'secondary_waste': ['W032'],
        'excluded_waste': ['W061', 'W062'],
        'description': 'Common Wastewater Treatment: sewage sludge, treatment residues',
    },
    'WGC': {
        'primary_waste': ['W02A', 'W032', 'W124'],
        'secondary_waste': ['W011', 'W033'],
        'excluded_waste': ['W061', 'W062', 'W091', 'W092', 'W093'],
        'description': 'Waste Gas Treatment (Chemical): scrubber sludges, spent catalysts, filter dust',
    },
}


def get_primary_waste_for_bat(
    bat_code: str,
    include_description: bool = False
) -> list[str] | list[dict]:
    """
    Get primary (most probable) EWC-Stat waste codes for a BAT code.

    Args:
        bat_code: BAT conclusion code (e.g., 'IS', 'NFM')
        include_description: If True, return list of dicts with code and description

    Example:
        >>> get_primary_waste_for_bat('IS')
        ['W061', 'W124', 'W12A']
        >>> get_primary_waste_for_bat('IS', include_description=True)
        [{'code': 'W061', 'description': 'Metal wastes, ferrous'}, ...]
    """
    mapping = BAT_TO_EWC_STAT.get(bat_code, {})
    codes = mapping.get('primary_waste', [])

    if include_description:
        return [
            {'code': c, 'description': EWC_STAT_CODES.get(c, f'Unknown: {c}')}
            for c in codes
        ]
    return codes


def get_excluded_waste_for_bat(
    bat_code: str,
    include_description: bool = False
) -> list[str] | list[dict]:
    """
    Get EWC-Stat waste codes that a BAT installation would NOT produce.

    Args:
        bat_code: BAT conclusion code (e.g., 'IS', 'NFM')
        include_description: If True, return list of dicts with code and description

    Example:
        >>> get_excluded_waste_for_bat('IS')
        ['W062', 'W091', 'W092', 'W093', 'W075']
    """
    mapping = BAT_TO_EWC_STAT.get(bat_code, {})
    codes = mapping.get('excluded_waste', [])

    if include_description:
        return [
            {'code': c, 'description': EWC_STAT_CODES.get(c, f'Unknown: {c}')}
            for c in codes
        ]
    return codes


def get_all_probable_waste_for_bat(
    bat_code: str,
    include_description: bool = False
) -> list[str] | list[dict]:
    """
    Get all probable waste codes (primary + secondary) for a BAT code.

    Args:
        bat_code: BAT conclusion code (e.g., 'IS', 'NFM')
        include_description: If True, return list of dicts with code and description

    Example:
        >>> get_all_probable_waste_for_bat('IS')
        ['W061', 'W124', 'W12A', 'W032', 'W033']
    """
    mapping = BAT_TO_EWC_STAT.get(bat_code, {})
    primary = mapping.get('primary_waste', [])
    secondary = mapping.get('secondary_waste', [])
    codes = primary + secondary

    if include_description:
        return [
            {'code': c, 'description': EWC_STAT_CODES.get(c, f'Unknown: {c}')}
            for c in codes
        ]
    return codes


def get_bat_for_ewc_stat(
    ewc_code: str,
    include_description: bool = False
) -> dict[str, list]:
    """
    Reverse lookup: find which BAT codes produce a given EWC-Stat waste code.

    Args:
        ewc_code: EWC-Stat waste code (e.g., 'W061')
        include_description: If True, return list of dicts with code and description

    Returns dict with 'primary' and 'secondary' lists.

    Example:
        >>> get_bat_for_ewc_stat('W061')
        {'primary': ['IS', 'FMP', 'SF', 'STM'], 'secondary': []}
        >>> get_bat_for_ewc_stat('W061', include_description=True)
        {'primary': [{'code': 'IS', 'description': 'Iron and Steel: ...'}, ...], ...}
    """
    primary_bats = []
    secondary_bats = []

    for bat_code, mapping in BAT_TO_EWC_STAT.items():
        if ewc_code in mapping.get('primary_waste', []):
            primary_bats.append(bat_code)
        elif ewc_code in mapping.get('secondary_waste', []):
            secondary_bats.append(bat_code)

    if include_description:
        return {
            'primary': [
                {'code': c, 'description': BAT_TO_EWC_STAT[c]['description']}
                for c in primary_bats
            ],
            'secondary': [
                {'code': c, 'description': BAT_TO_EWC_STAT[c]['description']}
                for c in secondary_bats
            ],
        }
    return {'primary': primary_bats, 'secondary': secondary_bats}


def get_bat_description(bat_code: str) -> str:
    """
    Get waste generation description for a BAT code.

    Example:
        >>> get_bat_description('IS')
        'Iron and Steel: ferrous metal wastes, combustion wastes, slags'
    """
    mapping = BAT_TO_EWC_STAT.get(bat_code, {})
    return mapping.get('description', f'Unknown BAT code: {bat_code}')


def get_valid_bat_codes() -> list[str]:
    """Get list of all valid BAT codes in the mapping."""
    return list(BAT_TO_EWC_STAT.keys())


def is_waste_valid_for_bat(bat_code: str, ewc_code: str) -> bool:
    """
    Check if a waste code is valid (producible) for a BAT installation.

    Uses implicit exclusion: only primary + secondary waste codes are valid.
    All unlisted codes are considered excluded.

    Args:
        bat_code: BAT conclusion code (e.g., 'IS', 'NFM')
        ewc_code: EWC-Stat waste code (e.g., 'W061')

    Returns:
        True if the waste code is in primary or secondary waste for the BAT,
        False otherwise (unlisted = excluded).

    Example:
        >>> is_waste_valid_for_bat('IS', 'W061')
        True  # primary waste for Iron & Steel
        >>> is_waste_valid_for_bat('IS', 'W032')
        True  # secondary waste for Iron & Steel
        >>> is_waste_valid_for_bat('IS', 'W071')
        False  # unlisted = excluded
    """
    valid_codes = get_all_probable_waste_for_bat(bat_code)
    return ewc_code in valid_codes


def get_valid_waste_matrix() -> dict[str, set[str]]:
    """
    Get complete matrix of valid BAT → waste code combinations.

    Uses implicit exclusion: only primary + secondary waste codes are valid.
    All unlisted codes are considered excluded.

    Returns:
        Dict where keys are BAT codes and values are sets of valid EWC-Stat codes.
        Useful for vectorized operations in pandas.

    Example:
        >>> matrix = get_valid_waste_matrix()
        >>> 'W061' in matrix['IS']
        True
        >>> 'W071' in matrix['IS']
        False
    """
    return {
        bat_code: set(get_all_probable_waste_for_bat(bat_code))
        for bat_code in BAT_TO_EWC_STAT
    }
