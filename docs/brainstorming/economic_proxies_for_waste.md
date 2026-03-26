# Economic Proxies for Industrial Waste Generation

Date: 2026-01-16

## Context

When allocating national (NUTS0) waste statistics to individual companies or regions, we need economic proxies that correlate with physical waste generation. This is especially relevant for heavy industries (C24 Basic metals, C25 Fabricated metal products) where waste is tied to material throughput.

---

## Proxy Comparison

| Proxy | Quality | Availability | Best For |
|-------|---------|--------------|----------|
| **Physical production (tonnes)** | ⭐⭐⭐⭐⭐ | Low | Direct allocation if available |
| **Gross Value Added (GVA)** | ⭐⭐⭐⭐ | Medium | Capital-intensive heavy industry |
| **Turnover** | ⭐⭐⭐ | High | General purpose, with caveats |
| **Employment** | ⭐⭐ | High | Labor-intensive industries only |
| **Energy consumption** | ⭐⭐⭐⭐ | Low | Process industries |

---

## Gross Value Added (GVA) Explained

### Definition

**GVA = Output - Intermediate Consumption**

Or equivalently:

**GVA = Turnover - Cost of Purchased Inputs + Change in Inventories**

GVA measures the value a company *creates* through its production process, excluding the value of materials and services it purchases from others.

### Components

```
Turnover (Sales Revenue)
  - Purchases of raw materials
  - Purchases of energy
  - Purchases of services
  - Other intermediate consumption
  ─────────────────────────────────
= Gross Value Added (GVA)

GVA can also be decomposed as:
  = Wages + Operating Surplus + Depreciation + Taxes on production
```

### Example: Steel Company

| Item | Amount (€M) |
|------|-------------|
| Turnover (steel sales) | 500 |
| - Iron ore purchases | -150 |
| - Coal/coke purchases | -80 |
| - Energy (electricity, gas) | -50 |
| - Services (logistics, maintenance) | -40 |
| **= Gross Value Added** | **180** |

The €180M GVA represents what the company *added* through its transformation process.

---

## Why GVA is Superior for Waste Allocation

### 1. Avoids Double-Counting

**Problem with turnover**: When Company A sells steel to Company B who makes car parts, both report turnover for the same material. Waste allocation based on turnover would count the material twice.

**GVA solution**: Only counts the value added at each stage, not the passed-through material value.

```
Example supply chain:

Iron mine (GVA: €50M) → Steel mill (GVA: €100M) → Parts maker (GVA: €80M)
         ↓                      ↓                        ↓
    Mining waste           Slag, scale              Scrap metal

Each company's waste relates to THEIR transformation, not purchased inputs.
```

### 2. Insensitive to Commodity Price Swings

**Problem with turnover**: Steel prices can double in a year. A company's turnover doubles but physical production (and waste) stays the same.

**GVA solution**: When steel prices rise, both output value AND input costs rise proportionally. GVA remains relatively stable.

```
Scenario: Steel price doubles

                    Year 1      Year 2      Change
Turnover            €500M       €1,000M     +100%
Input costs         €320M       €640M       +100%
GVA                 €180M       €360M       +100%
Physical output     100kt       100kt       0%
Waste generated     15kt        15kt        0%

Turnover suggests 2x waste, but physical reality unchanged.
GVA also doubles, but so does the denominator in allocation formulas.
```

Actually, GVA has the same problem here. The real advantage is in cross-sectional comparison:

```
Cross-sectional comparison (same year):

Company A: High-value specialty steel
  Turnover: €500M, Output: 50kt, Waste: 8kt

Company B: Commodity steel
  Turnover: €500M, Output: 200kt, Waste: 30kt

Using turnover: Both get same waste allocation (WRONG)
Using GVA: Company B likely has lower margins → lower GVA → less over-allocation
Using physical production: Correct allocation (BEST)
```

### 3. Reflects Transformation Intensity

GVA correlates with how much *physical transformation* a company performs:

- **High GVA** = Significant processing, machining, chemical transformation → More waste
- **Low GVA** = Trading, assembly, minimal processing → Less waste

```
Same turnover, different GVA:

Steel trading company:    Turnover €100M, GVA €5M   → Minimal waste
Steel processing company: Turnover €100M, GVA €30M → Significant waste
```

### 4. Better Than Employment for Capital-Intensive Industries

**Problem with employment**: Modern steel plants are highly automated. A plant with 500 workers may produce as much as an old plant with 2,000 workers.

```
Modern automated plant:  500 employees,  Output: 1Mt,  Waste: 150kt
Old labor-intensive:     2,000 employees, Output: 1Mt,  Waste: 150kt

Employment proxy: Old plant gets 4x waste allocation (WRONG)
GVA proxy: Similar GVA → similar allocation (CORRECT)
```

