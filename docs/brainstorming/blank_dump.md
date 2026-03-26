 We have waste generation allocated per facility
    # A lot of SRMs doesn't register as waste in e.g Sweden
        # But they might be in Finland, since their waste generation is much higher

        
 How to analyse this?
  - Trend analysis on waste types. Have they been declining (recovery paths found so doesn't even register as waste)
 - Check MFA/waste generation
    -  Or check ratio of direct material inputs/waste generation (and the trends of these!)
    - Check DMI of certain materials versus their waste generation (how efficiently are they using the material/classifying by-products as waste) and the trends of these!
 - Rawmat_trade/waste generation (Although this only covers import/exports)
 - Check PRIM waste, see if that includes the 10x tonnage of waste not tracked in current version
 - Domestic treatment gap

 -> This would let you check the level of efficiency in material handling?





Interesting recovery markets are almost implicit in the eurostat reported waste generation data, i.e highly productive regions with low ratio of reported waste have "mature" recovery technology and vice versa. 

SSAB in Luleå might not report their slags as waste, since legal use is certain and it's has been certified to meet quality criteria.
   - Another Steel plant in Europe, might not have had their slags accepted as a byproduct, and is still reported as waste. (-> Greater recovery opportunity).

How can this be checked? 
- Waste intesntity (Eurostat metadata says comparability between countries is "good", Swedish quality report 2018 on waste statistics says classifying by-products have impacted the waste generation comparability between countries.)
- Compare the national ratios of waste generation data and (production data or domestic material inputs or NACE turnover statistics).
- Signals how effective the industries are at converting 'wastes' into SRMs/byproducts.

-> This means that utilising the env_wasgen data is not just calculating quantities of generated wastes per facilities, it's implicitly detailing unexploited recovery sources.
   -> Might be more valuable for detailing unexploited recovery sources than quantifying exact wastes per facility.


-> Different waste reporting practices between countries can still impact the results, and should be examined.





### Add Claude Code SDK to interactive waste app? Other people can go in and type: "What are the most intersting hotspots for Green Liqour Dregs?"

Input-output table data for processes to quantify generated process waste per IED technology. 


# BAT-AEL, and BAT. Which facilities are classified against it, they should have more mature recovery technology.



# In the waste allocation pipeline, REMEMBER this from the Swedish quality report:
Local unit, establishment, facility, station have mostly been used assurvey objects. A local unit, establishment, facility or station can have several different economic activities, one main activity and several secondary activities. In this case the entire local unit,establishment, facility, station has been classified by its main activity. For example, coking plants can be found at steelworks.Independent coking plants (not existing in Sweden) should be classified as NACE 19 and steelworks as NACE 24. In our survey,coking plants at steelworks have been classified as belonging to NACE 24, and the waste generated there has been allocated toNACE 24.

I.e, several facilities shouldn't get a single waste allocation fraction, since they're included under the Main facility umbrella (coking plants at a steel works facility for example). 