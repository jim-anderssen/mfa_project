"""
PRODCOM to EWC-Stat waste classification mapping.

Maps 8-digit PRODCOM product codes to EWC-Stat waste categories
for material flow tracking from production to waste generation.

References:
- PRODCOM list: https://ec.europa.eu/eurostat/web/prodcom
- EWC-Stat: https://ec.europa.eu/eurostat/ramon/nomenclatures/
- Waste generation factors: Industry BAT reference documents
"""

from typing import Dict, List, Optional, TypedDict


class WasteMapping(TypedDict, total=False):
    """Type definition for waste mapping entries."""
    ewc_primary: str
    ewc_secondary: List[str]
    waste_factor: float
    byproduct_factors: Dict[str, float]
    description: str
    material_type: str


# PRODCOM 8-digit to EWC-Stat primary mapping
# Format: 'PRODCOM_CODE': WasteMapping
PRODCOM_TO_EWC: Dict[str, WasteMapping] = {
    # ===== BASIC METALS - IRON AND STEEL (NACE 24.10) =====
    '24101130': {
        'ewc_primary': 'W061',
        'ewc_secondary': ['W124', 'W12A'],
        'waste_factor': 0.15,
        'byproduct_factors': {'slag': 0.12, 'dust': 0.02, 'scale': 0.01},
        'description': 'Pig iron and spiegeleisen',
        'material_type': 'metal_ferrous',
    },
    '24102100': {
        'ewc_primary': 'W061',
        'ewc_secondary': ['W12A'],
        'waste_factor': 0.08,
        'byproduct_factors': {'scale': 0.03, 'trim': 0.05},
        'description': 'Flat rolled steel products',
        'material_type': 'metal_ferrous',
    },
    '24102030': {
        'ewc_primary': 'W061',
        'ewc_secondary': ['W12A'],
        'waste_factor': 0.10,
        'byproduct_factors': {'slag': 0.08, 'scale': 0.02},
        'description': 'Hot-rolled steel sheet',
        'material_type': 'metal_ferrous',
    },
    '24103100': {
        'ewc_primary': 'W061',
        'ewc_secondary': ['W12A'],
        'waste_factor': 0.06,
        'description': 'Cold-rolled steel products',
        'material_type': 'metal_ferrous',
    },
    '24104100': {
        'ewc_primary': 'W061',
        'ewc_secondary': ['W12A'],
        'waste_factor': 0.05,
        'description': 'Coated steel products',
        'material_type': 'metal_ferrous',
    },
    '24105100': {
        'ewc_primary': 'W061',
        'ewc_secondary': [],
        'waste_factor': 0.07,
        'description': 'Steel bars and rods',
        'material_type': 'metal_ferrous',
    },
    '24106100': {
        'ewc_primary': 'W061',
        'ewc_secondary': [],
        'waste_factor': 0.06,
        'description': 'Steel angles, shapes and sections',
        'material_type': 'metal_ferrous',
    },
    '24107100': {
        'ewc_primary': 'W061',
        'ewc_secondary': [],
        'waste_factor': 0.08,
        'description': 'Steel wire',
        'material_type': 'metal_ferrous',
    },

    # ===== NON-FERROUS METALS - ALUMINIUM (NACE 24.42) =====
    '24421100': {
        'ewc_primary': 'W062',
        'ewc_secondary': ['W12A', 'W124'],
        'waste_factor': 0.10,
        'byproduct_factors': {'red_mud': 1.5, 'dross': 0.05},
        'description': 'Unwrought aluminium',
        'material_type': 'metal_nonferrous',
    },
    '24422100': {
        'ewc_primary': 'W062',
        'ewc_secondary': ['W12A'],
        'waste_factor': 0.08,
        'byproduct_factors': {'dross': 0.04, 'scrap': 0.04},
        'description': 'Aluminium oxide (alumina)',
        'material_type': 'metal_nonferrous',
    },
    '24423000': {
        'ewc_primary': 'W062',
        'ewc_secondary': [],
        'waste_factor': 0.06,
        'description': 'Aluminium bars, rods and profiles',
        'material_type': 'metal_nonferrous',
    },
    '24424000': {
        'ewc_primary': 'W062',
        'ewc_secondary': [],
        'waste_factor': 0.05,
        'description': 'Aluminium plates, sheets and strip',
        'material_type': 'metal_nonferrous',
    },
    '24425000': {
        'ewc_primary': 'W062',
        'ewc_secondary': [],
        'waste_factor': 0.06,
        'description': 'Aluminium foil',
        'material_type': 'metal_nonferrous',
    },

    # ===== NON-FERROUS METALS - COPPER (NACE 24.44) =====
    '24441100': {
        'ewc_primary': 'W062',
        'ewc_secondary': ['W124'],
        'waste_factor': 0.08,
        'byproduct_factors': {'slag': 0.05, 'dust': 0.01},
        'description': 'Unwrought copper',
        'material_type': 'metal_nonferrous',
    },
    '24442000': {
        'ewc_primary': 'W062',
        'ewc_secondary': [],
        'waste_factor': 0.05,
        'description': 'Copper alloys unwrought',
        'material_type': 'metal_nonferrous',
    },
    '24443000': {
        'ewc_primary': 'W062',
        'ewc_secondary': [],
        'waste_factor': 0.04,
        'description': 'Copper bars, rods and profiles',
        'material_type': 'metal_nonferrous',
    },
    '24444000': {
        'ewc_primary': 'W062',
        'ewc_secondary': [],
        'waste_factor': 0.03,
        'description': 'Copper wire',
        'material_type': 'metal_nonferrous',
    },

    # ===== NON-FERROUS METALS - LEAD, ZINC, TIN (NACE 24.43) =====
    '24431100': {
        'ewc_primary': 'W062',
        'ewc_secondary': ['W01-05'],
        'waste_factor': 0.15,
        'byproduct_factors': {'slag': 0.10, 'dust': 0.03},
        'description': 'Unwrought lead',
        'material_type': 'metal_nonferrous',
    },
    '24432100': {
        'ewc_primary': 'W062',
        'ewc_secondary': ['W12A'],
        'waste_factor': 0.12,
        'byproduct_factors': {'slag': 0.08},
        'description': 'Unwrought zinc',
        'material_type': 'metal_nonferrous',
    },
    '24433100': {
        'ewc_primary': 'W062',
        'ewc_secondary': [],
        'waste_factor': 0.08,
        'description': 'Unwrought tin',
        'material_type': 'metal_nonferrous',
    },

    # ===== NON-FERROUS METALS - PRECIOUS METALS (NACE 24.41) =====
    '24411100': {
        'ewc_primary': 'W062',
        'ewc_secondary': ['W01-05'],
        'waste_factor': 0.05,
        'description': 'Silver unwrought',
        'material_type': 'metal_precious',
    },
    '24412100': {
        'ewc_primary': 'W062',
        'ewc_secondary': ['W01-05'],
        'waste_factor': 0.05,
        'description': 'Gold unwrought',
        'material_type': 'metal_precious',
    },
    '24413100': {
        'ewc_primary': 'W062',
        'ewc_secondary': ['W01-05'],
        'waste_factor': 0.05,
        'description': 'Platinum group metals unwrought',
        'material_type': 'metal_precious',
    },

    # ===== NON-FERROUS METALS - OTHER (NACE 24.45) =====
    '24451100': {
        'ewc_primary': 'W062',
        'ewc_secondary': ['W12A'],
        'waste_factor': 0.10,
        'description': 'Nickel and nickel alloys unwrought',
        'material_type': 'metal_nonferrous',
    },
    '24452000': {
        'ewc_primary': 'W062',
        'ewc_secondary': ['W12A'],
        'waste_factor': 0.10,
        'description': 'Cobalt mattes and products',
        'material_type': 'metal_nonferrous',
    },
    '24453000': {
        'ewc_primary': 'W062',
        'ewc_secondary': [],
        'waste_factor': 0.08,
        'description': 'Titanium and titanium alloys',
        'material_type': 'metal_nonferrous',
    },

    # ===== MINERAL PRODUCTS - CEMENT (NACE 23.51) =====
    '23511100': {
        'ewc_primary': 'W121',
        'ewc_secondary': ['W124'],
        'waste_factor': 0.02,
        'byproduct_factors': {'kiln_dust': 0.015, 'bypass_dust': 0.005},
        'description': 'Cement clinker',
        'material_type': 'mineral',
    },
    '23511210': {
        'ewc_primary': 'W121',
        'ewc_secondary': [],
        'waste_factor': 0.01,
        'description': 'Grey Portland cement',
        'material_type': 'mineral',
    },
    '23511220': {
        'ewc_primary': 'W121',
        'ewc_secondary': [],
        'waste_factor': 0.01,
        'description': 'White Portland cement',
        'material_type': 'mineral',
    },
    '23511250': {
        'ewc_primary': 'W121',
        'ewc_secondary': [],
        'waste_factor': 0.01,
        'description': 'Slag cement',
        'material_type': 'mineral',
    },

    # ===== MINERAL PRODUCTS - LIME (NACE 23.52) =====
    '23521010': {
        'ewc_primary': 'W12B',
        'ewc_secondary': ['W124'],
        'waste_factor': 0.01,
        'byproduct_factors': {'kiln_dust': 0.008},
        'description': 'Quicklime',
        'material_type': 'mineral',
    },
    '23521020': {
        'ewc_primary': 'W12B',
        'ewc_secondary': [],
        'waste_factor': 0.01,
        'description': 'Slaked lime',
        'material_type': 'mineral',
    },
    '23521030': {
        'ewc_primary': 'W12B',
        'ewc_secondary': [],
        'waste_factor': 0.02,
        'description': 'Hydraulic lime',
        'material_type': 'mineral',
    },

    # ===== MINERAL PRODUCTS - GLASS (NACE 23.11-23.19) =====
    '23111100': {
        'ewc_primary': 'W071',
        'ewc_secondary': ['W124'],
        'waste_factor': 0.05,
        'byproduct_factors': {'cullet': 0.03, 'dust': 0.01},
        'description': 'Flat glass',
        'material_type': 'mineral',
    },
    '23121100': {
        'ewc_primary': 'W071',
        'ewc_secondary': [],
        'waste_factor': 0.04,
        'description': 'Shaped and processed flat glass',
        'material_type': 'mineral',
    },
    '23131100': {
        'ewc_primary': 'W071',
        'ewc_secondary': [],
        'waste_factor': 0.06,
        'description': 'Hollow glass',
        'material_type': 'mineral',
    },
    '23141100': {
        'ewc_primary': 'W071',
        'ewc_secondary': [],
        'waste_factor': 0.04,
        'description': 'Glass fibres',
        'material_type': 'mineral',
    },

    # ===== CHEMICALS - BASIC (NACE 20.11-20.17) =====
    '20111100': {
        'ewc_primary': 'W02A',
        'ewc_secondary': [],
        'waste_factor': 0.02,
        'description': 'Industrial gases',
        'material_type': 'chemical',
    },
    '20132100': {
        'ewc_primary': 'W012',
        'ewc_secondary': ['W02A'],
        'waste_factor': 0.05,
        'byproduct_factors': {'neutralization_sludge': 0.03},
        'description': 'Inorganic acids',
        'material_type': 'chemical',
    },
    '20133100': {
        'ewc_primary': 'W012',
        'ewc_secondary': ['W02A'],
        'waste_factor': 0.04,
        'description': 'Inorganic bases (alkalis)',
        'material_type': 'chemical',
    },
    '20141100': {
        'ewc_primary': 'W02A',
        'ewc_secondary': ['W011'],
        'waste_factor': 0.03,
        'description': 'Basic organic chemicals',
        'material_type': 'chemical',
    },
    '20151000': {
        'ewc_primary': 'W02A',
        'ewc_secondary': ['W12B'],
        'waste_factor': 0.03,
        'byproduct_factors': {'gypsum': 0.02},
        'description': 'Fertilizers and nitrogen compounds',
        'material_type': 'chemical',
    },

    # ===== PLASTICS IN PRIMARY FORMS (NACE 20.16) =====
    '20165000': {
        'ewc_primary': 'W074',
        'ewc_secondary': ['W02A'],
        'waste_factor': 0.04,
        'byproduct_factors': {'off_spec': 0.02, 'catalyst': 0.005},
        'description': 'Plastics in primary forms',
        'material_type': 'polymer',
    },
    '20161000': {
        'ewc_primary': 'W074',
        'ewc_secondary': [],
        'waste_factor': 0.03,
        'description': 'Polyethylene',
        'material_type': 'polymer',
    },
    '20162000': {
        'ewc_primary': 'W074',
        'ewc_secondary': [],
        'waste_factor': 0.03,
        'description': 'Polypropylene',
        'material_type': 'polymer',
    },
    '20163000': {
        'ewc_primary': 'W074',
        'ewc_secondary': [],
        'waste_factor': 0.04,
        'description': 'Polystyrene',
        'material_type': 'polymer',
    },
    '20164000': {
        'ewc_primary': 'W074',
        'ewc_secondary': [],
        'waste_factor': 0.03,
        'description': 'Polyvinyl chloride (PVC)',
        'material_type': 'polymer',
    },

    # ===== PAPER AND PULP (NACE 17.11-17.12) =====
    '17111100': {
        'ewc_primary': 'W072',
        'ewc_secondary': ['W11', 'W092'],
        'waste_factor': 0.10,
        'byproduct_factors': {'black_liquor_solids': 0.50, 'bark': 0.10, 'sludge': 0.05},
        'description': 'Chemical wood pulp',
        'material_type': 'organic',
    },
    '17111200': {
        'ewc_primary': 'W072',
        'ewc_secondary': ['W092'],
        'waste_factor': 0.12,
        'byproduct_factors': {'bark': 0.12, 'sawdust': 0.05},
        'description': 'Mechanical wood pulp',
        'material_type': 'organic',
    },
    '17111300': {
        'ewc_primary': 'W072',
        'ewc_secondary': ['W11'],
        'waste_factor': 0.08,
        'byproduct_factors': {'deinking_sludge': 0.05},
        'description': 'Recycled pulp',
        'material_type': 'organic',
    },
    '17121100': {
        'ewc_primary': 'W072',
        'ewc_secondary': ['W11'],
        'waste_factor': 0.05,
        'byproduct_factors': {'broke': 0.03, 'sludge': 0.02},
        'description': 'Newsprint',
        'material_type': 'organic',
    },
    '17121200': {
        'ewc_primary': 'W072',
        'ewc_secondary': ['W11'],
        'waste_factor': 0.04,
        'description': 'Printing and writing paper',
        'material_type': 'organic',
    },
    '17121300': {
        'ewc_primary': 'W072',
        'ewc_secondary': [],
        'waste_factor': 0.05,
        'description': 'Packaging paper and board',
        'material_type': 'organic',
    },

    # ===== FOOD PRODUCTS (NACE 10.11-10.51) =====
    '10111100': {
        'ewc_primary': 'W091',
        'ewc_secondary': ['W05', 'W11'],
        'waste_factor': 0.35,
        'byproduct_factors': {'offal': 0.15, 'bone': 0.12, 'hide': 0.08},
        'description': 'Fresh or chilled bovine meat',
        'material_type': 'organic',
    },
    '10111200': {
        'ewc_primary': 'W091',
        'ewc_secondary': ['W05'],
        'waste_factor': 0.30,
        'byproduct_factors': {'offal': 0.12, 'bone': 0.10},
        'description': 'Fresh or chilled pig meat',
        'material_type': 'organic',
    },
    '10121100': {
        'ewc_primary': 'W091',
        'ewc_secondary': ['W05'],
        'waste_factor': 0.40,
        'byproduct_factors': {'offal': 0.15, 'feathers': 0.08},
        'description': 'Fresh or chilled poultry meat',
        'material_type': 'organic',
    },
    '10201100': {
        'ewc_primary': 'W091',
        'ewc_secondary': ['W11'],
        'waste_factor': 0.50,
        'byproduct_factors': {'bones': 0.20, 'heads': 0.15, 'viscera': 0.10},
        'description': 'Fresh or chilled fish',
        'material_type': 'organic',
    },
    '10511100': {
        'ewc_primary': 'W091',
        'ewc_secondary': ['W11'],
        'waste_factor': 0.10,
        'byproduct_factors': {'whey': 0.85},
        'description': 'Processed liquid milk',
        'material_type': 'organic',
    },
    '10512000': {
        'ewc_primary': 'W091',
        'ewc_secondary': ['W11'],
        'waste_factor': 0.80,
        'byproduct_factors': {'whey': 0.75},
        'description': 'Cheese',
        'material_type': 'organic',
    },
    '10513000': {
        'ewc_primary': 'W091',
        'ewc_secondary': ['W11'],
        'waste_factor': 0.05,
        'description': 'Butter and cream',
        'material_type': 'organic',
    },

    # ===== SECONDARY RAW MATERIALS (NACE 38.32) =====
    '38321110': {
        'ewc_primary': 'W061',
        'ewc_secondary': [],
        'waste_factor': 0.05,
        'description': 'Sorted ferrous metal waste',
        'material_type': 'secondary_metal',
    },
    '38321190': {
        'ewc_primary': 'W061',
        'ewc_secondary': [],
        'waste_factor': 0.05,
        'description': 'Other ferrous secondary raw materials',
        'material_type': 'secondary_metal',
    },
    '38321210': {
        'ewc_primary': 'W062',
        'ewc_secondary': [],
        'waste_factor': 0.06,
        'description': 'Aluminium secondary raw materials',
        'material_type': 'secondary_metal',
    },
    '38321290': {
        'ewc_primary': 'W062',
        'ewc_secondary': [],
        'waste_factor': 0.06,
        'description': 'Other non-ferrous secondary raw materials',
        'material_type': 'secondary_metal',
    },
    '38322910': {
        'ewc_primary': 'W074',
        'ewc_secondary': [],
        'waste_factor': 0.08,
        'description': 'Plastic secondary raw materials',
        'material_type': 'secondary_plastic',
    },
    '38322100': {
        'ewc_primary': 'W072',
        'ewc_secondary': [],
        'waste_factor': 0.05,
        'description': 'Paper secondary raw materials',
        'material_type': 'secondary_paper',
    },
    '38322200': {
        'ewc_primary': 'W071',
        'ewc_secondary': [],
        'waste_factor': 0.03,
        'description': 'Glass secondary raw materials',
        'material_type': 'secondary_glass',
    },
    '38322300': {
        'ewc_primary': 'W076',
        'ewc_secondary': [],
        'waste_factor': 0.08,
        'description': 'Textile secondary raw materials',
        'material_type': 'secondary_textile',
    },
    '38322400': {
        'ewc_primary': 'W073',
        'ewc_secondary': [],
        'waste_factor': 0.06,
        'description': 'Rubber secondary raw materials',
        'material_type': 'secondary_rubber',
    },
}


