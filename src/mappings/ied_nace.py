"""
IED Annex I Activity to NACE to PRODCOM mapping.

Links Industrial Emissions Directive installations to statistical classifications
for allocating national PRODCOM production data to facility locations.

References:
- IED Directive 2010/75/EU Annex I
- E-PRTR Regulation (EC) No 166/2006
- NACE Rev. 2 / PRODCOM correspondence
"""

# NACE Rev. 2 code descriptions (commonly used in facility data)
NACE_DESCRIPTIONS = {
    # Agriculture
    'A': 'Agriculture, forestry and fishing',
    '01': 'Crop and animal production',
    '01.46': 'Raising of swine/pigs',
    '01.47': 'Raising of poultry',

    # Mining
    'B': 'Mining and quarrying',

    # Manufacturing - C
    'C': 'Manufacturing',
    'C10-C12': 'Food products, beverages, tobacco',
    'C10': 'Manufacture of food products',
    '10.11': 'Processing of meat',
    '10.12': 'Processing of poultry meat',
    '10.13': 'Meat and poultry products',
    '10.20': 'Processing of fish',
    '10.31': 'Processing of potatoes',
    '10.32': 'Fruit and vegetable juice',
    '10.39': 'Other fruit and vegetable processing',
    '10.41': 'Oils and fats',
    '10.51': 'Dairy products',
    '10.61': 'Grain mill products',
    '10.62': 'Starches and starch products',
    'C13-C15': 'Textiles, wearing apparel, leather',
    '13.30': 'Finishing of textiles',
    '15.11': 'Tanning of hides and skins',
    'C16': 'Wood and wood products (excl. furniture)',
    '16.10': 'Sawmilling and planing of wood',
    'C17': 'Paper and paper products',
    'C17_C18': 'Paper products and printing',
    '17.11': 'Manufacture of pulp',
    '17.12': 'Manufacture of paper and paperboard',
    'C19': 'Coke and refined petroleum products',
    '19.10': 'Manufacture of coke oven products',
    '19.20': 'Manufacture of refined petroleum',
    'C20': 'Chemicals and chemical products',
    'C20-C22': 'Chemicals, pharmaceuticals, rubber, plastics',
    '20.11': 'Industrial gases',
    '20.12': 'Dyes and pigments',
    '20.13': 'Other inorganic basic chemicals',
    '20.14': 'Other organic basic chemicals',
    '20.15': 'Fertilizers and nitrogen compounds',
    '20.16': 'Plastics in primary forms',
    '20.17': 'Synthetic rubber in primary forms',
    '20.20': 'Pesticides and agrochemical products',
    '20.30': 'Paints, varnishes, inks',
    '20.51': 'Explosives',
    '20.52': 'Glues',
    '20.53': 'Essential oils',
    '20.59': 'Other chemical products',
    '20.60': 'Man-made fibres',
    'C21': 'Basic pharmaceutical products',
    '21.10': 'Basic pharmaceutical products',
    '21.20': 'Pharmaceutical preparations',
    'C22': 'Rubber and plastic products',
    'C23': 'Other non-metallic mineral products',
    '23.11': 'Flat glass',
    '23.12': 'Shaped and processed flat glass',
    '23.13': 'Hollow glass',
    '23.14': 'Glass fibres',
    '23.19': 'Other glass products',
    '23.20': 'Refractory products',
    '23.31': 'Ceramic tiles and flags',
    '23.32': 'Bricks, tiles and construction products',
    '23.41': 'Ceramic household and ornamental articles',
    '23.42': 'Ceramic sanitary fixtures',
    '23.43': 'Ceramic insulators',
    '23.44': 'Other technical ceramic products',
    '23.49': 'Other ceramic products',
    '23.51': 'Cement',
    '23.52': 'Lime and plite',
    'C24': 'Basic metals',
    'C24_C25': 'Basic metals, fabricated metal products',
    '24.10': 'Basic iron and steel, ferro-alloys',
    '24.20': 'Steel tubes, pipes, hollow profiles',
    '24.31': 'Cold drawing of bars',
    '24.32': 'Cold rolling of narrow strip',
    '24.33': 'Cold forming or folding',
    '24.34': 'Cold drawing of wire',
    '24.41': 'Precious metals production',
    '24.42': 'Aluminium production',
    '24.43': 'Lead, zinc and tin production',
    '24.44': 'Copper production',
    '24.45': 'Other non-ferrous metal production',
    '24.46': 'Processing of nuclear fuel',
    '24.51': 'Casting of iron',
    '24.52': 'Casting of steel',
    '24.53': 'Casting of light metals',
    '24.54': 'Casting of other non-ferrous metals',
    'C25': 'Fabricated metal products',
    '25.61': 'Treatment and coating of metals',
    'C26': 'Computer, electronic, optical products',
    'C27': 'Electrical equipment',
    'C28': 'Machinery and equipment n.e.c.',
    'C29': 'Motor vehicles, trailers, semi-trailers',
    '29.20': 'Bodies for motor vehicles',
    'C30': 'Other transport equipment',
    'C31-C32': 'Furniture; other manufacturing',
    '31.01': 'Office and shop furniture',
    '31.02': 'Kitchen furniture',
    '31.09': 'Other furniture',
    'C33': 'Repair and installation of machinery',

    # Utilities - D, E
    'D': 'Electricity, gas, steam supply',
    '35.11': 'Production of electricity',
    '35.21': 'Manufacture of gas',
    '35.30': 'Steam and air conditioning supply',
    'E': 'Water supply; sewerage, waste management',
    '36.00': 'Water collection, treatment and supply',
    '38.12': 'Collection of hazardous waste',
    '38.21': 'Treatment and disposal of non-hazardous waste',
    '38.22': 'Treatment and disposal of hazardous waste',
    '38.31': 'Dismantling of wrecks',
    '38.32': 'Recovery of sorted materials',

    # Construction
    'F': 'Construction',
}