---

## Allocation Formula

### Country → Company Allocation

Given:
- National waste generation by sector: `Waste_country[sector]`
- Company financial data: `GVA_company[i]`
- All companies in sector: `GVA_sector_total`

```
Waste_company[i] = Waste_country[sector] × (GVA_company[i] / GVA_sector_total)
```

### With Sector-Specific Waste Intensity

If waste intensity varies within a NACE code (e.g., primary vs secondary steel production):

```
Waste_company[i] = Waste_country[sector]
                   × (GVA_company[i] / GVA_sector_total)
                   × waste_intensity_factor[subsector]
```

Where `waste_intensity_factor` comes from:
- EXIOBASE waste coefficients
- Literature values
- Process engineering estimates

---

## Limitations of GVA

### 1. Still Not Physical Production

GVA is an economic measure. Two companies with identical GVA may have different:
- Product mixes (high-value vs commodity)
- Process efficiency (modern vs old technology)
- Vertical integration (more in-house processing = higher GVA)

**Mitigation**: Use subsector-specific waste intensity coefficients.

### 2. Affected by Profit Margins

High-margin companies have higher GVA for same physical output.

```
Premium brand steel:  GVA €200M, Output 100kt
Commodity steel:      GVA €150M, Output 100kt

GVA proxy over-allocates to premium brand.
```

**Mitigation**: Where possible, use industry-average margins or physical production data.

### 3. Data Availability

GVA is less commonly reported than turnover or employment.

**Calculation from financial statements**:
```
GVA ≈ Operating Revenue
      - Cost of Materials
      - Cost of Services

Or:

GVA ≈ Personnel Costs + EBITDA
```

---

## Practical Recommendations

### For Heavy Industry (C24, C25)

1. **Primary choice**: GVA from company financial data
2. **Fallback**: Turnover with sector-specific adjustment factors
3. **Validation**: Cross-check against known large facilities (IED installations)

### Data Sources for Company-Level Allocation

| Data | Source | Coverage |
|------|--------|----------|
| Company financials | Retriever, Orbis, national registries | Good |
| IED facility locations | E-PRTR, national databases | Large installations |
| Waste intensity coefficients | EXIOBASE, literature | By sector |
| National waste totals | Eurostat env_wasgen | Complete |

### Hybrid Approach

```
Step 1: Get national waste by NACE sector (Eurostat env_wasgen)
Step 2: Get company GVA from financial databases
Step 3: Allocate proportionally within sector
Step 4: Apply subsector waste intensity adjustments (EXIOBASE)
Step 5: Validate against known IED facilities
```

---

## References

- Eurostat Manual on Waste Statistics (methodology)
- EXIOBASE 3 documentation (waste coefficients)
- SBS methodology (GVA calculation)

---

## Notes

- For micro-level company allocation, GVA from financial statements is ideal
- No need for NUTS2 aggregation if company-level data is available
- Retriever/Orbis databases provide company financials including calculated GVA
- Swedish company data export (2025-08) may already include relevant fields

---

## Quick Reference: How GVA Works

**GVA = Turnover − Cost of Purchased Inputs**

It measures what a company *creates* through transformation, not what passes through.

```
Example: Steel mill

Turnover (steel sales)          €500M
− Iron ore purchases            €150M
− Energy costs                   €50M
− Services/other inputs          €80M
─────────────────────────────────────
= Gross Value Added             €220M
```

From financial statements:
```
GVA ≈ Personnel Costs + EBITDA
```

---

## Why GVA is the Best Proxy for Waste Allocation

### 1. Measures Transformation, Not Throughput

A steel *trader* and steel *processor* might both have €100M turnover, but:
- Trader: GVA €5M (just buys and sells) → minimal waste
- Processor: GVA €30M (cuts, treats, transforms) → significant waste

GVA captures who's actually *doing something* to the material.

### 2. Avoids the Employment Trap

Modern automated steel plant: 500 workers, produces 1Mt
Old manual plant: 2,000 workers, produces 1Mt

Both generate ~150kt waste. Employment says old plant gets 4× the allocation. GVA correctly gives them similar allocations because transformation value is similar.

### 3. Less Sensitive to Price Swings Than Turnover

When steel prices spike, turnover doubles but waste doesn't. GVA rises too, but the *ratio* between companies stays more stable because everyone's output prices and input costs move together.

---

## Direct Company-Level Allocation Formula

With micro-level company financial data (Retriever/Orbis), bypass NUTS2 entirely:

```
Company_waste = Country_waste[NACE] × (Company_GVA / Σ All_companies_GVA_in_NACE)
```

This allocates national waste statistics directly to individual companies based on their share of sector GVA.