# Waste generation factors by NACE 4-digit code (fallback when PRODCOM mapping unavailable)
NACE_WASTE_GENERATION_FACTORS: Dict[str, Dict[str, float]] = {
    # Basic metals
    '24.10': {'total': 0.15, 'slag': 0.12, 'dust': 0.02, 'scale': 0.01},
    '24.20': {'total': 0.08, 'scale': 0.03, 'trim': 0.05},
    '24.31': {'total': 0.06},
    '24.32': {'total': 0.06},
    '24.33': {'total': 0.06},
    '24.34': {'total': 0.06},
    '24.41': {'total': 0.05},
    '24.42': {'total': 0.10, 'red_mud': 1.5, 'dross': 0.05},
    '24.43': {'total': 0.12, 'slag': 0.08},
    '24.44': {'total': 0.08, 'slag': 0.05},
    '24.45': {'total': 0.10},
    '24.51': {'total': 0.05, 'sand': 0.03},
    '24.52': {'total': 0.05, 'sand': 0.03},
    '24.53': {'total': 0.06},
    '24.54': {'total': 0.06},
    # Minerals
    '23.11': {'total': 0.05, 'cullet': 0.03},
    '23.12': {'total': 0.04},
    '23.13': {'total': 0.06},
    '23.14': {'total': 0.04},
    '23.19': {'total': 0.05},
    '23.20': {'total': 0.04},
    '23.31': {'total': 0.03},
    '23.32': {'total': 0.03},
    '23.41': {'total': 0.02},
    '23.42': {'total': 0.02},
    '23.43': {'total': 0.03},
    '23.44': {'total': 0.02},
    '23.49': {'total': 0.03},
    '23.51': {'total': 0.02, 'kiln_dust': 0.015},
    '23.52': {'total': 0.01, 'kiln_dust': 0.008},
    # Chemicals
    '20.11': {'total': 0.02},
    '20.12': {'total': 0.03},
    '20.13': {'total': 0.05},
    '20.14': {'total': 0.03},
    '20.15': {'total': 0.03, 'gypsum': 0.02},
    '20.16': {'total': 0.04},
    '20.17': {'total': 0.03},
    '20.20': {'total': 0.05},
    '20.30': {'total': 0.04},
    '20.41': {'total': 0.03},
    '20.42': {'total': 0.04},
    '20.51': {'total': 0.02},
    '20.52': {'total': 0.02},
    '20.53': {'total': 0.03},
    '20.59': {'total': 0.03},
    '20.60': {'total': 0.04},
    # Paper and pulp
    '17.11': {'total': 0.10, 'black_liquor': 0.50, 'bark': 0.10},
    '17.12': {'total': 0.05, 'broke': 0.03},
    '17.21': {'total': 0.04},
    '17.22': {'total': 0.04},
    '17.23': {'total': 0.05},
    '17.24': {'total': 0.04},
    '17.29': {'total': 0.04},
    # Food
    '10.11': {'total': 0.35, 'offal': 0.15, 'bone': 0.12},
    '10.12': {'total': 0.40, 'feathers': 0.08},
    '10.13': {'total': 0.30},
    '10.20': {'total': 0.50, 'bones': 0.20},
    '10.31': {'total': 0.15},
    '10.32': {'total': 0.10},
    '10.39': {'total': 0.12},
    '10.41': {'total': 0.20},
    '10.51': {'total': 0.10, 'whey': 0.85},
    '10.61': {'total': 0.05},
    '10.62': {'total': 0.03},
    # Energy
    '35.11': {'total': 0.10, 'ash': 0.10, 'fgd': 0.03},
    '35.21': {'total': 0.05},
    '35.30': {'total': 0.02},
    # Materials recovery
    '38.32': {'total': 0.05},
}


