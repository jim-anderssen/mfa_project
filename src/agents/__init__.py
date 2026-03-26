"""
Agents module for automated data extraction using Claude Agent SDK.
"""

from src.agents.waste_extraction_agent import WasteExtractionAgent
from src.agents.config import ExtractionConfig

__all__ = ['WasteExtractionAgent', 'ExtractionConfig']
