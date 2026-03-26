# MFA Project

Material Flow Analysis of European waste generation, treatment, and transboundary shipments using Eurostat data. Supports investment decisions in recycling/recovery technology.

**Note**: Keep all notes, documentation, and comments as short and concise as possible.

## Structure
- `data/raw/` - Original Eurostat data (immutable)
- `data/interim/` - Intermediate transforms
- `data/processed/` - Final . Each category of data belongs in a subdirectory of this.
- `src/` - Python modules
- `notebooks/` - Analysis notebooks

Any archive directories are meant to store old explorations, and MUST not be looked into by you, unless EXPLICITLY stated otherwise.

## Key Concepts
- **NACE2**: Industry codes (C24=Basic metals, C25=Fabricated metals)
- **EWC-Stat/LoW**: Waste classification codes

## Analysis Potentials
- **wasgen/prodcom** - Link waste generation to production statistics
- **wasgen/mfa** - Compare waste flows with material flow accounts
- **wasgen-wastrt-import-export** - Waste balance (generation = treatment + export - import)
- **Facility allocation** - Allocate waste to specific treatment facilities