# Material type to EWC-Stat category mapping
MATERIAL_TO_EWC_CATEGORY: Dict[str, List[str]] = {
    'metal_ferrous': ['W061', 'W063'],
    'metal_nonferrous': ['W062', 'W063'],
    'metal_precious': ['W062'],
    'mineral': ['W121', 'W12B', 'W124', 'W071'],
    'organic': ['W091', 'W092', 'W075', 'W072'],
    'chemical': ['W01-05', 'W011', 'W012', 'W02A'],
    'polymer': ['W074', 'W073'],
    'secondary_metal': ['W061', 'W062'],
    'secondary_plastic': ['W074'],
    'secondary_paper': ['W072'],
    'secondary_glass': ['W071'],
    'secondary_textile': ['W076'],
    'secondary_rubber': ['W073'],
}


# ===== HELPER FUNCTIONS =====

def get_ewc_for_prodcom(prodcom_code: str) -> Optional[WasteMapping]:
    """
    Get EWC-Stat mapping for a PRODCOM code.

    Parameters
    ----------
    prodcom_code : str
        8-digit PRODCOM code

    Returns
    -------
    WasteMapping or None
        Mapping dictionary if found, None otherwise
    """
    return PRODCOM_TO_EWC.get(prodcom_code)


def get_waste_factor_for_nace(nace_code: str, factor_type: str = 'total') -> float:
    """
    Get waste generation factor for a NACE code.

    Parameters
    ----------
    nace_code : str
        4-digit NACE code (e.g., '24.10')
    factor_type : str
        Type of factor: 'total', 'slag', 'dust', etc.

    Returns
    -------
    float
        Waste factor (tonnes waste per tonne product), or 0.0 if not found
    """
    factors = NACE_WASTE_GENERATION_FACTORS.get(nace_code, {})
    return factors.get(factor_type, 0.0)


