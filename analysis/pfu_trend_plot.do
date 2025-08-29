*------------------------------------------------------------*
* PIFU Uptake Over Time
*------------------------------------------------------------*

* Load dataset
import delimited using "output/dataset_rheum.csv", clear

* Keep only PFU patients
keep if any_pfu == "T" | any_pfu == "True" | any_pfu == "1"

* Collapse to counts by year
collapse (count) n=patient_id, by(first_pfu_year)


* Save collapsed data for plotting outside Stata
export delimited using "output/processed/pfu_trend_counts.csv", replace	
	
	
* Plot uptake over time
twoway (line n first_pfu_year, sort lwidth(medthick) lcolor(blue)) ///
       , ytitle("Number of PFU patients") xtitle("Year of first PFU") ///
         title("PFU Uptake Over Time")	
	

*Save plot //to only run in stata - Issue in STata environment: Docker image running Stata in OpenSAFELY doesnt include GRaph2png translator
*graph export "output/processed/pfu_trend_plot.png", replace
	





