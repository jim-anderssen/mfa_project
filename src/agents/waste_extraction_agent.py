"""
Waste Extraction Agent using Claude Agent SDK.

Extracts waste generation data from industrial company environmental reports
and outputs CSV files compatible with the existing NUTS2 allocation pipeline.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

# Claude Agent SDK imports (when available)
# from claude_agent_sdk import query, ClaudeAgentOptions

from src.io_file import save_csv, PROCESSED_DIR
from src.nuts2.data_loader import COUNTRY_MAP, load_nuts2_names
from src.agents.config import ExtractionConfig, get_nace_description
from src.agents.subagents import (
    get_report_finder_prompt,
    get_waste_extractor_prompt,
    get_data_mapper_prompt,
    get_nuts2_locator_prompt
)
from src.agents.tools.waste_tools import (
    map_waste_to_ewc_stat,
    validate_extraction,
    normalize_country,
    lookup_nuts2_region,
    convert_waste_units
)
from src.agents.validation.validator import WasteDataValidator


# System prompt for the main agent
SYSTEM_PROMPT = """You are a specialized agent for extracting waste generation data from industrial company environmental reports.

## Your Goal
Build a dataset of company-reported waste generation data that is compatible with Eurostat waste statistics.

## Output Schema
For each waste stream extracted, create a record with:
- country: Country name
- country_code: ISO 2-letter code (e.g., DE, SE, PL)
- nuts2_region: NUTS2 code if facility location is known (e.g., DE21)
- nuts2_name: NUTS2 region name
- nace_r2: NACE Rev. 2 activity code (e.g., C24)
- nace_r2_activity: Activity description
- waste: EWC-Stat code (e.g., W061, W12A)
- waste_description: Waste type description
- year: Reporting year
- waste_tonnes: Amount in tonnes
- treatment_method: R/D codes or description (recycled, disposed, etc.)
- source_company: Company name
- source_facility: Facility/site name
- facility_location: City/address
- source_document: Report URL or filename
- confidence_score: Your confidence in the extraction (0-1)
- extraction_notes: Any notes about the extraction

## Process Flow

1. **Search for Reports**
   - Find major companies in the target NACE sector
   - Locate their sustainability/environmental reports
   - Prioritize reports with waste data sections

2. **Extract Waste Data**
   - Read PDF reports
   - Find waste generation tables/sections
   - Extract amounts, types, and treatment methods
   - Note facility locations when provided

3. **Map to Standard Codes**
   - Map company waste categories to EWC-Stat codes
   - Translate foreign language terms to English
   - Map facility locations to NUTS2 regions

4. **Validate Data**
   - Check for required fields
   - Verify plausibility of amounts
   - Ensure codes are valid

## Quality Standards
- Only include records with confidence >= 0.6
- Convert all amounts to tonnes
- Flag uncertain mappings
- Prefer facility-level data over consolidated totals
"""


class WasteExtractionAgent:
    """
    Agent for extracting waste data from company environmental reports.

    Uses Claude's capabilities with:
    - WebSearch for finding company reports
    - PDF reading for data extraction
    - Custom tools for data mapping and validation
    """

    def __init__(self, config: Optional[ExtractionConfig] = None):
        """
        Initialize the extraction agent.

        Parameters
        ----------
        config : ExtractionConfig, optional
            Configuration options. Uses defaults if not provided.
        """
        self.config = config or ExtractionConfig()
        self.validator = WasteDataValidator(load_reference=True)
        self._nuts2_names = None
        self._results: List[Dict[str, Any]] = []

    @property
    def nuts2_names(self) -> Dict[str, str]:
        """Lazy-load NUTS2 region names."""
        if self._nuts2_names is None:
            try:
                self._nuts2_names = load_nuts2_names()
            except Exception:
                self._nuts2_names = {}
        return self._nuts2_names

    def create_extraction_prompt(
        self,
        nace_codes: List[str],
        countries: List[str],
        years: List[int]
    ) -> str:
        """
        Create the main extraction prompt.

        Parameters
        ----------
        nace_codes : list
            NACE sector codes to target
        countries : list
            Countries to search
        years : list
            Reporting years to target

        Returns
        -------
        str
            Formatted prompt for the agent
        """
        nace_descriptions = [
            f"{code}: {get_nace_description(code)}"
            for code in nace_codes
        ]

        prompt = f"""Extract waste generation data from company environmental reports.

## Target Parameters

