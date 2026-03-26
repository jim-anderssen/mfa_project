"""
Custom tools for waste data extraction.

These functions can be used as tools by the Claude Agent SDK.
"""

from typing import Dict, Any, Optional, Tuple

from src.nuts2.data_loader import COUNTRY_MAP
from src.nuts2.geo_analysis import NUTS2_CENTROIDS
from src.mappings.ewc_stat import EWC_STAT_CODES, get_ewc_description
from src.mappings.company_terms import map_company_term, COMPANY_TERM_MAPPING
from src.mappings.translations import translate_waste_term, detect_language


# Reverse lookup for country codes
COUNTRY_CODE_TO_NAME = {v: k for k, v in COUNTRY_MAP.items()}

# City to NUTS2 mapping for major industrial cities
CITY_TO_NUTS2 = {
    # Germany
    'berlin': 'DE30',
    'hamburg': 'DE60',
    'munich': 'DE21',
    'münchen': 'DE21',
    'cologne': 'DEA2',
    'köln': 'DEA2',
    'frankfurt': 'DE71',
    'düsseldorf': 'DEA1',
    'dortmund': 'DEA5',
    'essen': 'DEA1',
    'duisburg': 'DEA1',
    'stuttgart': 'DE11',
    'nuremberg': 'DE25',
    'nürnberg': 'DE25',

    # Sweden
    'stockholm': 'SE11',
    'gothenburg': 'SE23',
    'göteborg': 'SE23',
    'malmö': 'SE22',
    'malmo': 'SE22',
    'luleå': 'SE33',
    'lulea': 'SE33',

    # Poland
    'warsaw': 'PL91',
    'warszawa': 'PL91',
    'krakow': 'PL21',
    'kraków': 'PL21',
    'gdansk': 'PL63',
    'gdańsk': 'PL63',
    'katowice': 'PL22',
    'wroclaw': 'PL51',
    'wrocław': 'PL51',

    # France
    'paris': 'FR10',
    'lyon': 'FRK2',
    'marseille': 'FRL0',
    'toulouse': 'FRJ2',
    'lille': 'FRE1',
    'bordeaux': 'FRI1',
    'strasbourg': 'FRF1',
    'nantes': 'FRG0',

    # Spain
    'madrid': 'ES30',
    'barcelona': 'ES51',
    'valencia': 'ES52',
    'sevilla': 'ES61',
    'bilbao': 'ES21',

    # Italy
    'rome': 'ITI4',
    'roma': 'ITI4',
    'milan': 'ITC4',
    'milano': 'ITC4',
    'naples': 'ITF3',
    'napoli': 'ITF3',
    'turin': 'ITC1',
    'torino': 'ITC1',

    # Netherlands
    'amsterdam': 'NL32',
    'rotterdam': 'NL33',
    'the hague': 'NL33',
    'den haag': 'NL33',
    'eindhoven': 'NL41',

    # Belgium
    'brussels': 'BE10',
    'bruxelles': 'BE10',
    'antwerp': 'BE21',
    'antwerpen': 'BE21',
    'ghent': 'BE23',
    'gent': 'BE23',

    # Austria
    'vienna': 'AT13',
    'wien': 'AT13',
    'graz': 'AT22',
    'linz': 'AT31',

    # Czechia
    'prague': 'CZ01',
    'praha': 'CZ01',
    'brno': 'CZ06',
    'ostrava': 'CZ08',

    # Finland
    'helsinki': 'FI1B',
    'tampere': 'FI19',
    'oulu': 'FI1D',

    # Denmark
    'copenhagen': 'DK01',
    'københavn': 'DK01',
    'aarhus': 'DK04',
    'odense': 'DK03',

    # Norway
    'oslo': 'NO01',
    'bergen': 'NO05',
    'trondheim': 'NO06',

    # Hungary
    'budapest': 'HU11',

    # Romania
    'bucharest': 'RO32',
    'bucuresti': 'RO32',
    'cluj': 'RO11',

    # Portugal
    'lisbon': 'PT17',
    'lisboa': 'PT17',
    'porto': 'PT11',
}


