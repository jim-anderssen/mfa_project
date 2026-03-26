"""
Example usage of the Waste Extraction Agent.

This script demonstrates how to:
1. Configure the extraction agent
2. Run extraction for specific sectors and countries
3. Process and validate results
4. Integrate with the existing NUTS2 pipeline
"""

import asyncio
from datetime import datetime

from src.agents import WasteExtractionAgent, ExtractionConfig
from src.agents.tools.waste_tools import (
    map_waste_to_ewc_stat,
    normalize_country,
    lookup_nuts2_region
)
from src.mappings.translations import translate_waste_term, detect_language


def example_basic_usage():
    """Basic usage example - extract waste data for metal manufacturing."""
    print("=" * 60)
    print("BASIC USAGE EXAMPLE")
    print("=" * 60)

    # Create configuration
    config = ExtractionConfig(
        target_countries=['Germany', 'Sweden', 'Poland'],
        target_nace_codes=['C24'],  # Basic metals
        target_years=[2023],
        max_companies_per_sector=5
    )

    # Create agent
    agent = WasteExtractionAgent(config)

    # Generate extraction prompt (shows what the agent would do)
    prompt = agent.create_extraction_prompt(
        config.target_nace_codes,
        config.target_countries,
        config.target_years
    )

    print("\nGenerated Prompt:")
    print("-" * 40)
    print(prompt[:1000] + "...")
    print()


def example_process_manual_data():
    """Example of processing manually extracted data."""
    print("=" * 60)
    print("MANUAL DATA PROCESSING EXAMPLE")
    print("=" * 60)

    agent = WasteExtractionAgent()

    # Sample extracted data (as if from PDF reports)
    sample_data = '''[
        {
            "country": "Germany",
            "nace_r2": "C24",
            "nace_r2_activity": "Manufacture of basic metals",
            "waste_type": "Steel scrap",
            "amount": 250000,
            "unit": "tonnes",
            "year": 2023,
            "treatment_method": "recycling",
            "source_company": "ThyssenKrupp Steel Europe",
            "facility_location": "Duisburg",
            "source_document": "Sustainability Report 2023",
            "confidence_score": 0.9
        },
        {
            "country": "Sweden",
            "nace_r2": "C24",
            "nace_r2_activity": "Manufacture of basic metals",
            "waste_type": "Slagg",
            "amount": 180,
            "unit": "kt",
            "year": 2023,
            "treatment_method": "reuse in construction",
            "source_company": "SSAB",
            "facility_location": "Luleå",
            "source_document": "Annual Report 2023",
            "confidence_score": 0.85
        },
        {
            "country": "Poland",
            "nace_r2": "C24",
            "waste_type": "złom stalowy",
            "amount": 95000,
            "unit": "tonnes",
            "year": 2023,
            "source_company": "ArcelorMittal Poland",
            "facility_location": "Katowice",
            "confidence_score": 0.8
        }
    ]'''

    # Process the data
    print("\nProcessing sample data...")
    result = agent.run_extraction_manual(sample_data)

    print("\nProcessed Results:")
    print("-" * 40)
    if len(result) > 0:
        for col in ['country', 'nuts2_region', 'waste', 'waste_tonnes', 'source_company']:
            if col in result.columns:
                print(f"{col}: {result[col].tolist()}")

    return result


def example_tool_usage():
    """Example of using individual tools."""
    print("=" * 60)
    print("TOOL USAGE EXAMPLES")
    print("=" * 60)

    # Waste term mapping
    print("\n1. Waste Term Mapping:")
    print("-" * 40)

    terms_to_map = [
        ("Steel scrap from production", ""),
        ("Flugasche", ""),  # German for fly ash
        ("Déchets plastiques", ""),  # French for plastic waste
        ("Slagg", ""),  # Swedish for slag
    ]

    for term, context in terms_to_map:
        result = map_waste_to_ewc_stat(term, context)
        if result['success']:
            print(f"  '{term}' → {result['ewc_stat_code']}: {result['ewc_stat_description']}")
            if result.get('detected_language'):
                print(f"    (Detected language: {result['detected_language']})")
        else:
            print(f"  '{term}' → {result['suggestion']}")

    # Country normalization
    print("\n2. Country Normalization:")
    print("-" * 40)

    countries = ["Germany", "DE", "Czech Republic", "Turkiye", "Holland"]
    for country in countries:
        result = normalize_country(country)
        if result['success']:
            print(f"  '{country}' → {result['country']} ({result['country_code']})")
        else:
            print(f"  '{country}' → {result.get('suggestion', 'Unknown')}")

    # NUTS2 lookup
    print("\n3. NUTS2 Region Lookup:")
    print("-" * 40)

    locations = [
        ("Duisburg", "DE"),
        ("Stockholm", None),
        ("Katowice", "PL"),
        ("Munich", "DE"),
    ]

    for location, country_code in locations:
        result = lookup_nuts2_region(location, country_code)
        if result['success']:
            print(f"  '{location}' → {result['nuts2_region']} ({result['match_type']})")
        else:
            print(f"  '{location}' → {result.get('suggestion', 'Not found')}")


