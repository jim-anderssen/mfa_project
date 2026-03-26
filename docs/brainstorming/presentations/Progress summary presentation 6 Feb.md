
Agenda:
- Capabilities with agentic developments
- Introductionary goals
- Data overview -> Method
- Basic facility example
- Demo of Pan-EU idea


- Capabilities with agentic developments
- Introductionary goals (track waste quantities, characteristics and interesting recovery markets)

- Example:
	- SSAB Luleå has recorded emissions data:
		- What process tech does it use (BOF or EAF)?
			- Specifies BOF slag, EAF slag etc.
		- How much process waste does SSAB Luleå generate?
		- How much waste does SSAB Luleå report?
			- This indicates the share of process waste still classified as waste, and not as a by-product
				- Larger shares means less mature recovery management => Interesting recovery source for Ragn-sells
			- Lower ratios of reported waste/generated waste => Interesting sources
		- Are there other facilities in the region with similar/large amounts of waste?
			- The region is interesting as a whole!

- Data overview
	- E-PRTR data 
		- Keystone data (emission fingerprints)
		- Allows for 
			- 1: classify process tech
			- 2: Estimate process waste generation
			- 3: Allocation of reported national * Nace waste
	- BAT reference documents
		- Reference data to estimate process waste generation :
			- t CO2/t LS
			- t Slag/t LS
			- => Compute: t Slag/t CO2
	- Eurostat national * NACE waste statistics
		- Allows for identifying regions' recovery potential from the generated wastes.


- Demo of idea:
	- Process technology classification
	- Process waste estimation per facility
	- Allocation of reported national waste to facilities
	- Geospatial clustering


- Emissions-based classification of process technology:
	- Specifies technology (e.g. BOF/EAF) and the types of wastes being generated.

- Emissions-based estimation of process waste:
	- Estimates the ranges of generated process waste with a mass-balance min/max. 
	- Supervised/rules-based estimation with process I/O data
	- Unsupervised tensor decomposition
	
- Reported waste quantity allocation to facilities:
	- Emissions basis (E-PRTR data)
	- Gross-value added basis (Economic data)
	- Regional SBS basis (Eurostat business stats.)

- Geospatial hotspots/clustering of recovery markets

- Interpretations & moving forward