def get_nace_description(nace_code: str) -> str:
    """
    Get description for a NACE code.

    Handles both exact matches and grouped codes like 'C24_C25'.
    """
    # Exact match
    if nace_code in NACE_DESCRIPTIONS:
        return NACE_DESCRIPTIONS[nace_code]

    # Try without leading zeros for 2-digit codes
    if nace_code.startswith('0') and len(nace_code) == 2:
        return NACE_DESCRIPTIONS.get(nace_code[1:], f'Unknown: {nace_code}')

    # Handle combined codes like "C24, C25"
    if ', ' in nace_code:
        parts = [p.strip() for p in nace_code.split(',')]
        descriptions = [NACE_DESCRIPTIONS.get(p, p) for p in parts]
        return '; '.join(descriptions)

    return f'Unknown: {nace_code}'


# IED Annex I Activity Code to NACE mapping
# Format: 'IED_code': {'nace': [list], 'description': str, 'bat_ref': str}
IED_TO_NACE = {
    # Chapter I: Energy industries
    '1.1': {
        'nace': ['35.11', '35.30'],
        'description': 'Combustion installations > 50 MW',
        'bat_ref': 'LCP',
        'prodcom_relevant': True,
    },
    '1.2': {
        'nace': ['19.20'],
        'description': 'Refining of mineral oil and gas',
        'bat_ref': 'REF',
        'prodcom_relevant': True,
    },
    '1.3': {
        'nace': ['19.10'],
        'description': 'Coke ovens',
        'bat_ref': 'IS',
        'prodcom_relevant': True,
    },
    '1.4': {
        'nace': ['19.10', '35.21'],
        'description': 'Coal gasification and liquefaction',
        'bat_ref': 'LCP',
        'prodcom_relevant': True,
    },
    '1.4(b)': {
        'nace': ['19.10', '35.21'],
        'description': 'Coal gasification and liquefaction plants',
        'bat_ref': 'LCP',
        'prodcom_relevant': True,
    },

    # Chapter II: Production and processing of metals
    '2.1': {
        'nace': ['24.10'],
        'description': 'Metal ore roasting and sintering',
        'bat_ref': 'IS',
        'prodcom_relevant': True,
    },
    '2.2': {
        'nace': ['24.10'],
        'description': 'Pig iron or steel production',
        'bat_ref': 'IS',
        'prodcom_relevant': True,
    },
    '2.3': {
        'nace': ['24.10', '24.20', '24.31', '24.32', '24.33', '24.34'],
        'description': 'Hot-rolling mills, forges, foundries > 20t/hr',
        'bat_ref': 'FMP',
        'prodcom_relevant': True,
    },
    '2.3(a)': {
        'nace': ['24.10', '24.20'],
        'description': 'Hot-rolling mills > 20t/hr',
        'bat_ref': 'FMP',
        'prodcom_relevant': True,
    },
    '2.3(b)': {
        'nace': ['24.10', '24.31', '24.32', '24.33', '24.34'],
        'description': 'Smitheries with hammers > 50kJ',
        'bat_ref': 'FMP',
        'prodcom_relevant': True,
    },
    '2.3(c)': {
        'nace': ['25.61'],
        'description': 'Protective fused metal coatings > 2t/hr',
        'bat_ref': 'FMP',
        'prodcom_relevant': True,
    },
    '2.4': {
        'nace': ['24.10', '24.51', '24.52'],
        'description': 'Ferrous metal foundries > 20t/day',
        'bat_ref': 'SF',
        'prodcom_relevant': True,
    },
    '2.5(a)': {
        'nace': ['24.41', '24.42', '24.43', '24.44', '24.45'],
        'description': 'Non-ferrous metals from ore/concentrates/secondary',
        'bat_ref': 'NFM',
        'prodcom_relevant': True,
    },
    '2.5(b)': {
        'nace': ['24.53', '24.54'],
        'description': 'Non-ferrous metal foundries > 4t/day Pb/Cd, > 20t/day others',
        'bat_ref': 'NFM',
        'prodcom_relevant': True,
    },
    '2.6': {
        'nace': ['25.61'],
        'description': 'Surface treatment using electrolytic/chemical process > 30m³',
        'bat_ref': 'STM',
        'prodcom_relevant': True,
    },

    # Chapter III: Mineral industry
    '3.1(a)': {
        'nace': ['23.51'],
        'description': 'Cement clinker production',
        'bat_ref': 'CLM',
        'prodcom_relevant': True,
    },
    '3.1(b)': {
        'nace': ['23.52'],
        'description': 'Lime production > 50t/day',
        'bat_ref': 'CLM',
        'prodcom_relevant': True,
    },
    '3.1(c)': {
        'nace': ['23.52'],
        'description': 'MgO production',
        'bat_ref': 'CLM',
        'prodcom_relevant': True,
    },
    '3.2': {
        'nace': ['23.52'],
        'description': 'Asbestos production',
        'bat_ref': 'CLM',
        'prodcom_relevant': False,
    },
    '3.3': {
        'nace': ['23.11', '23.12', '23.13', '23.14', '23.19'],
        'description': 'Glass manufacture > 20t/day',
        'bat_ref': 'GLS',
        'prodcom_relevant': True,
    },
    '3.4': {
        'nace': ['23.20'],
        'description': 'Mineral fibres manufacture',
        'bat_ref': 'GLS',
        'prodcom_relevant': True,
    },
    '3.5': {
        'nace': ['23.31', '23.32', '23.41', '23.42', '23.43', '23.44', '23.49'],
        'description': 'Ceramic products > 75t/day',
        'bat_ref': 'CER',
        'prodcom_relevant': True,
    },

    # Chapter IV: Chemical industry
    '4.1(a)': {
        'nace': ['20.11', '20.12', '20.13', '20.14', '20.15', '20.16', '20.17'],
        'description': 'Organic chemicals production',
        'bat_ref': 'LVOC',
        'prodcom_relevant': True,
    },
    '4.1(b)': {
        'nace': ['20.60'],
        'description': 'Production of synthetic fibres',
        'bat_ref': 'POL',
        'prodcom_relevant': True,
    },
    '4.1(c)': {
        'nace': ['20.14'],
        'description': 'Oxygen-containing hydrocarbons',
        'bat_ref': 'LVOC',
        'prodcom_relevant': True,
    },
    '4.1(d)': {
        'nace': ['20.14'],
        'description': 'Sulphur-containing hydrocarbons',
        'bat_ref': 'LVOC',
        'prodcom_relevant': True,
    },
    '4.1(e)': {
        'nace': ['20.15'],
        'description': 'Nitrogen-containing hydrocarbons',
        'bat_ref': 'LVOC',
        'prodcom_relevant': True,
    },
    '4.1(f)': {
        'nace': ['20.14'],
        'description': 'Halogen-containing hydrocarbons',
        'bat_ref': 'LVOC',
        'prodcom_relevant': True,
    },
    '4.1(g)': {
        'nace': ['20.14'],
        'description': 'Organometallic compounds',
        'bat_ref': 'LVOC',
        'prodcom_relevant': True,
    },
    '4.1(h)': {
        'nace': ['20.16'],
        'description': 'Plastics (PVC, PE, PP, PS, etc.)',
        'bat_ref': 'POL',
        'prodcom_relevant': True,
    },
    '4.1(i)': {
        'nace': ['20.14'],
        'description': 'Phosphorus-containing hydrocarbons',
        'bat_ref': 'LVOC',
        'prodcom_relevant': True,
    },
    '4.1(j)': {
        'nace': ['20.14', '20.59'],
        'description': 'Surface-active agents and surfactants',
        'bat_ref': 'LVOC',
        'prodcom_relevant': True,
    },
    '4.1(k)': {
        'nace': ['20.14', '20.59'],
        'description': 'Other organic chemicals n.e.c.',
        'bat_ref': 'LVOC',
        'prodcom_relevant': True,
    },
    '4.2(a)': {
        'nace': ['20.11', '20.13', '20.15'],
        'description': 'Inorganic chemicals production',
        'bat_ref': 'LVIC',
        'prodcom_relevant': True,
    },
    '4.2(b)': {
        'nace': ['20.15'],
        'description': 'Fertilizers production',
        'bat_ref': 'LVIC',
        'prodcom_relevant': True,
    },
    '4.2(c)': {
        'nace': ['20.13'],
        'description': 'Production of bases (ammonia, sodium hydroxide, etc.)',
        'bat_ref': 'LVIC',
        'prodcom_relevant': True,
    },
    '4.2(d)': {
        'nace': ['20.13'],
        'description': 'Production of salts (ammonium chloride, etc.)',
        'bat_ref': 'LVIC',
        'prodcom_relevant': True,
    },
    '4.2(e)': {
        'nace': ['20.13'],
        'description': 'Production of non-metals (silicon, phosphorus, etc.)',
        'bat_ref': 'LVIC',
        'prodcom_relevant': True,
    },
    '4.3': {
        'nace': ['20.20'],
        'description': 'Plant protection products and biocides',
        'bat_ref': 'OFC',
        'prodcom_relevant': True,
    },
    '4.4': {
        'nace': ['21.10', '21.20'],
        'description': 'Pharmaceutical products',
        'bat_ref': 'OFC',
        'prodcom_relevant': True,
    },
    '4.5': {
        'nace': ['20.51', '20.52', '20.53', '20.59'],
        'description': 'Explosives production',
        'bat_ref': 'OFC',
        'prodcom_relevant': True,
    },
    '4.6': {
        'nace': ['20.59'],
        'description': 'Other chemical products n.e.c.',
        'bat_ref': 'OFC',
        'prodcom_relevant': True,
    },

    # Chapter V: Waste management
    '5.1': {
        'nace': ['38.12', '38.22'],
        'description': 'Hazardous waste disposal/recovery > 10t/day',
        'bat_ref': 'WT',
        'prodcom_relevant': False,
    },
    '5.2': {
        'nace': ['38.21'],
        'description': 'Waste incineration > 3t/hr',
        'bat_ref': 'WI',
        'prodcom_relevant': False,
    },
    '5.3(a)': {
        'nace': ['38.21'],
        'description': 'Non-hazardous waste disposal > 50t/day',
        'bat_ref': 'WT',
        'prodcom_relevant': False,
    },
    '5.3(b)': {
        'nace': ['38.21', '38.32'],
        'description': 'Non-hazardous waste recovery > 75t/day',
        'bat_ref': 'WT',
        'prodcom_relevant': True,  # Materials recovery (38.32)
    },
    '5.4': {
        'nace': ['38.21'],
        'description': 'Landfills > 10t/day',
        'bat_ref': 'WT',
        'prodcom_relevant': False,
    },
    '5.5': {
        'nace': ['38.21'],
        'description': 'Underground storage of hazardous waste',
        'bat_ref': 'WT',
        'prodcom_relevant': False,
    },
    '5.6': {
        'nace': ['38.21'],
        'description': 'Temporary storage of hazardous waste > 50t',
        'bat_ref': 'WT',
        'prodcom_relevant': False,
    },

    # Chapter VI: Other activities
    '6.1(a)': {
        'nace': ['17.11'],
        'description': 'Pulp from timber > 20t/day',
        'bat_ref': 'PP',
        'prodcom_relevant': True,
    },
    '6.1(b)': {
        'nace': ['17.12'],
        'description': 'Paper/cardboard production > 20t/day',
        'bat_ref': 'PP',
        'prodcom_relevant': True,
    },
    '6.1(c)': {
        'nace': ['17.11', '17.12'],
        'description': 'Wood-based panels',
        'bat_ref': 'WBP',
        'prodcom_relevant': True,
    },
    '6.2': {
        'nace': ['13.30'],
        'description': 'Textile treatment > 10t/day',
        'bat_ref': 'TXT',
        'prodcom_relevant': True,
    },
    '6.3': {
        'nace': ['15.11'],
        'description': 'Tanning of hides > 12t/day',
        'bat_ref': 'TAN',
        'prodcom_relevant': True,
    },
    '6.4(a)': {
        'nace': ['10.11', '10.12', '10.13', '10.20'],
        'description': 'Slaughterhouses > 50t/day',
        'bat_ref': 'FDM',
        'prodcom_relevant': True,
    },
    '6.4(b)(i)': {
        'nace': ['10.11', '10.12', '10.13', '10.20', '10.39', '10.41'],
        'description': 'Food from animal raw materials > 75t/day',
        'bat_ref': 'FDM',
        'prodcom_relevant': True,
    },
    '6.4(b)(ii)': {
        'nace': ['10.31', '10.32', '10.39', '10.41', '10.61', '10.62'],
        'description': 'Food from vegetable raw materials > 300t/day',
        'bat_ref': 'FDM',
        'prodcom_relevant': True,
    },
    '6.4(c)': {
        'nace': ['10.51'],
        'description': 'Milk processing > 200t/day',
        'bat_ref': 'FDM',
        'prodcom_relevant': True,
    },
    '6.5': {
        'nace': ['10.41'],
        'description': 'Animal carcasses/waste disposal > 10t/day',
        'bat_ref': 'SA',
        'prodcom_relevant': True,
    },
    '6.6(a)': {
        'nace': ['01.47'],
        'description': 'Intensive poultry rearing > 40,000 places',
        'bat_ref': 'IRPP',
        'prodcom_relevant': False,
    },
    '6.6(b)': {
        'nace': ['01.46'],
        'description': 'Intensive pig rearing > 2,000 production pigs',
        'bat_ref': 'IRPP',
        'prodcom_relevant': False,
    },
    '6.6(c)': {
        'nace': ['01.46'],
        'description': 'Intensive pig rearing > 750 sows',
        'bat_ref': 'IRPP',
        'prodcom_relevant': False,
    },
    '6.7': {
        'nace': ['20.30', '25.61', '29.20', '31.01', '31.02', '31.09'],
        'description': 'Surface treatment with organic solvents > 150kg/hr',
        'bat_ref': 'STS',
        'prodcom_relevant': True,
    },
    '6.8': {
        'nace': ['24.46'],
        'description': 'Carbon/electrographite production',
        'bat_ref': 'NFM',
        'prodcom_relevant': True,
    },
    '6.9': {
        'nace': ['38.31'],
        'description': 'CO2 capture > 1.5Mt/year',
        'bat_ref': 'CCS',
        'prodcom_relevant': False,
    },
    '6.10': {
        'nace': ['16.10'],
        'description': 'Wood preservation > 75m³/day',
        'bat_ref': 'WPC',
        'prodcom_relevant': True,
    },
    '6.11': {
        'nace': ['36.00'],
        'description': 'Independently operated wastewater treatment',
        'bat_ref': 'CWW',
        'prodcom_relevant': False,
    },
}