def map_waste_to_ewc_stat(
    company_waste_term: str,
    context: str = '',
    nace_code: str = None
) -> Dict[str, Any]:
    """
    Map company-reported waste category to EWC-Stat code.

    Parameters
    ----------
    company_waste_term : str
        Waste term from company report
    context : str
        Additional context from report
    nace_code : str, optional
        NACE sector code for context-aware mapping

    Returns
    -------
    dict
        Mapping result with ewc_code, description, and confidence
    """
    # First, try to detect language and translate if needed
    lang = detect_language(company_waste_term)
    if lang:
        translated = translate_waste_term(company_waste_term, lang)
    else:
        translated = company_waste_term

    # Map to EWC-Stat
    ewc_code, confidence = map_company_term(translated, context)

    if ewc_code:
        return {
            'success': True,
            'ewc_stat_code': ewc_code,
            'ewc_stat_description': get_ewc_description(ewc_code),
            'original_term': company_waste_term,
            'translated_term': translated if lang else None,
            'detected_language': lang,
            'confidence': confidence,
            'requires_llm_classification': False
        }
    else:
        return {
            'success': False,
            'ewc_stat_code': None,
            'ewc_stat_description': None,
            'original_term': company_waste_term,
            'translated_term': translated if lang else None,
            'detected_language': lang,
            'confidence': 0.0,
            'requires_llm_classification': True,
            'suggestion': f"No mapping found for '{company_waste_term}'. LLM should classify based on context."
        }


