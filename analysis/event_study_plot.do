****************************************************
* Event Study: OPA per month relative to PFU
*An event study is a way of looking at outcomes before and after a specific 'event'.In our case the event is patient's/centres first PIFU date/centre's roll-out) 
****************************************************
*First we check the no anticipation assumption - flat trends before PIFU, good

* 1. Import dataset
import delimited using "output/dataset_rheum.csv", clear

* 2. Keep PFU patients
keep if any_pfu == "T" | any_pfu == "True" | any_pfu == "1"

* 3. Convert dates to Stata format
gen opa_date = date(first_opa_date, "YMD")
gen pfu_date = date(first_pfu_date, "YMD")
format opa_date pfu_date %td

* 4. Calculate event month relative to PFU
gen event_month = floor((opa_date - pfu_date)/30)

* Keep window (e.g. -36 to +36 months)
keep if event_month >= -36 & event_month <= 36

* 5. Create indicator: had any visit in this month
gen opa_this_month = 1   // since each row is a visit

* 6. Collapse to number of patients with visits per month
collapse (sum) opa_visits=opa_this_month, by(event_month)

* 7. Plot: This checks the no anticipation assumption
twoway (line opa_visits event_month, sort lwidth(medthick) lcolor(blue)) ///
       , ytitle("Number of OPAs") ///
         xtitle("Months relative to PFU rollout") ///
         title("Event Study: OPA counts around PFU") ///
         xline(0, lpattern(dash) lcolor(red))

* 8. Export
graph export "output/processed/event_study_monthly.png", replace
****************************************************


*Notes
*Data only stored first_opa_date