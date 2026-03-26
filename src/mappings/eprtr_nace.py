"""Direct EPRTR Annex I activity → NACE Rev. 2 mapping.

Bypasses the two-step EPRTR→IED→NACE chain for simpler lookups.

References:
- E-PRTR Regulation (EC) No 166/2006, Annex I
- NACE Rev. 2
"""

# EPRTR Annex I Activity Code → NACE mapping
# Format: 'eprtr_code': {'nace': [list], 'description': str}
EPRTR_TO_NACE = {
    # Chapter 1: Energy industries
    '1(a)': {
        'nace': ['19.20'],
        'description': 'Mineral oil and gas refineries',
    },
    '1(b)': {
        'nace': ['19.10', '35.21'],
        'description': 'Coal gasification and liquefaction plants',
    },
    '1(c)': {
        'nace': ['35.11', '35.30'],
        'description': 'Thermal power stations and combustion installations >50 MW',
    },
    '1(d)': {
        'nace': ['19.10'],
        'description': 'Coke ovens',
    },
    '1(e)': {
        'nace': ['24.10'],
        'description': 'Coal rolling mills >1 t/hr',
    },
    '1(f)': {
        'nace': ['35.11'],
        'description': 'Combustion installations for coal products >20 MW',
    },

    # Chapter 2: Production and processing of metals
    '2(a)': {
        'nace': ['24.10'],
        'description': 'Metal ore roasting and sintering',
    },
    '2(b)': {
        'nace': ['24.10'],
        'description': 'Pig iron or steel production (primary/secondary) incl. continuous casting',
    },
    '2(c)': {
        'nace': ['24.10', '24.20', '25.61'],
        'description': 'Processing of ferrous metals (general)',
    },
    '2(c)(i)': {
        'nace': ['24.10', '24.20'],
        'description': 'Hot-rolling mills >20 t/hr',
    },
    '2(c)(ii)': {
        'nace': ['24.10', '24.31', '24.32', '24.33', '24.34'],
        'description': 'Smitheries with hammers >50 kJ per hammer',
    },
    '2(c)(iii)': {
        'nace': ['25.61'],
        'description': 'Application of protective fused metal coatings >2 t/hr',
    },
    '2(d)': {
        'nace': ['24.10', '24.51', '24.52'],
        'description': 'Ferrous metal foundries >20 t/day',
    },
    '2(e)': {
        'nace': ['24.41', '24.42', '24.43', '24.44', '24.45', '24.53', '24.54'],
        'description': 'Non-ferrous metals (general)',
    },
    '2(e)(i)': {
        'nace': ['24.41', '24.42', '24.43', '24.44', '24.45'],
        'description': 'Non-ferrous metals from ore, concentrates, or secondary raw materials',
    },
    '2(e)(ii)': {
        'nace': ['24.42', '24.43', '24.44', '24.45', '24.53', '24.54'],
        'description': 'Non-ferrous metal melting and alloying',
    },
    '2(f)': {
        'nace': ['25.61'],
        'description': 'Surface treatment using electrolytic or chemical processes',
    },

    # Chapter 3: Mineral industry
    '3(a)': {
        'nace': ['23.51'],
        'description': 'Underground mining and related operations',
    },
    '3(b)': {
        'nace': ['23.51'],
        'description': 'Opencast mining and quarrying',
    },
    '3(c)': {
        'nace': ['23.51'],
        'description': 'Cement and cement clinker production',
    },
    '3(c)(i)': {
        'nace': ['23.51'],
        'description': 'Cement clinker in rotary kilns >500 t/day',
    },
    '3(c)(ii)': {
        'nace': ['23.52'],
        'description': 'Lime production >50 t/day',
    },
    '3(c)(iii)': {
        'nace': ['23.52'],
        'description': 'MgO production',
    },
    '3(d)': {
        'nace': ['23.52'],
        'description': 'Asbestos and asbestos-based products',
    },
    '3(e)': {
        'nace': ['23.11', '23.12', '23.13', '23.14', '23.19'],
        'description': 'Glass and glass fibre manufacture >20 t/day',
    },
    '3(f)': {
        'nace': ['23.20'],
        'description': 'Mineral fibres manufacture',
    },
    '3(g)': {
        'nace': ['23.31', '23.32', '23.41', '23.42', '23.43', '23.44', '23.49'],
        'description': 'Ceramic products by firing >75 t/day',
    },

    # Chapter 4: Chemical industry
    '4(a)': {
        'nace': ['20.11', '20.12', '20.13', '20.14', '20.15', '20.16', '20.17'],
        'description': 'Organic chemicals (general)',
    },
    '4(a)(i)': {
        'nace': ['20.14'],
        'description': 'Simple hydrocarbons',
    },
    '4(a)(ii)': {
        'nace': ['20.60'],
        'description': 'Oxygen-containing hydrocarbons',
    },
    '4(a)(iii)': {
        'nace': ['20.14'],
        'description': 'Sulphur-containing hydrocarbons',
    },
    '4(a)(iv)': {
        'nace': ['20.14'],
        'description': 'Nitrogen-containing hydrocarbons',
    },
    '4(a)(v)': {
        'nace': ['20.15'],
        'description': 'Phosphorus-containing hydrocarbons',
    },
    '4(a)(vi)': {
        'nace': ['20.14'],
        'description': 'Halogen-containing hydrocarbons',
    },
    '4(a)(vii)': {
        'nace': ['20.14'],
        'description': 'Organometallic compounds',
    },
    '4(a)(viii)': {
        'nace': ['20.16'],
        'description': 'Plastics (PVC, PE, PP, PS, etc.)',
    },
    '4(a)(ix)': {
        'nace': ['20.14'],
        'description': 'Synthetic rubber',
    },
    '4(a)(x)': {
        'nace': ['20.14', '20.59'],
        'description': 'Surface-active agents and surfactants',
    },
    '4(a)(xi)': {
        'nace': ['20.14', '20.59'],
        'description': 'Other organic chemicals n.e.c.',
    },
    '4(b)': {
        'nace': ['20.11', '20.13', '20.15'],
        'description': 'Inorganic chemicals (general)',
    },
    '4(b)(i)': {
        'nace': ['20.11'],
        'description': 'Industrial gases',
    },
    '4(b)(ii)': {
        'nace': ['20.13'],
        'description': 'Acids',
    },
    '4(b)(iii)': {
        'nace': ['20.13'],
        'description': 'Bases',
    },
    '4(b)(iv)': {
        'nace': ['20.13'],
        'description': 'Salts',
    },
    '4(b)(v)': {
        'nace': ['20.13'],
        'description': 'Non-metals, metal oxides, inorganic compounds',
    },
    '4(c)': {
        'nace': ['20.20'],
        'description': 'Plant protection products and biocides',
    },
    '4(d)': {
        'nace': ['21.10', '21.20'],
        'description': 'Pharmaceutical products',
    },
    '4(e)': {
        'nace': ['20.51', '20.52', '20.53', '20.59'],
        'description': 'Explosives and pyrotechnic products',
    },
    '4(f)': {
        'nace': ['20.59'],
        'description': 'Other chemical products n.e.c.',
    },

    # Chapter 5: Waste and wastewater management
    '5(a)': {
        'nace': ['38.12', '38.22'],
        'description': 'Hazardous waste disposal/recovery >10 t/day',
    },
    '5(b)': {
        'nace': ['38.21'],
        'description': 'Waste incineration >3 t/hr',
    },
    '5(c)': {
        'nace': ['38.21'],
        'description': 'Non-hazardous waste disposal >50 t/day',
    },
    '5(d)': {
        'nace': ['38.21'],
        'description': 'Landfills >10 t/day or 25 000 t capacity',
    },
    '5(e)': {
        'nace': ['38.21'],
        'description': 'Underground disposal of hazardous waste',
    },
    '5(f)': {
        'nace': ['38.21'],
        'description': 'Temporary storage of hazardous waste >50 t',
    },
    '5(g)': {
        'nace': ['36.00'],
        'description': 'Independently operated wastewater treatment',
    },

    # Chapter 6: Paper and wood
    '6(a)': {
        'nace': ['17.11'],
        'description': 'Pulp from timber or similar fibrous materials',
    },
    '6(b)': {
        'nace': ['17.12'],
        'description': 'Paper and cardboard production >20 t/day',
    },
    '6(c)': {
        'nace': ['16.10'],
        'description': 'Wood and wood products preservation with chemicals',
    },

    # Chapter 7: Intensive livestock production
    '7(a)': {
        'nace': ['01.47'],
        'description': 'Intensive rearing of poultry or pigs (general)',
    },
    '7(a)(i)': {
        'nace': ['01.47'],
        'description': 'Intensive poultry rearing >40 000 places',
    },
    '7(a)(ii)': {
        'nace': ['01.46'],
        'description': 'Intensive pig rearing >2 000 production pigs',
    },
    '7(a)(iii)': {
        'nace': ['01.46'],
        'description': 'Intensive pig rearing >750 sows',
    },
    '7(b)': {
        'nace': ['35.11'],
        'description': 'Intensive aquaculture >1 000 t/year',
    },

    # Chapter 8: Animal and vegetable products from food/beverage
    '8(a)': {
        'nace': ['10.11', '10.12', '10.13'],
        'description': 'Slaughterhouses >50 t/day',
    },
    '8(b)': {
        'nace': ['10.31', '10.32', '10.39', '10.41', '10.61', '10.62'],
        'description': 'Food and beverage manufacturing (general)',
    },
    '8(b)(i)': {
        'nace': ['10.11', '10.12', '10.13', '10.20', '10.39', '10.41'],
        'description': 'Food from animal raw materials >75 t/day',
    },
    '8(b)(ii)': {
        'nace': ['10.31', '10.32', '10.39', '10.41', '10.61', '10.62'],
        'description': 'Food from vegetable raw materials >300 t/day',
    },
    '8(c)': {
        'nace': ['10.51'],
        'description': 'Milk processing >200 t/day',
    },

    # Chapter 9: Other activities
    '9(a)': {
        'nace': ['13.30'],
        'description': 'Textile treatment >10 t/day',
    },
    '9(b)': {
        'nace': ['15.11'],
        'description': 'Tanning of hides and skins >12 t/day',
    },
    '9(c)': {
        'nace': ['20.30', '25.61', '29.20', '31.01', '31.02', '31.09'],
        'description': 'Surface treatment using organic solvents >150 kg/hr',
    },
    '9(d)': {
        'nace': ['24.46'],
        'description': 'Carbon or electrographite production',
    },
    '9(e)': {
        'nace': ['20.30', '25.61'],
        'description': 'Other surface treatment using organic solvents',
    },
}

