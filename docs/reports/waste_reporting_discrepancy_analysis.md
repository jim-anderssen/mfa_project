# Waste Reporting Discrepancy Analysis

Analysis of why EU waste statistics show dramatic reductions for some countries in NACE C24_C25 (basic metals/fabricated metals), and the role of recovery pathways in excluding waste from statistics.

## 1. Observed Discrepancies

Eurostat env_wasgen data for NACE C24_C25 shows divergent trends:

| Country | 2004 | 2022 | Change |
|---------|------|------|--------|
| Sweden | 10.6M | 1.2M | -89% |
| Germany | 9.9M | 3.9M | -61% |
| Poland | 33.0M | 2.9M | -91% |
| Finland | 2.7M | 2.9M | +7% |
| Italy | 4.9M | 4.9M | 0% |

Sweden, Germany, and Poland show dramatic reductions while Finland and Italy remain stable. This analysis investigates whether these reductions reflect real changes or statistical artifacts.

## 2. Classification Changes (2008-2010)

A major reclassification of EWC-Stat waste codes occurred around 2008-2010:

**Discontinued aggregate codes:**
- W12A → Mineral and solidified wastes (aggregate)
- W12-13 → Mineral wastes and solidified wastes
- W06 → Metallic wastes (aggregate)
- W10 → Mixed waste (aggregate)
- W13 → Solidified waste

**Replacement codes:**
- W061, W062, W063 → Ferrous, non-ferrous, mixed metallic
- W12B → Mineral waste (other)
- W121 → Glass waste
- W126 → Mineral construction waste
- W128_13 → Other mineral/solidified waste

**Poland example:** The 30M+ tonne drop is largely attributable to W12A reclassification. In 2004, Poland reported 29.9M tonnes under W12A (mineral wastes from metal production). After reclassification, much of this material no longer appears in equivalent codes.

## 3. Byproduct vs Waste Distinction

Materials sold as products are NOT waste under EU Waste Framework Directive criteria. Steel production generates substantial byproducts that never enter waste statistics.

**SSAB Luleå 2024 example:**

Biprodukter (byproducts): **465.5 kton** sold as products:
- Hyttsten (blast furnace slag) → road construction aggregate
- Tar, benzene, sulfur → sold to external buyers
- LD-slagg → road base material

These 465 kton are material flows that bypass waste statistics entirely because they are classified as products, not waste.

## 4. Internal Recycling Exclusion

Material recycled internally within facilities is typically excluded from reported waste generation. This represents a significant hidden flow.

**SSAB Luleå 2024 restprodukter (residual materials):**

Total: **770.7 kton**

Breakdown:
- ~722 kton internally reused (återanvänt internt)
- ~40-70 kton to deponi (landfill) → reported as waste
- ~37 kton external recycling

Only the landfilled portion (~5-9% of total) clearly enters waste statistics. Internal recycling, which represents 94% of restprodukter, is excluded.

## 5. Quantitative Comparison

Comparing official statistics with actual facility data:

| Metric | Value |
|--------|-------|
| Sweden C24_C25 Eurostat 2022 | 1.18M tonnes |
| SSAB Luleå total material flows | 1.2M+ tonnes |
| SSAB Luleå in waste statistics | ~50-70 kton |

A single Swedish steel facility handles more material than the entire sector's reported waste. Only ~5% of material flows appear in official waste statistics.

## 6. Conclusions

1. **Real waste generation has NOT decreased** as dramatically as statistics suggest
2. **Recovery pathways exclude material from statistics:**
   - Byproducts sold as products (e.g., slag for construction)
   - Internal recycling (process loops)
   - Pre-consumer scrap returns
3. **Classification changes around 2010** caused statistical discontinuities, particularly for mineral wastes (W12A)
4. **Cross-country comparison is problematic** due to different classification practices
5. **Pre-2010 vs post-2010 data** requires extreme caution when comparing trends

## Data Sources

- Eurostat env_wasgen dataset (NACE C24_C25, HAZ_NHAZ)
- SSAB Miljörapport 2024 Luleå
- Analysis script: `src/analysis/one_off/analyze_waste_discrepancy.py`
