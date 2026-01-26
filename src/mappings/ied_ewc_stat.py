"""
Direct IED Annex I Activity to EWC-Stat waste classification mapping.

Provides a direct mapping from IED activity codes to probable waste types,
bypassing the intermediate BAT layer for simpler lookups. The mapping is
auto-generated from the IED->BAT->EWC chain but allows per-IED overrides.

References:
- IED Directive 2010/75/EU Annex I
- EWC-Stat waste classification: Eurostat waste statistics regulation
- BAT Reference Documents (BREFs)
"""

from typing import TypedDict

from .ewc_stat import EWC_STAT_CODES
from .ied_nace import IED_TO_NACE
from .bat_ewc_stat import BAT_TO_EWC_STAT


class IEDWasteMapping(TypedDict):
    """Type definition for IED waste mapping entries."""
    primary_waste: list[str]
    secondary_waste: list[str]
    description: str
    source_bat: str


def _generate_ied_to_ewc_stat() -> dict[str, IEDWasteMapping]:
    """
    Generate IED_TO_EWC_STAT by traversing IED -> BAT -> EWC chain.

    This function is called once at module load to populate the mapping.
    Per-IED overrides are applied after the base BAT mapping to ensure
    complete coverage of relevant waste codes.
    """
    mapping: dict[str, IEDWasteMapping] = {}

    for ied_code, ied_info in IED_TO_NACE.items():
        bat_ref = ied_info.get('bat_ref', '')
        bat_mapping = BAT_TO_EWC_STAT.get(bat_ref, {})

        mapping[ied_code] = {
            'primary_waste': bat_mapping.get('primary_waste', []).copy(),
            'secondary_waste': bat_mapping.get('secondary_waste', []).copy(),
            'description': ied_info.get('description', f'IED activity {ied_code}'),
            'source_bat': bat_ref,
        }

    # Apply per-IED overrides for waste codes not captured in BAT mapping
    # These are additional secondary waste codes relevant to specific activities
    _apply_ied_overrides(mapping)

    return mapping


# Per-IED waste code overrides
# These add waste codes that are relevant to specific IED activities
# but not captured in the base BAT → EWC mapping
IED_WASTE_OVERRIDES: dict[str, dict[str, list[str]]] = {
    # W063: Mixed ferrous/non-ferrous metal wastes
    # Foundries often process both metal types
    '2.4': {'add_secondary': ['W063']},    # Ferrous foundries (SF)
    '2.5(b)': {'add_secondary': ['W063']}, # Non-ferrous foundries (NFM)

    # W073: Rubber wastes
    # Polymer production and surface treatment with solvents
    '4.1(b)': {'add_secondary': ['W073']}, # Synthetic fibres (POL)
    '6.7': {'add_secondary': ['W073']},    # Surface treatment solvents (STS)

    # W077: Waste containing PCB
    # Old electrical equipment in large installations
    '1.1': {'add_secondary': ['W077']},    # Large combustion plants (transformers)
    '5.1': {'add_secondary': ['W077', 'W0841', 'W08A', 'W102', 'W126', 'W128_13']},

    # W0841: Batteries and accumulators
    # Non-ferrous metal processing (lead, nickel, cadmium)
    '2.5(a)': {'add_secondary': ['W0841']}, # NFM from ore/secondary

    # W08A: Discarded equipment
    # Waste treatment and recovery facilities
    '5.3(b)': {'add_secondary': ['W08A', 'W102']}, # Non-hazardous recovery

    # W102: Mixed and undifferentiated materials
    # Waste treatment sorting residues
    '5.3(a)': {'add_secondary': ['W102']}, # Non-hazardous disposal

    # W126: Contaminated soils
    # Refineries and remediation activities
    '1.2': {'add_secondary': ['W126']},    # Refining

    # W128_13: Mineral wastes from treatment
    # Waste incineration produces mineral residues
    '5.2': {'add_secondary': ['W128_13']}, # Waste incineration
}


def _apply_ied_overrides(mapping: dict[str, IEDWasteMapping]) -> None:
    """Apply per-IED waste code overrides to the mapping."""
    for ied_code, overrides in IED_WASTE_OVERRIDES.items():
        if ied_code not in mapping:
            continue

        # Add secondary waste codes (avoid duplicates)
        if 'add_secondary' in overrides:
            existing = set(mapping[ied_code]['secondary_waste'])
            for code in overrides['add_secondary']:
                if code not in existing:
                    mapping[ied_code]['secondary_waste'].append(code)


# IED Activity Code to EWC-Stat waste mapping
# Auto-generated from IED -> BAT -> EWC chain
# primary_waste: Most probable EWC-Stat codes (high confidence)
# secondary_waste: Possible but less likely waste types
# source_bat: Original BAT reference for traceability
IED_TO_EWC_STAT: dict[str, IEDWasteMapping] = _generate_ied_to_ewc_stat()


