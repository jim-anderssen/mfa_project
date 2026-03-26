"""
Data loading utilities.

Modules:
- io: File I/O operations
- eurostat: Eurostat API data loading
- nuts2: NUTS2 regional data loading
- retriever: Swedish company data loading
"""

from .io import (
    load_csv,
    load_excel,
    save_csv,
    PROJECT_ROOT,
    DATA_DIR,
    RAW_DIR,
    INTERIM_DIR,
    PROCESSED_DIR,
)
from .eurostat import load_dataset, extend_eurostat_dataset
from .nuts2 import (
    ProxyType,
    load_waste_generation,
    load_sbs_employment,
    load_sbs_nuts2021,
    load_sbs_proxy,
    load_nuts2_names,
    load_recycling_potential,
    get_sbs_nuts2_employment,
    compute_sbs_proxy,
)
from .retriever import load_swedish_companies, parse_sni_to_nace

__all__ = [
    # io
    "load_csv",
    "load_excel",
    "save_csv",
    "PROJECT_ROOT",
    "DATA_DIR",
    "RAW_DIR",
    "INTERIM_DIR",
    "PROCESSED_DIR",
    # eurostat
    "load_dataset",
    # nuts2
    "ProxyType",
    "load_waste_generation",
    "load_sbs_employment",
    "load_sbs_nuts2021",
    "load_sbs_proxy",
    "load_nuts2_names",
    "load_recycling_potential",
    "get_sbs_nuts2_employment",
    "compute_sbs_proxy",
    # retriever
    "load_swedish_companies",
    "parse_sni_to_nace",
]
