"""
Multi-language support for waste terminology.

Translations from common European languages to English waste terms.
"""

from typing import Optional

# German waste terms
DE_TRANSLATIONS = {
    # Metals
    'metalabfälle': 'metal waste',
    'metallabfälle': 'metal waste',
    'schrott': 'scrap',
    'eisenschrott': 'ferrous scrap',
    'stahlschrott': 'steel scrap',
    'alteisen': 'scrap iron',
    'aluminiumschrott': 'aluminum scrap',
    'kupferschrott': 'copper scrap',
    'buntmetall': 'non-ferrous metal',
    'ne-metall': 'non-ferrous metal',

    # Industrial residues
    'schlacke': 'slag',
    'hochofenschlacke': 'blast furnace slag',
    'stahlwerksschlacke': 'steel slag',
    'flugasche': 'fly ash',
    'kesselasche': 'boiler ash',
    'gießereisand': 'foundry sand',
    'formsand': 'foundry sand',
    'zunder': 'mill scale',

    # Paper/cardboard
    'papierabfälle': 'paper waste',
    'altpapier': 'waste paper',
    'pappe': 'cardboard',
    'kartonage': 'cardboard packaging',

    # Plastics
    'kunststoffabfälle': 'plastic waste',
    'plastikabfälle': 'plastic waste',
    'folienabfälle': 'plastic film waste',

    # Wood
    'holzabfälle': 'wood waste',
    'altholz': 'waste wood',
    'sägemehl': 'sawdust',
    'späne': 'shavings',
    'holzspäne': 'wood shavings',

    # Hazardous
    'gefährliche abfälle': 'hazardous waste',
    'sonderabfälle': 'special waste',
    'chemische abfälle': 'chemical waste',
    'altöl': 'used oil',
    'lösungsmittel': 'solvent',

    # Other
    'glasabfälle': 'glass waste',
    'textilabfälle': 'textile waste',
    'gummiabfälle': 'rubber waste',
    'reifenabfälle': 'tire waste',
    'elektroschrott': 'electronic waste',
    'elektronikschrott': 'electronic waste',
    'bauschutt': 'construction waste',
    'abbruchmaterial': 'demolition waste',
    'klärschlamm': 'sewage sludge',
    'bioabfall': 'organic waste',
    'restmüll': 'residual waste',
    'mischabfall': 'mixed waste',
}

# French waste terms
FR_TRANSLATIONS = {
    # Metals
    'déchets métalliques': 'metal waste',
    'ferraille': 'scrap',
    'ferraille d\'acier': 'steel scrap',
    'ferraille de fer': 'iron scrap',
    'aluminium usagé': 'aluminum scrap',
    'cuivre usagé': 'copper scrap',
    'métaux non ferreux': 'non-ferrous metals',

    # Industrial residues
    'scories': 'slag',
    'laitier': 'slag',
    'cendres volantes': 'fly ash',
    'cendres de fond': 'bottom ash',
    'sable de fonderie': 'foundry sand',
    'calamine': 'mill scale',

    # Paper/cardboard
    'déchets de papier': 'paper waste',
    'vieux papiers': 'waste paper',
    'carton': 'cardboard',
    'emballages papier': 'paper packaging',

    # Plastics
    'déchets plastiques': 'plastic waste',
    'plastique usagé': 'waste plastic',
    'emballages plastiques': 'plastic packaging',

    # Wood
    'déchets de bois': 'wood waste',
    'bois usagé': 'waste wood',
    'sciure': 'sawdust',
    'copeaux de bois': 'wood shavings',

    # Hazardous
    'déchets dangereux': 'hazardous waste',
    'déchets chimiques': 'chemical waste',
    'huiles usagées': 'used oil',
    'solvants usés': 'spent solvent',

    # Other
    'déchets de verre': 'glass waste',
    'déchets textiles': 'textile waste',
    'déchets de caoutchouc': 'rubber waste',
    'pneus usagés': 'used tires',
    'déchets électroniques': 'electronic waste',
    'deee': 'weee',
    'déchets de construction': 'construction waste',
    'gravats': 'rubble',
    'boues': 'sludge',
    'biodéchets': 'organic waste',
    'déchets résiduels': 'residual waste',
}

# Swedish waste terms
SE_TRANSLATIONS = {
    # Metals
    'metallavfall': 'metal waste',
    'skrot': 'scrap',
    'järnskrot': 'iron scrap',
    'stålskrot': 'steel scrap',
    'aluminiumskrot': 'aluminum scrap',
    'kopparskrot': 'copper scrap',
    'icke-järnmetaller': 'non-ferrous metals',

    # Industrial residues
    'slagg': 'slag',
    'masugnslagg': 'blast furnace slag',
    'stålslagg': 'steel slag',
    'flygaska': 'fly ash',
    'bottenaska': 'bottom ash',
    'gjuterisand': 'foundry sand',
    'glödskal': 'mill scale',

    # Paper/cardboard
    'pappersavfall': 'paper waste',
    'returpapper': 'waste paper',
    'kartong': 'cardboard',
    'wellpapp': 'corrugated cardboard',

    # Plastics
    'plastavfall': 'plastic waste',
    'plastförpackningar': 'plastic packaging',

    # Wood
    'träavfall': 'wood waste',
    'returträ': 'waste wood',
    'sågspån': 'sawdust',
    'träflis': 'wood chips',

    # Hazardous
    'farligt avfall': 'hazardous waste',
    'kemiskt avfall': 'chemical waste',
    'spillolja': 'used oil',
    'lösningsmedel': 'solvent',

    # Other
    'glasavfall': 'glass waste',
    'textilavfall': 'textile waste',
    'gummiavfall': 'rubber waste',
    'däckavfall': 'tire waste',
    'elavfall': 'electronic waste',
    'elektronikavfall': 'electronic waste',
    'byggavfall': 'construction waste',
    'rivningsavfall': 'demolition waste',
    'slam': 'sludge',
    'bioavfall': 'organic waste',
    'restavfall': 'residual waste',
    'brännbart avfall': 'combustible waste',
}

