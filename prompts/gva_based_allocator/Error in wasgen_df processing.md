I've spotted an error in the wasgen_df processing in @src/allocation/gva_based_allocator.py and the allocate_waste method.   

If you look at the env_wasgen dataset, you have a hazard column that has HAZ, NHAZ and HAZ_NHAZ (which sums the 2 previous columns). So for the waste allocation we should boolean index only HAZ_NHAZ and use that as all waste, not HAZ and NHAZ aswell.

Then we have timeseries data from 2004-2022, we want allocate each biannual datapoints to the companies, (but we have economic data only from 2020 I think, so only from then onwards, from the start of the economic data). 

There's a bunch of waste categories that haven't been recorded since 2008 or similar. These we don't have to allocate anymore , we can skip them completetly. If there's a waste type which has one missing value (say 2020) but records 2018 and 2022, then we impute by the mean of the 2 closest values, and record the imputation in a column with imputed value: 2020.


  