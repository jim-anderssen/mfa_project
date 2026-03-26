Objective: Allocating shares of national * NACE waste from env_wasgen data to facilities, with a method that identifies the waste generation of each facility appropriately, so as little skewness is found.

In this project we've got a few options of allocating shares of national * NACE waste to facilities, in @src/allocation: 
- gva_based (economic data, retriever)
- emissions based (E-PRTR data)

We've also got the SBS approach using eurostat NUTS2 * NACE data.

Each approach brings a few problems: 
- gva_based uses organisations and not facilities (GVA for many facilities under the same name, perhaps not even Swedish facilities?, I don't know). Not possiblt to quantify waste shares for individual facilities
- Emissions based uses proxies as CO2 etc. to allocate waste, and different technologies produces different amount of emissions, not necessarily scaling linearly with waste generation (for example BOF/EAF for steelmaking)
- SBS for NUTS2 * Nace data only identifies regions of intensive activity, but doesn't include any facilities at all, and we don't have gva or turnover data, only wages, salaries and num. of employment.


Can we combine this, or augment them with something more superior?


