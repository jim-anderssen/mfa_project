"""
EWC-Stat waste classification codes.

Based on Eurostat waste classification (EWC-Stat/3).
Reference: https://ec.europa.eu/eurostat/ramon/nomenclatures/
"""

# EWC-Stat code definitions
EWC_STAT_CODES = {
    # Chemical and medical/healthcare waste (W01-05)
    'W01-05': 'Chemical and medical/healthcare waste',
    'W011': 'Spent solvents',
    'W012': 'Acid, alkaline or saline wastes',
    'W013': 'Used oils',
    'W02A': 'Chemical wastes',
    'W032': 'Industrial effluent sludges',
    'W033': 'Sludges and liquid wastes from waste treatment',
    'W05': 'Health care and biological wastes',

    # Metallic wastes (W06)
    'W06': 'Metallic wastes',
    'W061': 'Metal wastes, ferrous',
    'W062': 'Metal wastes, non-ferrous',
    'W063': 'Metal wastes, mixed ferrous and non-ferrous',

    # Non-metallic recyclable wastes (W07)
    'W07': 'Non-metallic recyclable wastes',
    'W071': 'Glass wastes',
    'W072': 'Paper and cardboard wastes',
    'W073': 'Rubber wastes',
    'W074': 'Plastic wastes',
    'W075': 'Wood wastes',
    'W076': 'Textile wastes',
    'W077': 'Waste containing PCB',
    'W06_07A': 'Recyclable wastes (metals and non-metals)',

    # Equipment (W08)
    'W08': 'Discarded equipment',
    'W08A': 'Discarded equipment (excluding discarded vehicles and batteries)',
    'W081': 'Discarded vehicles',
    'W0841': 'Batteries and accumulators wastes',

    # Animal and vegetal wastes (W09)
    'W09': 'Animal and vegetal wastes',
    'W091': 'Animal and mixed food waste',
    'W092': 'Vegetal wastes',
    'W093': 'Animal faeces, urine and manure',

    # Mixed ordinary wastes (W10)
    'W10': 'Mixed ordinary wastes',
    'W101': 'Household and similar wastes',
    'W102': 'Mixed and undifferentiated materials',
    'W103': 'Sorting residues',

    # Common sludges (W11)
    'W11': 'Common sludges',

    # Mineral and solidified wastes (W12-13)
    'W12-13': 'Mineral and solidified wastes',
    'W121': 'Mineral waste from construction and demolition',
    'W12B': 'Other mineral wastes',
    'W124': 'Combustion wastes',
    'W126': 'Soils',
    'W127': 'Dredging spoils',
    'W12A': 'Mineral wastes from waste treatment and stabilised wastes',
    'W128_13': 'Mineral wastes from waste treatment',
    'W13': 'Solidified, stabilised or vitrified wastes',
}

# NACE sector to typical waste codes mapping
NACE_TYPICAL_WASTES = {
    'C24': ['W061', 'W062', 'W063', 'W12A', 'W124'],  # Basic metals
    'C25': ['W061', 'W062', 'W063', 'W074'],  # Fabricated metal products
    'C10-C12': ['W091', 'W092', 'W11', 'W072'],  # Food, beverages, tobacco
    'C10': ['W091', 'W092', 'W11'],  # Food products
    'C11': ['W091', 'W092', 'W11'],  # Beverages
    'C12': ['W092', 'W076'],  # Tobacco
    'C13-C15': ['W076', 'W075'],  # Textiles, apparel, leather
    'C16': ['W075', 'W092'],  # Wood products
    'C17': ['W072', 'W11'],  # Paper products
    'C19': ['W013', 'W02A', 'W01-05'],  # Coke and petroleum
    'C20': ['W01-05', 'W011', 'W012', 'W02A'],  # Chemicals
    'C21': ['W01-05', 'W05'],  # Pharmaceuticals
    'C22': ['W073', 'W074'],  # Rubber and plastics
    'C23': ['W071', 'W121', 'W12B'],  # Non-metallic minerals
    'C26': ['W08A', 'W062'],  # Electronics
    'C27': ['W08A', 'W062'],  # Electrical equipment
    'C28': ['W061', 'W062'],  # Machinery
    'C29': ['W081', 'W061', 'W062'],  # Motor vehicles
    'C30': ['W081', 'W061', 'W062'],  # Other transport
    'C31-C32': ['W075', 'W076', 'W074'],  # Furniture and other
    'C33': ['W061', 'W08A'],  # Repair and installation
    'D': ['W124', 'W12A'],  # Electricity, gas
    'E': ['W11', 'W12A', 'W10'],  # Water, waste management
    'F': ['W121', 'W12B', 'W061'],  # Construction
}


def get_ewc_description(code: str) -> str:
    """Get description for an EWC-Stat code."""
    return EWC_STAT_CODES.get(code, f'Unknown code: {code}')


def get_typical_wastes_for_nace(nace_code: str) -> list:
    """Get typical waste codes for a NACE sector."""
    return NACE_TYPICAL_WASTES.get(nace_code, [])