# NACE to PRODCOM mapping for secondary raw materials/byproducts
# These are the PRODCOM codes most relevant for waste/byproduct quantification
NACE_TO_PRODCOM_BYPRODUCTS = {
    # Iron and steel
    '24.10': {
        'primary_products': ['24.10.11', '24.10.12', '24.10.13', '24.10.14'],
        'byproducts': ['24.10.11.30', '24.10.12.10'],  # Includes slag products
        'waste_generation_factor': 0.15,  # tonnes waste per tonne steel
        'slag_factor': 0.12,  # tonnes slag per tonne steel
    },
    # Non-ferrous metals
    '24.41': {
        'primary_products': ['24.41'],
        'byproducts': [],
        'waste_generation_factor': 0.05,
    },
    '24.42': {
        'primary_products': ['24.42'],
        'byproducts': [],
        'waste_generation_factor': 0.10,
        'red_mud_factor': 1.5,  # For alumina production
    },
    '24.43': {
        'primary_products': ['24.43'],
        'byproducts': [],
        'waste_generation_factor': 0.08,
    },
    '24.44': {
        'primary_products': ['24.44'],
        'byproducts': [],
        'waste_generation_factor': 0.15,
    },
    '24.45': {
        'primary_products': ['24.45'],
        'byproducts': [],
        'waste_generation_factor': 0.10,
    },
    # Cement and lime
    '23.51': {
        'primary_products': ['23.51.11', '23.51.12'],
        'byproducts': ['23.51.12.50'],  # Slag cement
        'waste_generation_factor': 0.02,
        'can_use_slag': True,
    },
    '23.52': {
        'primary_products': ['23.52.10'],
        'byproducts': [],
        'waste_generation_factor': 0.01,
    },
    # Power generation
    '35.11': {
        'primary_products': [],
        'byproducts': [],
        'ash_factor': 0.10,  # For coal plants
        'fgd_sludge_factor': 0.03,
    },
    # Materials recovery
    '38.32': {
        'primary_products': ['38.32.11', '38.32.12', '38.32.13', '38.32.21', '38.32.29'],
        'byproducts': [],
        'is_secondary_materials': True,
    },
}