**NACE Sectors:**
{chr(10).join('- ' + desc for desc in nace_descriptions)}

**Countries:** {', '.join(countries)}

**Years:** {', '.join(map(str, years))}

**Max companies per sector:** {self.config.max_companies_per_sector}

## Instructions

1. For each NACE sector, search for major companies in the target countries
2. Find their sustainability or environmental reports for the target years
3. Extract waste generation data, including:
   - Waste types and amounts (in tonnes)
   - Treatment methods (recycling, disposal, recovery)
   - Facility locations (for NUTS2 mapping)
4. Map company waste categories to EWC-Stat codes
5. Return structured data as JSON

## Expected Output Format

Return a JSON array of waste records:
```json
[
  {{
    "country": "Germany",
    "country_code": "DE",
    "nuts2_region": "DEA1",
    "nuts2_name": "Düsseldorf",
    "nace_r2": "C24",
    "nace_r2_activity": "Manufacture of basic metals",
    "waste": "W061",
    "waste_description": "Metal wastes, ferrous",
    "year": 2023,
    "waste_tonnes": 150000,
    "treatment_method": "recycling",
    "source_company": "ThyssenKrupp Steel",
    "source_facility": "Duisburg-Hamborn",
    "facility_location": "Duisburg",
    "source_document": "https://...",
    "confidence_score": 0.9,
    "extraction_notes": null
  }}
]
```

Begin extraction now."""

        return prompt

    def process_extracted_data(
        self,
        raw_data: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Process and normalize extracted data.

        Parameters
        ----------
        raw_data : list
            Raw extracted records from agent

        Returns
        -------
        pd.DataFrame
            Processed and normalized data
        """
        processed = []

        for record in raw_data:
            # Normalize country
            if 'country' in record:
                country_result = normalize_country(record['country'])
                if country_result['success']:
                    record['country'] = country_result['country']
                    record['country_code'] = country_result['country_code']

            # Map waste code if not already mapped
            if 'waste' not in record and 'waste_type' in record:
                mapping = map_waste_to_ewc_stat(
                    record['waste_type'],
                    record.get('nace_r2', '')
                )
                if mapping['success']:
                    record['waste'] = mapping['ewc_stat_code']
                    record['waste_description'] = mapping['ewc_stat_description']

            # Convert units if needed
            if 'unit' in record and record.get('waste_tonnes') is None:
                amount = record.get('amount', record.get('waste_amount', 0))
                converted, _ = convert_waste_units(amount, record['unit'])
                record['waste_tonnes'] = converted

            # Lookup NUTS2 if facility location provided
            if record.get('facility_location') and not record.get('nuts2_region'):
                nuts2_result = lookup_nuts2_region(
                    record['facility_location'],
                    record.get('country_code')
                )
                if nuts2_result['success']:
                    record['nuts2_region'] = nuts2_result['nuts2_region']
                    record['nuts2_name'] = self.nuts2_names.get(
                        nuts2_result['nuts2_region'],
                        nuts2_result.get('nuts2_name')
                    )

            # Add mean_wasgen for pipeline compatibility
            record['mean_wasgen'] = record.get('waste_tonnes', 0)

            processed.append(record)

        return pd.DataFrame(processed)

    def validate_and_filter(
        self,
        df: pd.DataFrame
    ) -> tuple:
        """
        Validate extracted data and filter by confidence.

        Parameters
        ----------
        df : pd.DataFrame
            Extracted data

        Returns
        -------
        tuple
            (valid_df, invalid_df, summary)
        """
        valid_df, invalid_df = self.validator.validate_batch(
            df,
            min_confidence=self.config.min_confidence
        )

        summary = self.validator.get_validation_summary(valid_df, invalid_df)

        return valid_df, invalid_df, summary

    def save_results(
        self,
        df: pd.DataFrame,
        filename: str,
        include_invalid: bool = False,
        invalid_df: pd.DataFrame = None
    ) -> Path:
        """
        Save extraction results to CSV.

        Parameters
        ----------
        df : pd.DataFrame
            Valid extracted data
        filename : str
            Output filename
        include_invalid : bool
            Whether to save invalid records separately
        invalid_df : pd.DataFrame
            Invalid records (if include_invalid=True)

        Returns
        -------
        Path
            Path to saved file
        """
        output_path = self.config.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Select columns for output
        output_columns = [
            'country', 'country_code', 'nuts2_region', 'nuts2_name',
            'nace_r2', 'nace_r2_activity', 'waste', 'waste_description',
            'year', 'waste_tonnes', 'mean_wasgen', 'treatment_method',
            'source_company', 'source_facility', 'facility_location',
            'source_document', 'confidence_score', 'extraction_notes'
        ]

        # Only include columns that exist
        existing_cols = [c for c in output_columns if c in df.columns]
        df[existing_cols].to_csv(output_path, index=False)

        if include_invalid and invalid_df is not None and len(invalid_df) > 0:
            invalid_path = output_path.parent / f"invalid_{filename}"
            invalid_df.to_csv(invalid_path, index=False)

        return output_path

    async def run_extraction(
        self,
        nace_codes: List[str] = None,
        countries: List[str] = None,
        years: List[int] = None
    ) -> pd.DataFrame:
        """
        Run the full extraction pipeline.

        This is the main entry point for running the agent.

        Parameters
        ----------
        nace_codes : list, optional
            NACE codes to target. Defaults to config.
        countries : list, optional
            Countries to search. Defaults to config.
        years : list, optional
            Years to target. Defaults to config.

        Returns
        -------
        pd.DataFrame
            Validated extraction results

        Note
        ----
        This method requires the Claude Agent SDK to be installed and configured.
        For usage without the SDK, see run_extraction_manual().
        """
        nace_codes = nace_codes or self.config.target_nace_codes
        countries = countries or self.config.target_countries
        years = years or self.config.target_years

        # Create extraction prompt
        prompt = self.create_extraction_prompt(nace_codes, countries, years)

        # This is where the Claude Agent SDK would be called
        # For now, provide a placeholder that shows expected usage
        print("=" * 60)
        print("EXTRACTION PROMPT")
        print("=" * 60)
        print(prompt)
        print("=" * 60)
        print()
        print("To run this agent, you need the Claude Agent SDK installed:")
        print("  pip install claude-agent-sdk")
        print()
        print("Then use the SDK's query() function with:")
        print("  - WebSearch tool for finding reports")
        print("  - WebFetch tool for downloading PDFs")
        print("  - Read tool for processing PDFs")
        print()

        # Return empty DataFrame as placeholder
        return pd.DataFrame()

    def run_extraction_manual(
        self,
        extracted_json: str
    ) -> pd.DataFrame:
        """
        Process manually extracted data (for testing without SDK).

        Parameters
        ----------
        extracted_json : str
            JSON string with extracted records

        Returns
        -------
        pd.DataFrame
            Validated and processed data
        """
        raw_data = json.loads(extracted_json)
        df = self.process_extracted_data(raw_data)
        valid_df, invalid_df, summary = self.validate_and_filter(df)

        print(f"Validation Summary:")
        print(f"  Total records: {summary['total_records']}")
        print(f"  Valid records: {summary['valid_records']}")
        print(f"  Invalid records: {summary['invalid_records']}")
        print(f"  Validation rate: {summary['validation_rate']:.1%}")

        return valid_df


