# MFA Project Task Plan

## Current Tasks

### 1. Economic Allocation Review
**Status:** Pending

Review and validate economic allocation methodology (regional/company based):
- Verify allocation logic in existing code
- Check data sources (SBS employment/turnover proxies)
- Validate allocation results against expected patterns
- Document methodology assumptions

### 2. Clustering Logic Audit
**Status:** Pending

Audit clustering logic - verify geo centroid calculations:
- Review geographic centroid calculation code
- Verify centroids are properly centered for NUTS2 regions
- Check coordinate system/projection handling
- Test with known regions for validation

### 3. Regional Clustering Algorithm Review
**Status:** Pending

Review overall clustering algorithm for regional waste profiles:
- Examine clustering parameters and methods
- Validate cluster assignments make sense
- Check feature scaling and normalization
- Review cluster quality metrics

### 4. Integrate Company-Based Economic Data
**Status:** Pending

Integrate company-based economic data into allocation:
- Identify relevant company-level data sources
- Design integration with existing regional allocation
- Implement company-to-NUTS2 mapping
- Validate company data quality and coverage
- Update allocation methodology to incorporate company metrics

### 5. Validate Allocation with Company Report Data
**Status:** Pending

Test allocation methodology against real company environmental reports:
- Fetch data from companies' environmental reports
- Filter companies by region/country, NACE category, and economic turnover threshold
- Collect all companies in a single region/country and NACE category above turnover threshold
- Regress allocated waste against true waste generation from company data
- Aggregate all waste categories to total waste per country (reports likely only state total waste)
- Compare allocated vs. reported waste to validate methodology accuracy
- Document discrepancies and refine allocation approach

---

## To Be Continued

_Add additional tasks below as they are identified_

---

**Last Updated:** 2026-01-16