# BAT reference document codes
BAT_REFERENCE_DOCS = {
    'LCP': 'Large Combustion Plants',
    'REF': 'Refining of Mineral Oil and Gas',
    'IS': 'Iron and Steel Production',
    'FMP': 'Ferrous Metals Processing',
    'SF': 'Smitheries and Foundries',
    'NFM': 'Non-Ferrous Metals Industries',
    'STM': 'Surface Treatment of Metals',
    'CLM': 'Cement, Lime and Magnesium Oxide',
    'GLS': 'Manufacture of Glass',
    'CER': 'Ceramic Manufacturing',
    'LVOC': 'Production of Large Volume Organic Chemicals',
    'LVIC': 'Production of Large Volume Inorganic Chemicals',
    'POL': 'Production of Polymers',
    'OFC': 'Production of Speciality Inorganic Chemicals',
    'WT': 'Waste Treatment',
    'WI': 'Waste Incineration',
    'PP': 'Production of Pulp, Paper and Board',
    'WBP': 'Wood-based Panels Production',
    'TXT': 'Textiles Industry',
    'TAN': 'Tanning of Hides and Skins',
    'FDM': 'Food, Drink and Milk Industries',
    'SA': 'Slaughterhouses and Animals By-products Industries',
    'IRPP': 'Intensive Rearing of Poultry or Pigs',
    'STS': 'Surface Treatment Using Organic Solvents',
    'CCS': 'CO2 Capture and Storage',
    'WPC': 'Wood Preservation with Chemicals',
    'CWW': 'Common Waste Water Treatment',
}