def create_agent(config: ExtractionConfig = None) -> WasteExtractionAgent:
    """
    Factory function to create a configured extraction agent.

    Parameters
    ----------
    config : ExtractionConfig, optional
        Configuration options

    Returns
    -------
    WasteExtractionAgent
        Configured agent instance
    """
    return WasteExtractionAgent(config)


# Example usage and testing
if __name__ == "__main__":
    # Create agent with default config
    config = ExtractionConfig(
        target_countries=['Germany', 'Sweden', 'Poland'],
        target_nace_codes=['C24', 'C25'],
        target_years=[2022, 2023],
        max_companies_per_sector=5
    )

    agent = create_agent(config)

    # Show extraction prompt
    print("Creating extraction prompt...")
    prompt = agent.create_extraction_prompt(
        config.target_nace_codes,
        config.target_countries,
        config.target_years
    )
    print(prompt)

    # Test with sample data
    sample_data = '''[
        {
            "country": "Germany",
            "nace_r2": "C24",
            "waste_type": "Steel scrap",
            "amount": 150000,
            "unit": "tonnes",
            "year": 2023,
            "treatment_method": "recycling",
            "source_company": "Example Steel GmbH",
            "facility_location": "Duisburg",
            "confidence_score": 0.85
        }
    ]'''

    print("\nProcessing sample data...")
    result = agent.run_extraction_manual(sample_data)
    print(f"\nProcessed {len(result)} valid records")
    if len(result) > 0:
        print(result.to_string())
