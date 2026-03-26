# PRODCOM Waste Generation Coefficients Review

## Summary

The waste generation coefficients in `src/mappings/prodcom_waste.py` claim to be sourced from "Industry BAT reference documents" but this cannot be verified. Many coefficients appear to be rough estimates.

## Comparison with BREF Documents

### Aluminium (NACE 24.42) - `red_mud: 1.5`
- **Source:** BREF Non-Ferrous Metals Industries (2017)
- **BREF states:** "1.0–2.5 tonnes of red mud per tonne of alumina" depending on bauxite quality
- **Status:** ✓ Within documented range

### Iron & Steel (NACE 24.10) - `slag: 0.12`
- **Source:** BREF Iron and Steel Production (2013)
- **BREF states:** "250–300 kg blast furnace slag per tonne hot metal" (0.25–0.30)
- **Status:** ✗ Current value is roughly half the documented value

### Cement (NACE 23.51) - `kiln_dust: 0.015`
- **Source:** BREF Cement, Lime and Magnesium Oxide (2013)
- **BREF states:** CKD generation varies widely (1-10% of clinker production)
- **Status:** ~ Plausible but highly variable

### Aluminium dross (NACE 24.42) - `dross: 0.05`
- **Source:** BREF Non-Ferrous Metals Industries (2017)
- **BREF states:** Typically 15-25 kg per tonne of aluminium (0.015-0.025)
- **Status:** ✗ Current value is approximately double the documented range

## Recommendations

1. **Validate all coefficients** against actual BREF documents at https://eippcb.jrc.ec.europa.eu/reference

2. **Key BREFs to consult:**
   - Iron and Steel Production (IS)
   - Non-Ferrous Metals Industries (NFM)
   - Cement, Lime and Magnesium Oxide Manufacturing Industries (CLM)
   - Production of Pulp, Paper and Board (PP)
   - Food, Drink and Milk Industries (FDM)

3. **Add uncertainty ranges** rather than point estimates where data is variable

4. **Document sources** for each coefficient with specific BREF section references

5. **Consider process-specific factors** - many industries have multiple process routes with different waste profiles (e.g., BOF vs EAF steelmaking)

## Priority Updates Needed

| NACE | Parameter | Current | BREF Range | Priority |
|------|-----------|---------|------------|----------|
| 24.10 | slag | 0.12 | 0.25-0.30 | High |
| 24.42 | dross | 0.05 | 0.015-0.025 | High |
| 24.10 | total | 0.15 | Needs review | Medium |
| 17.11 | black_liquor | 0.50 | Needs review | Medium |

## References

- BREF documents: https://eippcb.jrc.ec.europa.eu/reference
- Eurostat PRODCOM: https://ec.europa.eu/eurostat/web/prodcom
- EWC-Stat codes: https://ec.europa.eu/eurostat/ramon/nomenclatures/
