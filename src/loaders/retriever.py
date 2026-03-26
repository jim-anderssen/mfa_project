"""
Swedish company data loader for Retriever export files.

Loads company data from Retriever Excel exports and parses SNI codes to NACE format.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, List


def parse_sni_to_nace(sni_code: str) -> str:
    """
    Convert 5-digit SNI code to NACE format.

    Examples:
        '24101' -> 'C24.10'
        '25120' -> 'C25.12'
        '10110' -> 'C10.11'

    Parameters
    ----------
    sni_code : str
        5-digit Swedish SNI code (same as NACE but without dots)

    Returns
    -------
    str
        NACE formatted code with section letter and dot separator
    """
    code = str(sni_code).strip()
    if len(code) < 4:
        return f'C{code}'

    # First 2 digits = division, next 2 = group
    division = code[:2]
    group = code[2:4]

    # Determine section letter based on division
    div_num = int(division)
    if 10 <= div_num <= 33:
        section = 'C'  # Manufacturing
    elif 35 <= div_num <= 35:
        section = 'D'  # Electricity, gas
    elif 36 <= div_num <= 39:
        section = 'E'  # Water, waste
    elif 41 <= div_num <= 43:
        section = 'F'  # Construction
    elif 1 <= div_num <= 3:
        section = 'A'  # Agriculture
    elif 5 <= div_num <= 9:
        section = 'B'  # Mining
    else:
        section = ''

    return f'{section}{division}.{group}'


def load_swedish_companies(
    file_path: Path,
    year: str = '2022',
    filter_nace: Optional[List[str]] = None,
    primary_nace_only: bool = True
) -> pd.DataFrame:
    """
    Load Retriever Excel export, extract key columns.

    Uses EBITDA as proxy for Gross Value Added.

    Parameters
    ----------
    file_path : Path
        Path to Retriever export Excel file
    year : str
        Year for financial data (default: '2022')
    filter_nace : list of str, optional
        NACE divisions to filter by (e.g., ['24', '25'] for metals)
    primary_nace_only : bool
        If True, filter by primary NACE code only (default: True)

    Returns
    -------
    pd.DataFrame
        Columns: company_id, company_name, nace_codes, ebitda, country_code
    """
    # Read Excel file
    df = pd.read_excel(file_path)

    # Use EBITDA as GVA proxy
    ebitda_col = f'Rörelseresultat före avskrivningar, EBITDA (tkr) {year}'
    ebitda = pd.to_numeric(df[ebitda_col], errors='coerce').fillna(0)

    result = pd.DataFrame({
        'company_id': df['Org. nr'].astype(str),
        'company_name': df['Företagsnamn'],
        'sni_codes': df['SNI kodlista all'],
        'ebitda': ebitda,
        'country_code': 'SE'
    })

    # Parse SNI codes to NACE
    def parse_sni_list(sni_str):
        """Parse pipe-separated SNI codes to NACE list."""
        if pd.isna(sni_str):
            return []
        codes = str(sni_str).split(' | ')
        return [parse_sni_to_nace(c.strip()) for c in codes if c.strip()]

    result['nace_codes'] = result['sni_codes'].apply(parse_sni_list)

    # Extract primary NACE (first code)
    result['nace_primary'] = result['nace_codes'].apply(
        lambda x: x[0] if x else None
    )

    # Extract 2-digit NACE (division)
    result['nace_2digit'] = result['nace_primary'].apply(
        lambda x: x[1:3] if x and len(x) >= 3 else None
    )

    # Filter by NACE divisions if specified
    if filter_nace:
        if primary_nace_only:
            # Only match on primary NACE code
            result = result[result['nace_2digit'].isin(filter_nace)].copy()
        else:
            # Match on any NACE code
            def matches_filter(nace_list):
                for nace in nace_list:
                    if any(nace[1:3] == div for div in filter_nace):
                        return True
                return False
            result = result[result['nace_codes'].apply(matches_filter)].copy()

    # Convert from tkr to kr (multiply by 1000)
    result['ebitda'] = result['ebitda'] * 1000

    # Remove companies with missing or zero EBITDA
    result = result[result['ebitda'] > 0].copy()

    return result.reset_index(drop=True)


def get_swedish_company_summary(
    file_path: Path,
    nace_divisions: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Generate summary statistics for Swedish companies by NACE division.

    Parameters
    ----------
    file_path : Path
        Path to Retriever export Excel file
    nace_divisions : list of str, optional
        NACE divisions to include (e.g., ['24', '25'])

    Returns
    -------
    pd.DataFrame
        Summary by NACE division with company count and total GVA
    """
    companies = load_swedish_companies(file_path, filter_nace=nace_divisions)

    # Explode NACE codes for multi-industry companies
    exploded = companies.explode('nace_codes')
    exploded['division'] = exploded['nace_codes'].apply(
        lambda x: x[1:3] if x and len(x) >= 3 else None
    )

    summary = exploded.groupby('division').agg({
        'company_id': 'nunique',
        'ebitda': 'sum'
    }).reset_index()

    summary.columns = ['nace_division', 'n_companies', 'total_ebitda']
    return summary.sort_values('total_ebitda', ascending=False)