# NACE 2-digit section lookup (for filtering by industry division)
_NACE_SECTIONS = {
    '01': 'A', '10': 'C10', '13': 'C13', '15': 'C15', '16': 'C16',
    '17': 'C17', '19': 'C19', '20': 'C20', '21': 'C21', '23': 'C23',
    '24': 'C24', '25': 'C25', '29': 'C29', '31': 'C31',
    '35': 'D35', '36': 'E36', '38': 'E38',
}


def get_nace_for_eprtr(eprtr_code: str) -> list[str]:
    """Get NACE codes for an E-PRTR Annex I activity code."""
    mapping = EPRTR_TO_NACE.get(str(eprtr_code).strip(), {})
    return mapping.get('nace', [])


def get_eprtr_description(eprtr_code: str) -> str:
    """Get description for an E-PRTR activity code."""
    mapping = EPRTR_TO_NACE.get(str(eprtr_code).strip(), {})
    return mapping.get('description', f'Unknown: {eprtr_code}')


def get_nace_section_for_eprtr(eprtr_code: str) -> list[str]:
    """Get NACE sections (e.g. 'C24', 'C25') for an E-PRTR activity code.

    Returns deduplicated, sorted list.
    """
    nace_codes = get_nace_for_eprtr(eprtr_code)
    sections = set()
    for code in nace_codes:
        div = code.split('.')[0]
        section = _NACE_SECTIONS.get(div, f'?{div}')
        sections.add(section)
    return sorted(sections)


def get_eprtr_codes_for_nace_section(*sections: str) -> list[str]:
    """Get all E-PRTR codes that map to given NACE sections (e.g. 'C24', 'C25').

    >>> get_eprtr_codes_for_nace_section('C24', 'C25')
    ['2(a)', '2(b)', '2(c)', '2(c)(i)', ...]
    """
    target = set(sections)
    result = []
    for eprtr_code in EPRTR_TO_NACE:
        code_sections = set(get_nace_section_for_eprtr(eprtr_code))
        if code_sections & target:
            result.append(eprtr_code)
    return result