def get_prodcom_codes_for_nace(nace_code: str) -> List[str]:
    """
    Get all PRODCOM codes that map to a NACE code.

    Parameters
    ----------
    nace_code : str
        NACE code (e.g., '24.10')

    Returns
    -------
    list
        List of 8-digit PRODCOM codes
    """
    nace_prefix = nace_code.replace('.', '')[:4]
    return [code for code in PRODCOM_TO_EWC.keys() if code.startswith(nace_prefix)]


def get_nace_from_prodcom(prodcom_code: str) -> str:
    """
    Extract NACE 4-digit code from PRODCOM code.

    Parameters
    ----------
    prodcom_code : str
        8-digit PRODCOM code

    Returns
    -------
    str
        NACE code in format 'XX.XX'
    """
    return f"{prodcom_code[:2]}.{prodcom_code[2:4]}"


def is_secondary_material(prodcom_code: str) -> bool:
    """
    Check if PRODCOM code represents secondary raw materials.

    Parameters
    ----------
    prodcom_code : str
        8-digit PRODCOM code

    Returns
    -------
    bool
        True if secondary material
    """
    mapping = PRODCOM_TO_EWC.get(prodcom_code, {})
    material_type = mapping.get('material_type', '')
    return material_type.startswith('secondary_')


def get_ewc_categories_for_material_type(material_type: str) -> List[str]:
    """
    Get EWC-Stat categories for a material type.

    Parameters
    ----------
    material_type : str
        Material type (e.g., 'metal_ferrous', 'polymer')

    Returns
    -------
    list
        List of EWC-Stat codes
    """
    return MATERIAL_TO_EWC_CATEGORY.get(material_type, [])


def get_all_mapped_prodcom_codes() -> List[str]:
    """Get all PRODCOM codes in the mapping."""
    return list(PRODCOM_TO_EWC.keys())


def get_prodcom_codes_by_ewc(ewc_code: str) -> List[str]:
    """
    Get PRODCOM codes that map to a specific EWC-Stat code.

    Parameters
    ----------
    ewc_code : str
        EWC-Stat code (e.g., 'W061')

    Returns
    -------
    list
        List of PRODCOM codes
    """
    return [
        code for code, mapping in PRODCOM_TO_EWC.items()
        if mapping.get('ewc_primary') == ewc_code
    ]