def get_waste_for_ied(
    ied_code: str,
    include_secondary: bool = True,
    include_description: bool = False
) -> list[str] | list[dict]:
    """
    Get EWC-Stat waste codes for an IED Annex I activity code.

    Args:
        ied_code: IED activity code (e.g., '2.2', '1.1')
        include_secondary: If True, include secondary waste types (default True)
        include_description: If True, return list of dicts with code and description

    Returns:
        List of EWC-Stat codes (or dicts if include_description=True)

    Example:
        >>> get_waste_for_ied('2.2')
        ['W061', 'W124', 'W12A', 'W032', 'W033']
        >>> get_waste_for_ied('2.2', include_secondary=False)
        ['W061', 'W124', 'W12A']
        >>> get_waste_for_ied('2.2', include_description=True)
        [{'code': 'W061', 'description': 'Metal wastes, ferrous'}, ...]
    """
    mapping = IED_TO_EWC_STAT.get(ied_code, {})
    codes = mapping.get('primary_waste', []).copy()

    if include_secondary:
        codes.extend(mapping.get('secondary_waste', []))

    if include_description:
        return [
            {'code': c, 'description': EWC_STAT_CODES.get(c, f'Unknown: {c}')}
            for c in codes
        ]
    return codes


def get_primary_waste_for_ied(
    ied_code: str,
    include_description: bool = False
) -> list[str] | list[dict]:
    """
    Get primary (most probable) EWC-Stat waste codes for an IED activity code.

    Args:
        ied_code: IED activity code (e.g., '2.2', '1.1')
        include_description: If True, return list of dicts with code and description

    Example:
        >>> get_primary_waste_for_ied('2.2')
        ['W061', 'W124', 'W12A']
    """
    return get_waste_for_ied(ied_code, include_secondary=False,
                             include_description=include_description)


def is_waste_valid_for_ied(ied_code: str, ewc_code: str) -> bool:
    """
    Check if a waste code is valid (producible) for an IED installation.

    Uses implicit exclusion: only primary + secondary waste codes are valid.
    All unlisted codes are considered excluded.

    Args:
        ied_code: IED activity code (e.g., '2.2', '1.1')
        ewc_code: EWC-Stat waste code (e.g., 'W061')

    Returns:
        True if the waste code is in primary or secondary waste for the IED,
        False otherwise (unlisted = excluded).

    Example:
        >>> is_waste_valid_for_ied('2.2', 'W061')
        True  # ferrous metal waste from steel production
        >>> is_waste_valid_for_ied('2.2', 'W071')
        False  # glass waste not from steel production
    """
    valid_codes = get_waste_for_ied(ied_code, include_secondary=True)
    return ewc_code in valid_codes


def get_ied_waste_matrix() -> dict[str, set[str]]:
    """
    Get complete matrix of valid IED -> waste code combinations.

    Uses implicit exclusion: only primary + secondary waste codes are valid.
    All unlisted codes are considered excluded.

    Returns:
        Dict where keys are IED codes and values are sets of valid EWC-Stat codes.
        Useful for vectorized operations in pandas.

    Example:
        >>> matrix = get_ied_waste_matrix()
        >>> 'W061' in matrix['2.2']
        True
        >>> 'W071' in matrix['2.2']
        False
    """
    return {
        ied_code: set(get_waste_for_ied(ied_code))
        for ied_code in IED_TO_EWC_STAT
    }


def get_ied_description(ied_code: str) -> str:
    """
    Get activity description for an IED code.

    Example:
        >>> get_ied_description('2.2')
        'Pig iron or steel production'
    """
    mapping = IED_TO_EWC_STAT.get(ied_code, {})
    return mapping.get('description', f'Unknown IED code: {ied_code}')


def get_source_bat(ied_code: str) -> str:
    """
    Get the source BAT reference document code for an IED activity.

    Example:
        >>> get_source_bat('2.2')
        'IS'
    """
    mapping = IED_TO_EWC_STAT.get(ied_code, {})
    return mapping.get('source_bat', '')


def get_valid_ied_codes() -> list[str]:
    """Get list of all valid IED codes in the mapping."""
    return list(IED_TO_EWC_STAT.keys())


def generate_lookup_table_csv(output_path: str) -> None:
    """
    Generate a CSV lookup table for IED to EWC-Stat mapping.

    Creates a denormalized table with one row per IED-waste code combination,
    suitable for joining with other datasets.

    Args:
        output_path: Path to write the CSV file

    Output columns:
        ied_code, ied_description, ewc_stat_code, ewc_stat_description,
        waste_category, source_bat
    """
    import csv

    rows = []
    for ied_code, mapping in sorted(IED_TO_EWC_STAT.items()):
        description = mapping['description']
        source_bat = mapping['source_bat']

        # Add primary waste codes
        for ewc_code in mapping['primary_waste']:
            rows.append({
                'ied_code': ied_code,
                'ied_description': description,
                'ewc_stat_code': ewc_code,
                'ewc_stat_description': EWC_STAT_CODES.get(ewc_code, ''),
                'waste_category': 'primary',
                'source_bat': source_bat,
            })

        # Add secondary waste codes
        for ewc_code in mapping['secondary_waste']:
            rows.append({
                'ied_code': ied_code,
                'ied_description': description,
                'ewc_stat_code': ewc_code,
                'ewc_stat_description': EWC_STAT_CODES.get(ewc_code, ''),
                'waste_category': 'secondary',
                'source_bat': source_bat,
            })

    fieldnames = [
        'ied_code', 'ied_description', 'ewc_stat_code',
        'ewc_stat_description', 'waste_category', 'source_bat'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