def example_translation():
    """Example of multi-language translation."""
    print("=" * 60)
    print("TRANSLATION EXAMPLES")
    print("=" * 60)

    terms = [
        "Metallabfälle",  # German
        "Déchets métalliques",  # French
        "Metallavfall",  # Swedish
        "Residuos metálicos",  # Spanish
        "Odpady metalowe",  # Polish
    ]

    print("\nTranslating waste terms:")
    print("-" * 40)
    for term in terms:
        lang = detect_language(term)
        translation = translate_waste_term(term, lang)
        print(f"  '{term}' ({lang or '?'}) → '{translation}'")


def example_integration_with_pipeline():
    """Example of integrating with existing NUTS2 allocation pipeline."""
    print("=" * 60)
    print("PIPELINE INTEGRATION EXAMPLE")
    print("=" * 60)

    print("""
To integrate extracted data with the existing pipeline:

```python
from src.agents import WasteExtractionAgent, ExtractionConfig
from src.nuts2.allocation import allocate_waste_to_regions
from src.nuts2.data_loader import load_sbs_employment, get_sbs_nuts2_employment, load_nuts2_names

# 1. Extract data
config = ExtractionConfig(
    target_countries=['Germany', 'Sweden'],
    target_nace_codes=['C24'],
    target_years=[2023]
)
agent = WasteExtractionAgent(config)

# 2. Run extraction (with Claude Agent SDK)
# extracted_df = await agent.run_extraction()

# 3. For records without NUTS2 region, allocate using employment shares
sbs = load_sbs_employment()
sbs_nuts2 = get_sbs_nuts2_employment(sbs)
nuts2_names = load_nuts2_names()

# Filter to records without direct NUTS2 assignment
to_allocate = extracted_df[extracted_df['nuts2_region'].isna()]

# Allocate using employment proxy
allocated = allocate_waste_to_regions(to_allocate, sbs_nuts2, nuts2_names)

# 4. Combine direct extractions with allocated data
direct = extracted_df[extracted_df['nuts2_region'].notna()]
final_df = pd.concat([direct, allocated], ignore_index=True)

# 5. Save results
from src.io_file import save_csv
save_csv(final_df, 'extracted_company_waste.csv')
```
""")


def example_sdk_usage():
    """Example of how to use with Claude Agent SDK (when available)."""
    print("=" * 60)
    print("CLAUDE AGENT SDK USAGE")
    print("=" * 60)

    print("""
When the Claude Agent SDK is installed, you can run the full extraction:

```python
import asyncio
from src.agents import WasteExtractionAgent, ExtractionConfig

async def run_extraction():
    config = ExtractionConfig(
        target_countries=['Germany', 'Sweden', 'Poland'],
        target_nace_codes=['C24', 'C25'],
        target_years=[2022, 2023],
        max_companies_per_sector=10
    )

    agent = WasteExtractionAgent(config)

    # Run the extraction pipeline
    results = await agent.run_extraction()

    # Save results
    output_path = agent.save_results(
        results,
        f'extracted_waste_{datetime.now().strftime("%Y%m%d")}.csv'
    )

    print(f"Saved {len(results)} records to {output_path}")
    return results

# Run
asyncio.run(run_extraction())
```

To install the Claude Agent SDK:
```bash
pip install claude-agent-sdk
export ANTHROPIC_API_KEY=your-api-key
```

The agent will:
1. Use WebSearch to find company sustainability reports
2. Use WebFetch to download PDF reports
3. Extract waste data from the PDFs
4. Map waste categories to EWC-Stat codes
5. Identify NUTS2 regions from facility locations
6. Validate and output structured CSV data
""")


if __name__ == "__main__":
    # Run all examples
    example_basic_usage()
    print("\n")

    example_tool_usage()
    print("\n")

    example_translation()
    print("\n")

    result = example_process_manual_data()
    print("\n")

    example_integration_with_pipeline()
    print("\n")

    example_sdk_usage()
