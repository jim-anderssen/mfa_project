"""
Configuration for the waste extraction agent.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from src.io_file import PROCESSED_DIR, RAW_DIR
from src.nuts2.data_loader import COUNTRY_MAP


@dataclass
class ExtractionConfig:
    """Configuration for waste extraction agent."""

    # Target parameters
    target_countries: List[str] = field(
        default_factory=lambda: list(COUNTRY_MAP.keys())
    )
    target_nace_codes: List[str] = field(
        default_factory=lambda: ['C24', 'C25', 'C20', 'C10-C12']
    )
    target_years: List[int] = field(
        default_factory=lambda: [2022, 2023, 2024]
    )

    # Search parameters
    max_companies_per_sector: int = 20
    max_reports_per_company: int = 3
    search_languages: List[str] = field(
        default_factory=lambda: ['en', 'de', 'fr', 'se', 'es', 'it', 'pl']
    )

    # Output parameters
    output_dir: Path = field(default_factory=lambda: PROCESSED_DIR / 'extracted')
    pdf_cache_dir: Path = field(default_factory=lambda: RAW_DIR / 'company_reports')

    # Quality thresholds
    min_confidence: float = 0.6
    validate_against_reference: bool = True

    # API settings
    model: str = 'claude-sonnet-4-5-20250514'
    max_tokens: int = 4096
    web_search_max_uses: int = 10

    def __post_init__(self):
        """Ensure directories exist."""
        self.output_dir = Path(self.output_dir)
        self.pdf_cache_dir = Path(self.pdf_cache_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pdf_cache_dir.mkdir(parents=True, exist_ok=True)


# NACE activity descriptions
NACE_ACTIVITIES = {
    'B': 'Mining and quarrying',
    'C': 'Manufacturing',
    'C10': 'Manufacture of food products',
    'C10-C12': 'Manufacture of food products, beverages and tobacco',
    'C11': 'Manufacture of beverages',
    'C12': 'Manufacture of tobacco products',
    'C13-C15': 'Manufacture of textiles, wearing apparel and leather',
    'C16': 'Manufacture of wood and products of wood',
    'C17': 'Manufacture of paper and paper products',
    'C18': 'Printing and reproduction of recorded media',
    'C19': 'Manufacture of coke and refined petroleum products',
    'C20': 'Manufacture of chemicals and chemical products',
    'C21': 'Manufacture of basic pharmaceutical products',
    'C22': 'Manufacture of rubber and plastic products',
    'C23': 'Manufacture of other non-metallic mineral products',
    'C24': 'Manufacture of basic metals',
    'C24_C25': 'Manufacture of basic metals and fabricated metal products',
    'C25': 'Manufacture of fabricated metal products',
    'C26': 'Manufacture of computer, electronic and optical products',
    'C27': 'Manufacture of electrical equipment',
    'C28': 'Manufacture of machinery and equipment',
    'C29': 'Manufacture of motor vehicles, trailers and semi-trailers',
    'C30': 'Manufacture of other transport equipment',
    'C31-C32': 'Manufacture of furniture; other manufacturing',
    'C33': 'Repair and installation of machinery and equipment',
    'D': 'Electricity, gas, steam and air conditioning supply',
    'E': 'Water supply; sewerage, waste management',
    'F': 'Construction',
}


def get_nace_description(code: str) -> str:
    """Get description for a NACE code."""
    return NACE_ACTIVITIES.get(code, f'NACE {code}')