# Spanish waste terms
ES_TRANSLATIONS = {
    'residuos metálicos': 'metal waste',
    'chatarra': 'scrap',
    'chatarra de acero': 'steel scrap',
    'chatarra de hierro': 'iron scrap',
    'aluminio usado': 'aluminum scrap',
    'escoria': 'slag',
    'cenizas volantes': 'fly ash',
    'residuos de papel': 'paper waste',
    'residuos plásticos': 'plastic waste',
    'residuos de madera': 'wood waste',
    'residuos peligrosos': 'hazardous waste',
    'aceites usados': 'used oil',
    'residuos de vidrio': 'glass waste',
    'residuos textiles': 'textile waste',
    'raee': 'weee',
    'residuos de construcción': 'construction waste',
    'lodos': 'sludge',
    'biorresiduos': 'organic waste',
}

# Italian waste terms
IT_TRANSLATIONS = {
    'rifiuti metallici': 'metal waste',
    'rottami': 'scrap',
    'rottami ferrosi': 'ferrous scrap',
    'rottami di acciaio': 'steel scrap',
    'scorie': 'slag',
    'ceneri volanti': 'fly ash',
    'rifiuti di carta': 'paper waste',
    'rifiuti plastici': 'plastic waste',
    'rifiuti di legno': 'wood waste',
    'rifiuti pericolosi': 'hazardous waste',
    'oli usati': 'used oil',
    'rifiuti di vetro': 'glass waste',
    'rifiuti tessili': 'textile waste',
    'raee': 'weee',
    'rifiuti da costruzione': 'construction waste',
    'fanghi': 'sludge',
    'rifiuti organici': 'organic waste',
}

# Polish waste terms
PL_TRANSLATIONS = {
    'odpady metalowe': 'metal waste',
    'złom': 'scrap',
    'złom stalowy': 'steel scrap',
    'złom żelazny': 'iron scrap',
    'żużel': 'slag',
    'popiół lotny': 'fly ash',
    'odpady papierowe': 'paper waste',
    'makulatura': 'waste paper',
    'odpady z tworzyw sztucznych': 'plastic waste',
    'odpady drewniane': 'wood waste',
    'odpady niebezpieczne': 'hazardous waste',
    'oleje odpadowe': 'used oil',
    'odpady szklane': 'glass waste',
    'odpady tekstylne': 'textile waste',
    'zużyty sprzęt elektryczny': 'electronic waste',
    'odpady budowlane': 'construction waste',
    'osady': 'sludge',
    'bioodpady': 'organic waste',
}

# Combined translations dictionary
TRANSLATIONS = {
    'de': DE_TRANSLATIONS,
    'fr': FR_TRANSLATIONS,
    'se': SE_TRANSLATIONS,
    'sv': SE_TRANSLATIONS,  # Swedish ISO code
    'es': ES_TRANSLATIONS,
    'it': IT_TRANSLATIONS,
    'pl': PL_TRANSLATIONS,
}


def translate_waste_term(term: str, source_lang: Optional[str] = None) -> str:
    """
    Translate a waste term to English.

    Parameters
    ----------
    term : str
        Waste term in foreign language
    source_lang : str, optional
        ISO 2-letter language code (de, fr, se, es, it, pl).
        If None, tries all languages.

    Returns
    -------
    str
        English translation or original term if not found
    """
    term_lower = term.lower().strip()

    if source_lang and source_lang in TRANSLATIONS:
        # Try specific language
        mapping = TRANSLATIONS[source_lang]
        if term_lower in mapping:
            return mapping[term_lower]
        # Try partial match
        for foreign, english in mapping.items():
            if foreign in term_lower or term_lower in foreign:
                return english
    else:
        # Try all languages
        for mapping in TRANSLATIONS.values():
            if term_lower in mapping:
                return mapping[term_lower]
            for foreign, english in mapping.items():
                if foreign in term_lower or term_lower in foreign:
                    return english

    return term  # Return original if no translation found


def detect_language(text: str) -> Optional[str]:
    """
    Simple language detection based on common waste terms.

    Returns ISO 2-letter code or None if unknown.
    """
    text_lower = text.lower()

    # German indicators
    if any(w in text_lower for w in ['abfälle', 'abfall', 'schrott', 'schlacke']):
        return 'de'

    # French indicators
    if any(w in text_lower for w in ['déchets', 'ferraille', 'scories']):
        return 'fr'

    # Swedish indicators
    if any(w in text_lower for w in ['avfall', 'skrot', 'slagg']):
        return 'se'

    # Spanish indicators
    if any(w in text_lower for w in ['residuos', 'chatarra', 'escoria']):
        return 'es'

    # Italian indicators
    if any(w in text_lower for w in ['rifiuti', 'rottami', 'scorie']):
        return 'it'

    # Polish indicators
    if any(w in text_lower for w in ['odpady', 'złom', 'żużel']):
        return 'pl'

    return None
