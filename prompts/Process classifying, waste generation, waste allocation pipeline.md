Main requirement: Try to use the existing codebase structure and files as much as possible for this pipeline. We've got a bunch of this structure already created, but it hasn't been integrated yet. Let's try to modify existing files before creating new ones.

The steps we need to lay out are:

1. Load each facility in the eprtr data (@src/loaders/eprtr_emissions, load_all_emissions()). This is done.
2. Classify the process technology used for each facility by it's emissions fingerprint (let's focus only on the IS (Iron&Steel BAT for now.). This will produce a technology classification for each facility.
	1. For this we can use the emissions from the process input/output data gathered from the BREF documents (IS is currently being constructed) in the @data/interim/process_emissions.csv
	2. We haven't decided on what the best way of classifying is:
		1. Tensor decomposition (seems pretty good), @src/allocation/technology_identifier.py
		2. Rules based (if CO2 high and CO high -> BOF etc. etc.), Approach from: @src/validation/steel_tracker.py
		3. Other possible classification methods? Could you outline some examples?
		

3. Once each facility is classified correctly, we can estimate each facilities range of waste generation from the process input/output data, simply by using the CO2 emission data (X tonne CO2/ tonne produced output) = (Y tonne residual/tonne produced output) => (X tonne CO2) = (Y tonne residual). This will produce a range of min/max waste generation
	1. We can calculate each all residual types (e.g EAF slag, ladle slag), and all sum for total generated waste 


4. Then we can use the @src/allocation/emissions_based_allocator.py to allocate the national * NACE reported waste to each facility, using the CO2 as allocator. For now we will use a straight allocation of all waste codes (individual codes and aggregated codes). We will have to come up with weighted coefficients for each technology (based on the BAT documents, and for example the input-output table gives a reported range of waste production, meaning an EAF produces A amount of wastes, and BF_BOF produces B amount of wastes), so we can weight the coefficients based on that. This is still in it's infancy and there's many aspects to consider (for example what are the total waste production for a facility classified as a single technology (e.g EAF has simple waste regimes, and BOF more complex if it includes BF as well?))
	1. This produces a 'reported waste from this facility'


The output of this pipeline is that each facility get's:
	- Classified with a technology regime
	- Estimated process waste generation (estimates on individual residuals and total residuals from BAT/BREF data)
	- Allocated reported waste (individual waste codes, and aggregated codes)
	- The combination of estimated process waste generation and allcoation national wastes, is that we can analyse where potential recovery waste stocks and flows are found, on a Pan-EU level.


Later on we will use this data to (These stages we can do later on): 
- Load it into the the facility hierarchichal clustering approaches we have started experimenting with in @src/analysis/facility_clustering.py
- Load and visualise it in the @app/app.py