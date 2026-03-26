"""
GVA-Based Company-Level Waste Allocator.

Allocates nationally-reported waste generation (from Eurostat env_wasgen) to
individual companies using EBITDA as a proxy for Gross Value Added (GVA).

Rationale:
    National waste statistics report total waste by industry sector (NACE code),
    but not at the company level. To estimate company-level waste generation,
    we assume waste production scales with economic activity. EBITDA serves as
    a proxy for GVA since both measure value creation before capital costs.

Core algorithm:
    For each (country, NACE, waste_type, year) combination:
        1. W_national = total national waste from env_wasgen
        2. Find companies in that country with matching NACE code
        3. Calculate EBITDA shares: share_c = Company_EBITDA / Σ Sector_EBITDA
        4. Allocate: W_company = W_national * share_c

Data requirements:
    - wasgen_df: Long-format waste generation data with columns:
        country/geo, nace/nace_r2, waste, year, tonnes
    - companies_df: Company registry with columns:
        company_id, company_name, nace_2digit, ebitda, country_code

Key features:
    - HAZ_NHAZ filtering: Uses total waste (HAZ_NHAZ) to avoid double-counting
      hazardous (HAZ) and non-hazardous (NHAZ) separately
    - NACE deduplication: Removes parent NACE codes when children exist
      (e.g., removes C24_C25 if C24 and C25 are both present)
    - Country name normalization: Converts full names to ISO codes

Example usage:
    >>> from src.allocation.gva_based_allocator import load_gva_allocator
    >>> allocator = load_gva_allocator('companies.xlsx', 'SE', ['24', '25'])
    >>> result = allocator.allocate_waste(wasgen_df, countries=['SE'])
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import warnings

from .emissions_based_allocator import NACE_HIERARCHY


class GVAAllocator:
    """
    Allocator that distributes national waste to companies based on EBITDA.

    Uses EBITDA as proxy for GVA. Matches on primary NACE code only.

    Parameters
    ----------
    companies_df : pd.DataFrame
        Company data with EBITDA.
        Required columns: company_id, company_name, nace_2digit, ebitda, country_code
    facilities_df : pd.DataFrame, optional
        E-PRTR facility registry for validated mode matching.
        Not used in simple mode.
    validate_waste_types : bool, optional
        Whether to validate waste types against IED-EWC mapping.
        Default: False (simple mode). Set True for validated IED mode.

    Attributes
    ----------
    companies : pd.DataFrame
        Company data with parsed NACE codes
    """

    def __init__(
        self,
        companies_df: pd.DataFrame,
        facilities_df: Optional[pd.DataFrame] = None,
        validate_waste_types: bool = False,
    ):
        self.validate_waste_types = validate_waste_types
        self.facilities = facilities_df
        self._prepare_companies(companies_df)

        if self.validate_waste_types and facilities_df is not None:
            from src.mappings.ied_ewc_stat import get_ied_waste_matrix

            self.waste_matrix = get_ied_waste_matrix()

    def _prepare_companies(self, companies_df: pd.DataFrame):
        """Prepare company data with standardized NACE codes."""
        self.companies = companies_df.copy()

        # Ensure required columns exist
        required = ["company_id", "company_name", "ebitda", "country_code"]
        missing = [c for c in required if c not in self.companies.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Extract 2-digit NACE if not present
        if "nace_2digit" not in self.companies.columns:
            if "nace_primary" in self.companies.columns:
                self.companies["nace_2digit"] = self.companies["nace_primary"].apply(
                    lambda x: x[1:3] if x and len(x) >= 3 else None
                )
            else:
                raise ValueError("Missing nace_2digit or nace_primary column")

    def _filter_hazard_total(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter to HAZ_NHAZ rows only.

        Eurostat env_wasgen reports waste in three hazard categories:
        - HAZ: Hazardous waste only
        - NHAZ: Non-hazardous waste only
        - HAZ_NHAZ: Total (hazardous + non-hazardous)

        Using HAZ_NHAZ avoids double-counting that would occur if we summed
        HAZ and NHAZ separately. If no hazard column exists, assume data is
        already filtered or aggregated.
        """
        if "hazard" in df.columns:
            return df[df["hazard"] == "HAZ_NHAZ"].copy()
        return df

    def _melt_year_columns(
        self, df: pd.DataFrame, min_year: int = 2020
    ) -> pd.DataFrame:
        """
        Melt year columns (2004, 2006, ..., 2022) into rows.

        Returns DataFrame with 'year' and 'tonnes' columns.
        Only includes years >= min_year.
        """
        # Identify year columns (numeric column names)
        year_cols = [c for c in df.columns if str(c).isdigit()]
        id_cols = [c for c in df.columns if c not in year_cols]

        melted = df.melt(
            id_vars=id_cols, value_vars=year_cols, var_name="year", value_name="tonnes"
        )
        melted["year"] = melted["year"].astype(int)

        # Filter to min_year onwards
        return melted[melted["year"] >= min_year].copy()

    def _prepare_time_series(
        self, df: pd.DataFrame, stale_cutoff_year: int = 2016
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare time series data: skip stale categories, impute missing years.

        Parameters
        ----------
        df : pd.DataFrame
            Long-format DataFrame with 'year' and 'tonnes' columns
        stale_cutoff_year : int
            Skip categories with no data since this year (default 2016)

        Returns
        -------
        cleaned_df : pd.DataFrame
            Cleaned DataFrame with imputed values and 'imputed' column
        impute_log : pd.DataFrame
            Log recording imputations
        """
        impute_log = []
        result_rows = []

        for (country, nace, waste), group in df.groupby(["country", "nace", "waste"]):
            group = group.sort_values("year")

            # Skip waste categories with no data since cutoff year
            recent = group[group["year"] >= stale_cutoff_year]
            has_recent = (recent["tonnes"].notna() & (recent["tonnes"] > 0)).any()
            if not has_recent:
                continue

            # Impute missing values using mean of adjacent years
            for _, row in group.iterrows():
                row = row.copy()
                if pd.isna(row["tonnes"]) or row["tonnes"] == 0:
                    prev = group[(group["year"] < row["year"]) & (group["tonnes"] > 0)]
                    next_ = group[(group["year"] > row["year"]) & (group["tonnes"] > 0)]

                    if len(prev) > 0 and len(next_) > 0:
                        prev_val = prev.iloc[-1]["tonnes"]
                        next_val = next_.iloc[0]["tonnes"]
                        row["tonnes"] = (prev_val + next_val) / 2
                        row["imputed"] = True
                        impute_log.append(
                            {
                                "country": country,
                                "nace": nace,
                                "waste": waste,
                                "year": row["year"],
                                "imputed_value": row["tonnes"],
                                "prev_year": prev.iloc[-1]["year"],
                                "prev_value": prev_val,
                                "next_year": next_.iloc[0]["year"],
                                "next_value": next_val,
                            }
                        )
                    else:
                        row["imputed"] = False
                else:
                    row["imputed"] = False
                result_rows.append(row)

        return pd.DataFrame(result_rows), pd.DataFrame(impute_log)

    def _parse_nace_code(self, nace_code: str) -> List[str]:
        """
        Parse a NACE code that may be a combined/range code.

        Handles formats like:
        - 'C24' -> ['24']
        - 'C24_C25' -> ['24', '25']
        - 'C10-C12' -> ['10', '11', '12']
        - 'C24.10' -> ['24.10']
        """
        code = nace_code.replace("C", "").strip()

        # Handle underscore-separated codes like '24_25'
        if "_" in code:
            parts = code.split("_")
            return [p.strip() for p in parts]

        # Handle range codes like '10-12'
        if "-" in code and code.count("-") == 1:
            parts = code.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                start, end = int(parts[0]), int(parts[1])
                return [str(i) for i in range(start, end + 1)]
            return [p.strip() for p in parts]

        # Section codes
        section_map = {
            "B": ["05", "06", "07", "08", "09"],
            "A": ["01", "02", "03"],
            "": [str(i) for i in range(10, 34)],
            "D": ["35"],
            "E": ["36", "37", "38", "39"],
            "F": ["41", "42", "43"],
        }
        if code in section_map:
            return section_map[code]

        return [code]

    def calculate_ebitda_shares(
        self, country: str, nace_code: str, waste_code: Optional[str] = None
    ) -> Tuple[pd.DataFrame, str]:
        """
        Calculate each company's share of sector EBITDA.

        Matches on primary NACE code only (2-digit level).

        Parameters
        ----------
        country : str
            ISO 2-letter country code
        nace_code : str
            NACE code (can be combined like 'C24_C25')
        waste_code : str, optional
            EWC-Stat waste code (used only in validated mode)

        Returns
        -------
        matched_df : pd.DataFrame
            Companies with calculated EBITDA shares.
            Columns: company_id, company_name, ebitda, ebitda_share
        filter_status : str
            Status: 'ok', 'no_nace_match', 'no_waste_match'
        """
        nace_divisions = self._parse_nace_code(nace_code)

        # Filter by country
        country_mask = self.companies["country_code"] == country
        matched = self.companies[country_mask].copy()

        if len(matched) == 0:
            return pd.DataFrame(), "no_nace_match"

        # Filter by primary NACE (2-digit division)
        nace_mask = matched["nace_2digit"].isin(nace_divisions)
        matched = matched[nace_mask].copy()

        if len(matched) == 0:
            return pd.DataFrame(), "no_nace_match"

        # Calculate EBITDA shares
        total_ebitda = matched["ebitda"].sum()
        if total_ebitda <= 0:
            return pd.DataFrame(), "no_nace_match"

        matched["ebitda_share"] = matched["ebitda"] / total_ebitda

        return matched, "ok"

    def allocate_waste(
        self,
        wasgen_df: pd.DataFrame,
        countries: Optional[List[str]] = None,
        deduplicate_nace: bool = True,
        min_year: int = 2020,
        stale_cutoff_year: int = 2016,
    ) -> pd.DataFrame:
        """
        Allocate national waste generation to companies by EBITDA share.

        Parameters
        ----------
        wasgen_df : pd.DataFrame
            National waste generation data (long format).
            Required columns: country (or geo), nace (or nace_r2),
                            waste, year, tonnes
        countries : list, optional
            Countries to process. Default: all in wasgen_df.
        deduplicate_nace : bool, optional
            Whether to remove NACE hierarchy overlaps before allocation.
            Default: True. Prevents double-counting.

        Returns
        -------
        pd.DataFrame
            Company-level waste allocations with columns:
            company_id, company_name, country, nace, waste_type, year,
            allocated_tonnes, national_tonnes, ebitda_share, method
        """
        wasgen_df = wasgen_df.copy()

        # Step 1: Normalize column names for consistent processing
        wasgen_df = self._standardize_wasgen_columns(wasgen_df)

        # Step 2: Filter to HAZ_NHAZ to avoid summing HAZ + NHAZ (would double-count)
        wasgen_df = self._filter_hazard_total(wasgen_df)

        # Step 3: Remove parent NACE codes when children exist
        # e.g., if both C24_C25 and C24 exist, remove C24_C25 to avoid double-counting
        if deduplicate_nace:
            wasgen_df, dedup_log = self._deduplicate_nace_hierarchy(wasgen_df)
            self._nace_dedup_log = dedup_log
        else:
            self._nace_dedup_log = pd.DataFrame()

        # Check if data has year columns (wide format) or already has 'tonnes' column
        year_cols = [c for c in wasgen_df.columns if str(c).isdigit()]
        if year_cols and "tonnes" not in wasgen_df.columns:
            # Melt year columns to long format
            wasgen_df = self._melt_year_columns(wasgen_df, min_year=min_year)

            # Prepare time series: skip stale categories, impute gaps
            wasgen_df, impute_log = self._prepare_time_series(
                wasgen_df, stale_cutoff_year=stale_cutoff_year
            )
            self._impute_log = impute_log
        else:
            self._impute_log = pd.DataFrame()
            # Add year column if not present (legacy format)
            if "year" not in wasgen_df.columns:
                wasgen_df["year"] = min_year
            if "imputed" not in wasgen_df.columns:
                wasgen_df["imputed"] = False

        # Step 4: Filter to requested countries
        if countries:
            wasgen_df = wasgen_df[wasgen_df["country"].isin(countries)]

        results = []
        unallocated = []

        # Step 5: Aggregate to unique (country, nace, waste, year) combinations
        # This handles any duplicate rows in the input data
        grouped = (
            wasgen_df.groupby(["country", "nace", "waste", "year"])
            .agg({"tonnes": "sum"})
            .reset_index()
        )

        # Step 6: Allocate each waste stream to companies based on EBITDA share
        for _, row in grouped.iterrows():
            country, nace, waste, year = (
                row["country"],
                row["nace"],
                row["waste"],
                row["year"],
            )
            national_tonnes = row["tonnes"]

            # Skip zero or missing values
            if pd.isna(national_tonnes) or national_tonnes <= 0:
                continue

            # Find companies matching this country+NACE and calculate their shares
            shares, filter_status = self.calculate_ebitda_shares(
                country, nace, waste_code=waste
            )

            # Track waste streams that couldn't be allocated (no matching companies)
            if len(shares) == 0:
                unallocated.append(
                    {
                        "country": country,
                        "nace": nace,
                        "waste": waste,
                        "year": year,
                        "national_tonnes": national_tonnes,
                        "reason": filter_status,
                    }
                )
                continue

            # Distribute national waste to each company proportionally
            for _, comp in shares.iterrows():
                allocated_tonnes = national_tonnes * comp["ebitda_share"]

                if allocated_tonnes > 0:
                    results.append(
                        {
                            "company_id": comp["company_id"],
                            "company_name": comp["company_name"],
                            "country": country,
                            "nace": nace,
                            "waste_type": waste,
                            "year": year,
                            "allocated_tonnes": allocated_tonnes,
                            "national_tonnes": national_tonnes,
                            "ebitda": comp["ebitda"],
                            "ebitda_share": comp["ebitda_share"],
                            "method": "ebitda",
                        }
                    )

        allocated_df = pd.DataFrame(results)
        self.unallocated = pd.DataFrame(unallocated)

        if len(self.unallocated) > 0:
            total_unalloc = self.unallocated["national_tonnes"].sum()
            total_alloc = (
                allocated_df["allocated_tonnes"].sum() if len(allocated_df) > 0 else 0
            )
            total = total_alloc + total_unalloc
            pct = 100 * total_unalloc / total if total > 0 else 0

            warnings.warn(
                f"{len(self.unallocated)} waste streams ({pct:.1f}% of tonnage) "
                f"could not be allocated."
            )

        return allocated_df

    def _standardize_wasgen_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names to match expected format.

        Handles different source formats:
        - Eurostat API: geo, nace_r2, obs_value
        - Processed files: country, nace, tonnes
        - Legacy files: mean_wasgen instead of tonnes

        Also converts full country names (e.g., 'Sweden') to ISO codes ('SE')
        for matching with company data.
        """
        # Detect if data has year columns (wide format) - affects how we handle tonnes
        year_cols = [c for c in df.columns if str(c).isdigit()]
        has_year_cols = len(year_cols) > 0

        # Column name mappings from various source formats
        renames = {
            "geo": "country",  # Eurostat uses 'geo'
            "country_code": "country",  # Some processed files
            "nace_r2": "nace",  # Eurostat uses 'nace_r2'
            "obs_value": "tonnes",  # Eurostat observation value
        }
        # Only rename mean_wasgen if no year columns (legacy aggregated format)
        if not has_year_cols:
            renames["mean_wasgen"] = "tonnes"

        for old, new in renames.items():
            if old in df.columns and new not in df.columns:
                df = df.rename(columns={old: new})

        # Convert full country names to ISO 2-letter codes for matching
        if "country" in df.columns:
            country_name_to_iso = {
                "Sweden": "SE",
                "Norway": "NO",
                "Finland": "FI",
                "Denmark": "DK",
                "Germany": "DE",
                "France": "FR",
                "Poland": "PL",
                "Netherlands": "NL",
                "Belgium": "BE",
                "Austria": "AT",
                "Italy": "IT",
                "Spain": "ES",
            }
            # Only convert if values look like full names (length > 2)
            sample = (
                df["country"].dropna().iloc[0]
                if len(df["country"].dropna()) > 0
                else ""
            )
            if len(sample) > 2:
                df["country"] = df["country"].map(
                    lambda x: country_name_to_iso.get(x, x) if pd.notna(x) else x
                )

        return df

    def _deduplicate_nace_hierarchy(
        self, wasgen_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Remove NACE hierarchy overlaps to prevent double-counting.

        Eurostat env_wasgen sometimes reports waste at multiple NACE levels:
        - Aggregate: C24_C25 (basic metals + fabricated metals combined)
        - Detailed: C24 (basic metals), C25 (fabricated metals)

        If both exist for the same (country, waste) combination, the aggregate
        includes the detailed values. We remove the aggregate to avoid
        double-counting when summing across NACE codes.

        The NACE_HIERARCHY dict (from emissions_based_allocator) defines
        parent-child relationships for this deduplication.
        """
        dedup_log = []
        rows_to_remove = []

        # Check each (country, waste) combination for hierarchy overlaps
        for (country, waste), group in wasgen_df.groupby(["country", "waste"]):
            nace_codes = set(group["nace"].unique())

            for parent, children in NACE_HIERARCHY.items():
                if parent in nace_codes:
                    children_present = [c for c in children if c in nace_codes]

                    if children_present:
                        parent_mask = (
                            (wasgen_df["country"] == country)
                            & (wasgen_df["nace"] == parent)
                            & (wasgen_df["waste"] == waste)
                        )
                        parent_rows = wasgen_df[parent_mask]

                        if len(parent_rows) > 0:
                            rows_to_remove.extend(parent_rows.index.tolist())

                            for _, row in parent_rows.iterrows():
                                dedup_log.append(
                                    {
                                        "country": country,
                                        "nace_removed": parent,
                                        "nace_kept": ", ".join(children_present),
                                        "waste": waste,
                                        "tonnes_removed": row.get("tonnes", 0),
                                    }
                                )

        cleaned_df = wasgen_df.drop(index=rows_to_remove).reset_index(drop=True)
        dedup_log_df = pd.DataFrame(dedup_log)

        if len(dedup_log) > 0:
            total_removed = dedup_log_df["tonnes_removed"].sum()
            warnings.warn(
                f"NACE hierarchy deduplication removed {len(dedup_log)} rows "
                f"({total_removed:,.0f} tonnes) to avoid double-counting"
            )

        return cleaned_df, dedup_log_df

    def get_allocation_summary(self, allocated_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate summary statistics for the allocation.

        Parameters
        ----------
        allocated_df : pd.DataFrame
            Output from allocate_waste()

        Returns
        -------
        pd.DataFrame
            Summary by country and NACE with company counts and coverage
        """
        if len(allocated_df) == 0:
            return pd.DataFrame()

        summary = (
            allocated_df.groupby(["country", "nace"])
            .agg(
                {
                    "allocated_tonnes": "sum",
                    "national_tonnes": "first",
                    "company_id": "nunique",
                    "ebitda_share": ["mean", "std"],
                }
            )
            .reset_index()
        )

        summary.columns = [
            "country",
            "nace",
            "allocated_tonnes",
            "national_tonnes",
            "n_companies",
            "mean_share",
            "std_share",
        ]

        if len(self.unallocated) > 0:
            unalloc_by_nace = self.unallocated.groupby(["country", "nace"])[
                "national_tonnes"
            ].sum()
            summary["unallocated_tonnes"] = summary.apply(
                lambda r: unalloc_by_nace.get((r["country"], r["nace"]), 0), axis=1
            )
        else:
            summary["unallocated_tonnes"] = 0

        summary["coverage_pct"] = (
            100
            * summary["allocated_tonnes"]
            / (summary["allocated_tonnes"] + summary["unallocated_tonnes"])
        )

        return summary.sort_values("allocated_tonnes", ascending=False)


def load_gva_allocator(
    companies_path: Path,
    country: str = "SE",
    filter_nace: Optional[List[str]] = None,
    validate_waste_types: bool = False,
) -> GVAAllocator:
    """
    Factory function to create a GVAAllocator with loaded company data.

    Parameters
    ----------
    companies_path : Path
        Path to company data file (Excel or CSV)
    country : str
        Country code. Default: 'SE' for Sweden.
    filter_nace : list of str, optional
        NACE divisions to filter by (e.g., ['24', '25'])
    validate_waste_types : bool
        Whether to enable waste type validation

    Returns
    -------
    GVAAllocator
        Initialized allocator
    """
    from src.loaders.retriever import load_swedish_companies

    if country == "SE":
        companies = load_swedish_companies(companies_path, filter_nace=filter_nace)
    else:
        raise NotImplementedError(f"Country {country} not yet supported")

    return GVAAllocator(companies, validate_waste_types=validate_waste_types)


def run_gva_allocation_pipeline(
    companies_path: str,
    wasgen_path: str,
    output_dir: str,
    countries: Optional[List[str]] = None,
    filter_nace: Optional[List[str]] = None,
    deduplicate_nace: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run the complete GVA-based allocation pipeline.

    Parameters
    ----------
    companies_path : str
        Path to company data file
    wasgen_path : str
        Path to waste generation data (CSV, long format)
    output_dir : str
        Directory for output files
    countries : list, optional
        Countries to process
    filter_nace : list of str, optional
        NACE divisions to filter companies by
    deduplicate_nace : bool
        Whether to remove NACE hierarchy overlaps

    Returns
    -------
    allocated_df : pd.DataFrame
        Company-level allocations
    summary_df : pd.DataFrame
        Allocation summary
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load waste generation data
    wasgen = pd.read_csv(wasgen_path)

    # Create allocator
    allocator = load_gva_allocator(Path(companies_path), filter_nace=filter_nace)

    # Run allocation
    allocated = allocator.allocate_waste(
        wasgen, countries, deduplicate_nace=deduplicate_nace
    )

    # Generate summary
    summary = allocator.get_allocation_summary(allocated)

    # Save outputs
    allocated.to_csv(output_dir / "company_waste_allocated.csv", index=False)
    summary.to_csv(output_dir / "gva_allocation_summary.csv", index=False)

    if len(allocator.unallocated) > 0:
        allocator.unallocated.to_csv(
            output_dir / "gva_unallocated_waste.csv", index=False
        )

    if hasattr(allocator, "_nace_dedup_log") and len(allocator._nace_dedup_log) > 0:
        allocator._nace_dedup_log.to_csv(
            output_dir / "gva_nace_dedup_log.csv", index=False
        )

    print(f"GVA allocation complete:")
    print(f"  - {len(allocated)} company allocations")
    print(f"  - {allocated['allocated_tonnes'].sum():,.0f} tonnes allocated")
    print(f"  - {allocated['company_id'].nunique()} unique companies")
    if "year" in allocated.columns:
        print(f"  - Years: {sorted(allocated['year'].unique())}")
    if deduplicate_nace:
        print(f"  - NACE deduplication: ENABLED")
    print(f"  - Outputs saved to {output_dir}")

    return allocated, summary