def validate_extraction(extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate an extracted waste data record.

    Parameters
    ----------
    extracted_data : dict
        Extracted waste record with fields like waste_tonnes, waste, year, etc.

    Returns
    -------
    dict
        Validation result with is_valid, issues, warnings, and adjusted confidence
    """
    issues = []
    warnings = []
    confidence = extracted_data.get('confidence_score', 0.5)

    # Required fields
    required_fields = ['waste_tonnes', 'waste', 'year', 'source_company']
    for field in required_fields:
        if field not in extracted_data or extracted_data[field] is None:
            issues.append(f"Missing required field: {field}")

    # Waste amount validation
    if 'waste_tonnes' in extracted_data and extracted_data['waste_tonnes'] is not None:
        tonnes = extracted_data['waste_tonnes']
        if tonnes < 0:
            issues.append("Negative waste amount")
        elif tonnes == 0:
            warnings.append("Zero waste amount - verify if intentional")
        elif tonnes > 100_000_000:  # 100 million tonnes
            warnings.append("Unusually high waste amount (>100M tonnes) - verify")
        elif tonnes > 10_000_000:  # 10 million tonnes
            warnings.append("High waste amount (>10M tonnes) - verify for major facility")

    # EWC-Stat code validation
    if 'waste' in extracted_data and extracted_data['waste']:
        waste_code = extracted_data['waste']
        if waste_code not in EWC_STAT_CODES:
            warnings.append(f"Unknown EWC-Stat code: {waste_code}")
            confidence -= 0.1

    # Year validation
    if 'year' in extracted_data and extracted_data['year']:
        year = extracted_data['year']
        if year < 2010:
            warnings.append(f"Old data year ({year}) - may be outdated")
        elif year > 2025:
            issues.append(f"Future year ({year}) - invalid")

    # Country validation
    if 'country' in extracted_data and extracted_data['country']:
        country = extracted_data['country']
        if country not in COUNTRY_MAP and country not in COUNTRY_CODE_TO_NAME:
            warnings.append(f"Unknown country: {country}")

    # Calculate final confidence
    final_confidence = max(0, min(1, confidence - 0.1 * len(warnings) - 0.3 * len(issues)))

    return {
        'is_valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'original_confidence': extracted_data.get('confidence_score', 0.5),
        'adjusted_confidence': final_confidence,
        'confidence_adjustment': final_confidence - extracted_data.get('confidence_score', 0.5)
    }


def normalize_country(country_name: str) -> Dict[str, Any]:
    """
    Normalize country name to ISO code.

    Parameters
    ----------
    country_name : str
        Country name from report

    Returns
    -------
    dict
        Normalized country with code
    """
    # Direct lookup
    if country_name in COUNTRY_MAP:
        return {
            'success': True,
            'country': country_name,
            'country_code': COUNTRY_MAP[country_name]
        }

    # Check if it's already a code
    if country_name.upper() in COUNTRY_CODE_TO_NAME:
        return {
            'success': True,
            'country': COUNTRY_CODE_TO_NAME[country_name.upper()],
            'country_code': country_name.upper()
        }

    # Case-insensitive search
    for country, code in COUNTRY_MAP.items():
        if country.lower() == country_name.lower():
            return {
                'success': True,
                'country': country,
                'country_code': code
            }

    # Common variations
    variations = {
        'czech republic': 'Czechia',
        'turkiye': 'Türkiye',
        'turkey': 'Türkiye',
        'uk': 'United Kingdom',
        'great britain': 'United Kingdom',
        'holland': 'Netherlands',
        'the netherlands': 'Netherlands',
        'hellas': 'Greece',
    }

    lower_name = country_name.lower()
    if lower_name in variations:
        standard_name = variations[lower_name]
        return {
            'success': True,
            'country': standard_name,
            'country_code': COUNTRY_MAP.get(standard_name)
        }

    return {
        'success': False,
        'country': country_name,
        'country_code': None,
        'suggestion': f"Unknown country: {country_name}. Please verify spelling."
    }


def lookup_nuts2_region(
    location: str,
    country_code: str = None
) -> Dict[str, Any]:
    """
    Look up NUTS2 region from a location name.

    Parameters
    ----------
    location : str
        City, region, or address
    country_code : str, optional
        ISO 2-letter country code to narrow search

    Returns
    -------
    dict
        NUTS2 region information
    """
    location_lower = location.lower().strip()

    # Direct city lookup
    if location_lower in CITY_TO_NUTS2:
        nuts2_code = CITY_TO_NUTS2[location_lower]
        return {
            'success': True,
            'nuts2_region': nuts2_code,
            'nuts2_name': get_nuts2_name(nuts2_code),
            'country_code': nuts2_code[:2],
            'match_type': 'city_exact'
        }

    # Partial city match
    for city, nuts2_code in CITY_TO_NUTS2.items():
        if city in location_lower or location_lower in city:
            # If country_code provided, verify match
            if country_code and not nuts2_code.startswith(country_code):
                continue
            return {
                'success': True,
                'nuts2_region': nuts2_code,
                'nuts2_name': get_nuts2_name(nuts2_code),
                'country_code': nuts2_code[:2],
                'match_type': 'city_partial'
            }

    # If country_code provided but no city match, return country-level info
    if country_code:
        # Find any NUTS2 region for this country
        country_regions = [code for code in NUTS2_CENTROIDS.keys()
                          if code.startswith(country_code)]
        if country_regions:
            return {
                'success': False,
                'nuts2_region': None,
                'country_code': country_code,
                'available_regions': country_regions[:10],
                'suggestion': f"Could not map '{location}' to NUTS2. Country has {len(country_regions)} NUTS2 regions."
            }

    return {
        'success': False,
        'nuts2_region': None,
        'country_code': country_code,
        'suggestion': f"Could not map '{location}' to NUTS2 region. Try providing city name or more specific location."
    }


def get_nuts2_name(nuts2_code: str) -> Optional[str]:
    """Get name for a NUTS2 region code."""
    # This is a simplified version - in production, would load from Eurostat
    # For now, return code as placeholder
    return nuts2_code


def convert_waste_units(
    value: float,
    from_unit: str,
    to_unit: str = 'tonnes'
) -> Tuple[float, str]:
    """
    Convert waste amounts between units.

    Parameters
    ----------
    value : float
        Numeric value to convert
    from_unit : str
        Source unit (kg, t, tonnes, mt, kt, etc.)
    to_unit : str
        Target unit (default: tonnes)

    Returns
    -------
    tuple
        (converted_value, unit)
    """
    from_unit_lower = from_unit.lower().strip()

    # Conversion factors to tonnes
    to_tonnes = {
        'kg': 0.001,
        'kilogram': 0.001,
        'kilograms': 0.001,
        't': 1.0,
        'tonne': 1.0,
        'tonnes': 1.0,
        'ton': 1.0,
        'tons': 1.0,
        'metric ton': 1.0,
        'metric tonnes': 1.0,
        'mt': 1.0,  # metric ton
        'kt': 1000.0,  # kiloton
        'kiloton': 1000.0,
        'kilotonnes': 1000.0,
        'thousand tonnes': 1000.0,
        '000 tonnes': 1000.0,
        'million tonnes': 1_000_000.0,
        'mt (million)': 1_000_000.0,
    }

    if from_unit_lower in to_tonnes:
        tonnes_value = value * to_tonnes[from_unit_lower]
        return tonnes_value, 'tonnes'

    # Unknown unit - return as-is with warning
    return value, from_unit