def get_nace_for_ied(ied_code: str) -> list:
    """Get NACE codes for an IED Annex I activity code."""
    mapping = IED_TO_NACE.get(ied_code, {})
    return mapping.get('nace', [])


def get_ied_description(ied_code: str) -> str:
    """Get description for an IED activity code."""
    mapping = IED_TO_NACE.get(ied_code, {})
    return mapping.get('description', f'Unknown IED code: {ied_code}')


def get_bat_reference(ied_code: str) -> str:
    """Get BAT reference document code for an IED activity."""
    mapping = IED_TO_NACE.get(ied_code, {})
    bat_code = mapping.get('bat_ref', '')
    return BAT_REFERENCE_DOCS.get(bat_code, bat_code)


def is_prodcom_relevant(ied_code: str) -> bool:
    """Check if IED activity has relevant PRODCOM production data."""
    mapping = IED_TO_NACE.get(ied_code, {})
    return mapping.get('prodcom_relevant', False)


def get_prodcom_byproduct_info(nace_code: str) -> dict:
    """Get PRODCOM byproduct information for a NACE code."""
    return NACE_TO_PRODCOM_BYPRODUCTS.get(nace_code, {})


def get_all_nace_for_bat(bat_code: str) -> list:
    """Get all NACE codes associated with a BAT reference document."""
    nace_codes = []
    for ied_code, mapping in IED_TO_NACE.items():
        if mapping.get('bat_ref') == bat_code:
            nace_codes.extend(mapping.get('nace', []))
    return list(set(nace_codes))
