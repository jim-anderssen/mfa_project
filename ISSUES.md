## High priority

   For @classify_tech_generate_and_allocate_waste.py
   - [ ] Check that the waste allocation includes all relevant nace categories in total shares (C24_C25 waste shares -> includes C24, C25 facilities, not only C24). ja-2026-02-03
   - [ ] Check the impact of an insufficient amount of facilities with reported CO2 for waste allocation, how does it skew the allocation? (for example countries with lower repoted CO2 coverage will get more skewed results, can this variance be computed with an % interval or similar?) Can we regress CO2 emissions on other parameter/s to increase coverage? ja-2026-02-03
   - [ ] 
   - [ ] Decide whether the waste generation should get a yearly estimated waste (2020,21,22,23 etc.), currently the CO2 value is mean of all years. Also if the waste allocation should get yearly allocated waste (2020,2021,2022) etc., currerntly mean over 3 years. ja-2026-02-03
   - [ ] Remove inclusion of waste codes that have been discontinued from waste statistics (codes that haven't been reported since 2008 etc.). ja-2026-02-03
   - [ ] Check facility clustering logic. Are the nace codes causing troubles? Optimising or better approaches available?
   - [ ] Make recovery maturity indicator (Already on the way). 2025-02-04
   - [ ] See why all facilities don't show up in app. Does it have to do with allocated tonnage minimum 5000 tonnes in clustering, or it it because of a mix up with IED and EPRTR activities?
   

           

## Low priority
                
- [ ] Improve clarity and ease-of-use in app, for example the pop-up boxes and them showing unknowns etc. ja-2026-02-03
                                                                               

  ## Backlog                                                                                                          
  - [ ] Technology classifications of all IEDs (take from BAT reference documents). For IEDs that don't have specific classifications, decide whether to add BAT reference as classification or just skip step. ja-2026-02-03
  - [ ] Validate results of IS tech classifications(e.g use GEM IS data to validate?), waste generation and allocated wastes (once high priority have been cleared). Review whether current approaches are effective and should be optimised, or if other methods should be tested. ja-2026-02-03
  - [ ] Can we use the E-PRTR data from the Access database for more data types? https://sdi.eea.europa.eu/catalogue/srv/api/records/ff47e25d-5d4c-491d-b9ce-de17ca61fe6d/attachments/EEA_Industrial_Reporting_Metadata_v13.pdf (newest data download link): https://sdi.eea.europa.eu/data/3461f4ab-a3ee-4af2-bc11-95e651a8d0ba). (pandas_access: https://pypi.org/project/pandas_access/) ja-2025-02-03
- [ ] Update the pipelines using the 2025 eprtr data. ja-2025-02-03
- [ ] Create latent waste indicator (alloc waste/generated waste, <<1 = mature recovery market, ~1 = interesting recovery stream, >>1 = problematic allocation ), ja-2025-02-03
- [ ] Analysis of waste code trends for different countries. Which waste codes have been receding (for example in C24_C25, since there's such a difference between countries)
- [ ] If the allocation method is true, the allocated wastes to facilities *should* be close to the facilties' wasteTransfers from F4_2, if the allocation approach is effective. Supervised learning to get allocation data to match up with that. ja-20260204
- [ ] Adjacent sites (child sites like coking ovens etc.) get's allocated to the parent facilities (C19 -> C24) in the env_wasgen data!
- [ ] Does the offsite Waste transfers measure up with total wastes from wasgen * NACE sector data, (for example nace 24 total wastes, and offsite trnsfers from IEDs belonging to nace 24?
- [ ] HW offsite waste transfers as indicator of facility size (HW is kind of impossible to not generate and have to treat)
- [ ] Regions with plenty of HW disposal offsite waste transfers would indicate few recovery/recycling actors are present
- [ ] Which waste codes is it possible for a certain IED facility produce (out of the major process wastes). Allocate only these waste codes.

  **3. TODO comments** (for code-specific issues)                                                                                        

   TODO: Handle edge case where facility has no emissions data                                                                      

   FIXME: This allocation fails for multi-NACE facilities                                                                           

   NOTE: Consider caching this expensive computation