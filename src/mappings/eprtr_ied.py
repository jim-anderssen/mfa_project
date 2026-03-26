"""EPRTR Annex I to IED Annex I activity code mapping.

Derived from F6_1_IED_Installations.csv which contains both taxonomies.
Uses most common mapping for each EPRTR code.
"""
import pandas as pd

EPRTR_TO_IED = {
    # Chapter 1: Energy industries
    '1(a)': '1.2',       # Mineral oil/gas refining (1934 facilities)
    '1(b)': '1.4(b)',    # Coal gasification (52)
    '1(c)': '1.1',       # Combustion >50 MW (18224)
    '1(d)': '1.3',       # Coke ovens (144)
    '1(e)': '2.2',       # (24) - often co-located
    '1(f)': '1.1',       # (55)

    # Chapter 2: Metals
    '2(a)': '2.1',       # Metal ore roasting/sintering (105)
    '2(b)': '2.2',       # Pig iron/steel production (1706)
    '2(c)': '2.3(c)',    # Hot-rolling, forges (745)
    '2(c)(i)': '2.3(a)', # Hot-rolling >20t/hr (632)
    '2(c)(ii)': '2.3(b)', # Smitheries (57)
    '2(c)(iii)': '2.3(c)', # Protective coatings (2116)
    '2(d)': '2.4',       # Ferrous metal foundries (4153)
    '2(e)': '2.5(b)',    # Non-ferrous production (2306)
    '2(e)(i)': '2.5(a)', # Non-ferrous from ore (1006)
    '2(e)(ii)': '2.5(b)', # Non-ferrous melting (4689)
    '2(f)': '2.6',       # Surface treatment (20799)

    # Chapter 3: Minerals
    '3(a)': '3.1(a)',    # Cement clinker - NOTE: data shows 1.1 but 3.1(a) is correct
    '3(b)': '3.1(a)',    # Cement (480)
    '3(c)': '3.1(a)',    # Cement (580)
    '3(c)(i)': '3.1(a)', # Cement clinker (1113)
    '3(c)(ii)': '3.1(b)', # Lime (237)
    '3(c)(iii)': '3.1(b)', # MgO production (726)
    '3(d)': '3.2',       # Asbestos (8) - use correct IED, not 2.5(b)
    '3(e)': '3.3',       # Glass (2833)
    '3(f)': '3.4',       # Mineral fibres (475)
    '3(g)': '3.5',       # Ceramics (9331)

    # Chapter 4: Chemicals
    '4(a)': '4.1(a)',    # Organic chemicals (1325)
    '4(a)(i)': '4.1(a)', # Basic organic chemicals (1102)
    '4(a)(ii)': '4.1(b)', # Simple hydrocarbons (4533)
    '4(a)(iii)': '4.1(c)', # Oxygen-containing (95)
    '4(a)(iv)': '4.1(d)', # Sulphur-containing (543)
    '4(a)(ix)': '4.1(i)', # Phosphorus-containing (219)
    '4(a)(v)': '4.1(e)', # Nitrogen-containing (46)
    '4(a)(vi)': '4.1(f)', # Halogen-containing (191)
    '4(a)(vii)': '4.1(g)', # Organometallic (423)
    '4(a)(viii)': '4.1(h)', # Plastics (5501)
    '4(a)(x)': '4.1(j)', # Surface-active agents (546)
    '4(a)(xi)': '4.1(k)', # Other organic chemicals (607)
    '4(b)': '4.2(a)',    # Inorganic chemicals (422)
    '4(b)(i)': '4.2(a)', # Gases (886)
    '4(b)(ii)': '4.2(b)', # Acids (348)
    '4(b)(iii)': '4.2(c)', # Bases (73)
    '4(b)(iv)': '4.2(d)', # Salts (1441)
    '4(b)(v)': '4.2(e)', # Non-metals (1538)
    '4(c)': '4.3',       # Biocides (1089)
    '4(d)': '4.4',       # Pharmaceuticals (732)
    '4(e)': '4.5',       # Explosives (4317)
    '4(f)': '4.6',       # Other chemical products (393)

    # Chapter 5: Waste management
    '5(a)': '5.1',       # Hazardous waste disposal - use 5.1 (IED_TO_NACE has 5.1)
    '5(b)': '5.2',       # Waste incineration - map to 5.2 (IED_TO_NACE has 5.2)
    '5(c)': '5.3(a)',    # Non-hazardous disposal (use 5.3(a))
    '5(d)': '5.4',       # Landfills (19761)
    '5(e)': '5.5',       # Underground storage (but data shows 6.5??)
    '5(f)': '5.6',       # Temporary storage (use 5.6)
    '5(g)': '6.11',      # Wastewater treatment (429)

    # Chapter 6: Paper/textiles
    '6(a)': '6.1(a)',    # Pulp (812)
    '6(b)': '6.1(b)',    # Paper/cardboard (4635)
    '6(c)': '6.10',      # Wood preservation (889)

    # Chapter 7: Intensive agriculture
    '7(a)': '6.6(a)',    # Intensive rearing - generic (13893)
    '7(a)(i)': '6.6(a)', # Poultry (58986)
    '7(a)(ii)': '6.6(b)', # Pigs >2000 (58299)
    '7(a)(iii)': '6.6(c)', # Sows >750 (17648)
    '7(b)': '1.1',       # (256) - combustion co-located

    # Chapter 8: Food/drink
    '8(a)': '6.4(a)',    # Slaughterhouses (5843)
    '8(b)': '6.4(b)(ii)', # Food processing (2253)
    '8(b)(i)': '6.4(b)(i)', # Food from animal (2208)
    '8(b)(ii)': '6.4(b)(ii)', # Food from vegetable (8182)
    '8(c)': '6.4(c)',    # Milk processing (4005)

    # Chapter 9: Other
    '9(a)': '6.2',       # Textile treatment (1916)
    '9(b)': '6.3',       # Tanning (194)
    '9(c)': '6.7',       # Surface treatment with solvents (8040)
    '9(d)': '6.8',       # Carbon/graphite (278)
    '9(e)': '6.7',       # (83)
}


def eprtr_to_ied(eprtr_code: str) -> str:
    """Convert EPRTR Annex I code to IED Annex I code."""
    if pd.isna(eprtr_code):
        return None
    code = str(eprtr_code).strip()
    return EPRTR_TO_IED.get(code)
