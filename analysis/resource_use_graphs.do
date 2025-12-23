/*==============================================================================
DO FILE NAME:			resource_use_graphs.do
PROJECT:				OpenSAFELY PIFU project: Resource use
DATE: 					08/12/2025
AUTHOR:					R Njuguna									
DESCRIPTION OF FILE:	Resource use tables and graphs
DATASETS USED:			measures.csv				
==============================================================================*/

version 18.0
set type double
*ssc install blindschemes
*set scheme plotplainblind //colour scheme

* --- EDIT THESE PATHS if needed ---
global projectdir "C:\Users\Rebeccanj\GitHub\PIFU-HealthEconomics--project1--"
global measuresfile "$projectdir/output/measures/measures.csv"
global figdir "$projectdir/output/processed/figures"
capture mkdir "$figdir"

* --------------------------
* Import combined measures.csv
* --------------------------
clear
import delimited "$measuresfile", varnames(1) stringcols(_all)

* quick peek (comment out later)
*codebook
*describe, simple
*list in 1/8, abbrev(30)

* Create period_date from interval_start (format: YYYY-MM-DD)
gen double period_date = date(interval_start, "YMD")
format period_date %td

* Convert numerator to numeric once
gen double numerator_num = real(numerator)
gen double denominator_num = real(denominator)

*===============================================================
* PLOT 1a: Combined plot (Allopa, rheum and nonrheum) - 
*     mean visits per patient
*===============================================================

preserve

* keep the three visit measures + patient_count measure
keep if inlist(measure, "count_all_opa", "count_rheum_opa", "count_nonrheum_opa", "patient_count")

* ensure numeric count: use numerator_num (Calculated above line 37)
* collapse to one observation per period_date x measure (sum)
collapse (sum) cnt = numerator_num, by(period_date measure)

* now reshape wide so each measure is a column
reshape wide cnt, i(period_date) j(measure) string

* rename into clean variables (check the exact generated names with describe if unsure)
rename cntcount_all_opa        all_opa
rename cntcount_rheum_opa      rheum_opa
rename cntcount_nonrheum_opa   nonrheum_opa
rename cntpatient_count        patient_count

* replace missing with 0 for visit totals
replace all_opa = 0 if missing(all_opa)
replace rheum_opa = 0 if missing(rheum_opa)
replace nonrheum_opa = 0 if missing(nonrheum_opa)

* --------------------------
* Compute mean visits per patient
* --------------------------
gen double mean_all_opa = .
gen double mean_rheum_opa = .
gen double mean_nonrheum_opa = .

replace mean_all_opa = all_opa / patient_count if patient_count > 0
replace mean_rheum_opa = rheum_opa / patient_count if patient_count > 0
replace mean_nonrheum_opa = nonrheum_opa / patient_count if patient_count > 0

* --------------------------
* Plot the three mean series (per patient)
* --------------------------
twoway ///
    (line mean_all_opa period_date,       sort lcolor(blue)  lwidth(medium) ) ///
    (line mean_rheum_opa period_date,     sort lcolor(red)   lpatt(dash)  lwidth(medium) ) ///
    (line mean_nonrheum_opa period_date,  sort lcolor(green) lpatt(dash)  lwidth(medium) ) ///
    , ///
    title("Mean outpatient visits per patient over time") ///
    xtitle("Month") ytitle("Mean visits per patient per month") ///
    legend(order(1 "All OPA" 2 "Rheum OPA" 3 "Non-rheum OPA") pos(6) rows(1)) ///
    graphregion(margin(r+3)) ///
    name(g_overall, replace)

graph export "$figdir/all_opa_mean_per_patient.png", name(g_overall) replace width(1600)

restore


*===============================================================
* PLOT 1b: Combined plot (Allopa, rheum and nonrheum) 
*     Mean visits per 1000 patients
*===============================================================
preserve

* keep the three visit measures + patient_count measure
keep if inlist(measure, "count_all_opa", "count_rheum_opa", "count_nonrheum_opa", "patient_count")

* ensure numeric count: use numerator_num (Calculated above line 37)
* collapse to one observation per period_date x measure (sum)
collapse (sum) cnt = numerator_num, by(period_date measure)

* now reshape wide so each measure is a column
reshape wide cnt, i(period_date) j(measure) string

* rename into clean variables (check the exact generated names with describe if unsure)
rename cntcount_all_opa        all_opa
rename cntcount_rheum_opa      rheum_opa
rename cntcount_nonrheum_opa   nonrheum_opa
rename cntpatient_count        patient_count

* replace missing with 0 if you prefer zeros instead of missing for visit totals
replace all_opa = 0 if missing(all_opa)
replace rheum_opa = 0 if missing(rheum_opa)
replace nonrheum_opa = 0 if missing(nonrheum_opa)

* Leave patient_count missing if missing (guard below prevents division by zero)
* optionally replace patient_count = 0 if you prefer (not recommended)

* --------------------------
* Compute mean visits per patient
* --------------------------
* Prevent division by zero by computing only where patient_count>0
gen double mean_all_opa = .
gen double mean_rheum_opa = .
gen double mean_nonrheum_opa = .

replace mean_all_opa = all_opa / patient_count if patient_count > 0
replace mean_rheum_opa = rheum_opa / patient_count if patient_count > 0
replace mean_nonrheum_opa = nonrheum_opa / patient_count if patient_count > 0

* Scale to per-1000 patients for easier plotting/reading
gen double mean_all_opa_per1000 = mean_all_opa * 1000
gen double mean_rheum_opa_per1000 = mean_rheum_opa * 1000
gen double mean_nonrheum_opa_per1000 = mean_nonrheum_opa * 1000

* --------------------------
* Plot the three mean series (per 1,000 patients)
* --------------------------
twoway ///
    (line mean_all_opa_per1000 period_date,       sort lcolor(blue)  lwidth(medium) ) ///
    (line mean_rheum_opa_per1000 period_date,     sort lcolor(red)  lpatt(dash)  lwidth(medium) ) ///
    (line mean_nonrheum_opa_per1000 period_date,  sort lcolor(green) lpatt(dash)  lwidth(medium) ) ///
    , ///
    title("Mean outpatient visits per 1,000 patients over time") /// 
    xtitle("Month") ytitle("Visits per 1,000 patients") ///
    legend(order(1 "All OPA" 2 "Rheum OPA" 3 "Non-rheum OPA") position(6) rows(1)) ///
    graphregion(margin(r+3)) ///
    name(g_overall, replace)

graph export "$figdir/all_opa_mean_per1000.png", name(g_overall) replace width(1600)

restore



*===============================================================
* PLOT 2: Combined plot (All OPA, rheum and non-rheum)
*          Mean visits per 1,000 patients with COVID shading
*===============================================================

preserve

*---------------------------------------------------------------
* Keep required measures
*---------------------------------------------------------------
keep if inlist(measure, ///
    "count_all_opa", ///
    "count_rheum_opa", ///
    "count_nonrheum_opa", ///
    "patient_count")

*---------------------------------------------------------------
* Collapse to one row per period_date x measure
*---------------------------------------------------------------
collapse (sum) cnt = numerator_num, by(period_date measure)

*---------------------------------------------------------------
* Reshape to wide format
*---------------------------------------------------------------
reshape wide cnt, i(period_date) j(measure) string

* Rename variables
rename cntcount_all_opa        all_opa
rename cntcount_rheum_opa      rheum_opa
rename cntcount_nonrheum_opa   nonrheum_opa
rename cntpatient_count        patient_count

* Replace missing visit counts with 0
replace all_opa = 0 if missing(all_opa)
replace rheum_opa = 0 if missing(rheum_opa)
replace nonrheum_opa = 0 if missing(nonrheum_opa)

*---------------------------------------------------------------
* Compute mean visits per patient
*---------------------------------------------------------------
gen double mean_all_opa = .
gen double mean_rheum_opa = .
gen double mean_nonrheum_opa = .

replace mean_all_opa = all_opa / patient_count if patient_count > 0
replace mean_rheum_opa = rheum_opa / patient_count if patient_count > 0
replace mean_nonrheum_opa = nonrheum_opa / patient_count if patient_count > 0

* Scale to per 1,000 patients
gen double mean_all_opa_per1000      = mean_all_opa * 1000
gen double mean_rheum_opa_per1000    = mean_rheum_opa * 1000
gen double mean_nonrheum_opa_per1000 = mean_nonrheum_opa * 1000

*---------------------------------------------------------------
* Format date axis
*---------------------------------------------------------------
format period_date %tdDDMonCCYY

*---------------------------------------------------------------
* COVID restriction periods (UK national)
*---------------------------------------------------------------
local lock1_start = daily("2020-03-23","YMD")
local lock1_end   = daily("2020-07-04","YMD")

local lock2_start = daily("2020-11-05","YMD")
local lock2_end   = daily("2020-12-02","YMD")

local lock3_start = daily("2021-01-06","YMD")
local lock3_end   = daily("2021-03-29","YMD")

*---------------------------------------------------------------
* Define vertical range for shading
*---------------------------------------------------------------
egen ymax = rowmax(mean_all_opa_per1000 ///
                   mean_rheum_opa_per1000 ///
                   mean_nonrheum_opa_per1000)

gen ymin = 0

*---------------------------------------------------------------
* Plot with shaded COVID periods
*---------------------------------------------------------------
twoway ///
    /* COVID restriction shading */ ///
    (rarea ymin ymax period_date if inrange(period_date, `lock1_start', `lock1_end'), ///
        color(black%70) lwidth(none)) ///
    (rarea ymin ymax period_date if inrange(period_date, `lock2_start', `lock2_end'), ///
        color(black%70) lwidth(none)) ///
    (rarea ymin ymax period_date if inrange(period_date, `lock3_start', `lock3_end'), ///
        color(black%70) lwidth(none)) ///
    ///
    /* Mean visit lines */ ///
    (line mean_all_opa_per1000 period_date,       sort lcolor(blue)  lwidth(medium)) ///
    (line mean_rheum_opa_per1000 period_date,     sort lcolor(red)   lpatt(dash) lwidth(medium)) ///
    (line mean_nonrheum_opa_per1000 period_date,  sort lcolor(green) lpatt(dash) lwidth(medium)) ///
    , ///
    title("Mean outpatient visits per 1,000 patients over time") ///
    subtitle("Shaded regions indicate UK COVID-19 restriction periods") ///
    xtitle("Month") ///
    ytitle("Visits per 1,000 patients") ///
    legend(order(4 "All OPA" 5 "Rheum OPA" 6 "Non-rheum OPA") position(6) rows(1)) ///
    graphregion(margin(r+3)) ///
    name(g_overall, replace)

graph export "$figdir/all_opa_mean_per1000.png", ///
    name(g_overall) replace width(1600)

restore


*===============================================================
*PLOT 3: BAR GRAPH - Pre-PIFU post PIFU - visits per 1,000 patients
*==============================================================
preserve

* Keep only the two before/after PIFU measures
keep if inlist(measure, ///
    "count_all_opa_pre_pifu", ///
    "count_all_opa_post_pifu")

* ------------------------------------------------------------------
* CRITICAL STEP: sum visits and patient-months BEFORE dividing
* ------------------------------------------------------------------
collapse (sum) numerator_num denominator_num, by(measure)

* Compute mean visits per patient per month (visits per patient-month)
gen double rate_ppm = numerator_num / denominator_num

* Convert to per 1,000 patients (per month)
gen double rate_per1000 = rate_ppm * 1000

* Create readable labels
gen str10 phase = ""
replace phase = "Pre-PIFU"  if measure == "count_all_opa_pre_pifu"
replace phase = "Post-PIFU" if measure == "count_all_opa_post_pifu"

* ------------------------------------------------------------------
* Final bar chart (both bars in one plot) - per 1,000 patients per month
* ------------------------------------------------------------------
graph bar rate_per1000, ///
    over(phase, label(angle(0))) ///
    ytitle("Mean outpatient visits per 1,000 patients per month") ///
    title("Outpatient visit rates before and after first PIFU") ///
    blabel(bar, format(%4.2f)) ///
    bar(1, lcolor(none)) ///
    name(g_pifu_prepost_per1000, replace)

* Export
graph export "$figdir/pifu_prepost_bar_per1000.png", ///
    name(g_pifu_prepost_per1000) replace width(1600)

restore

*===============================================================
*PLOT 7: ALL OPAs  plot by sex
*==============================================================
preserve

* --- Prepare data ---
keep if measure == "count_all_opa_by_sex"

gen double cnt = numerator_num
collapse (sum) cnt, by(period_date sex)

* Build Male / Female series (case-insensitive)
bysort period_date: egen male_cnt   = total(cond(lower(sex)=="male", cnt, .))
bysort period_date: egen female_cnt = total(cond(lower(sex)=="female", cnt, .))

* Keep one row per period_date
bysort period_date: keep if _n == 1

format period_date %tdDDMonCCYY

* --- Plot: Male vs Female ---
twoway ///
    (line male_cnt   period_date, sort lcolor(blue) lwidth(medium)) ///
    (line female_cnt period_date, sort lcolor(red)  lwidth(medium) lpatt(dash)) ///
    , ///
    title("Total outpatient visits over time — by sex") ///
    xtitle("Time period") ///
    ytitle("Number of outpatient visits") ///
    legend(order(1 "Male" 2 "Female") position(6) ring(0.5)) ///
    graphregion(margin(r+3)) ///
    name(g_sex, replace)

graph export "$figdir/all_opa_by_sex.png", name(g_sex) replace width(1600)

restore


*===============================================================
*PLOT 8: ALL OPAs plot by PIFU and sex
*==============================================================
preserve

* --- choose the combined measure that contains pfu and sex breakdown ---
keep if measure == "count_all_opa_by_pfu_sex"

* check categories quickly (optional)
tab pfu_group sex, missing

* numeric count
gen double cnt = numerator_num

* collapse to one obs per period_date × pfu_group × sex
collapse (sum) cnt, by(period_date pfu_group sex)

* create the four series using case-insensitive matching of text values
bysort period_date: egen pifu_female    = total(cond(lower(pfu_group)=="pfu" & regexm(lower(sex),"^f"), cnt, .))
bysort period_date: egen nonpifu_female = total(cond(lower(pfu_group)!="pfu" & regexm(lower(sex),"^f"), cnt, .))
bysort period_date: egen pifu_male      = total(cond(lower(pfu_group)=="pfu" & regexm(lower(sex),"^m"), cnt, .))
bysort period_date: egen nonpifu_male   = total(cond(lower(pfu_group)!="pfu" & regexm(lower(sex),"^m"), cnt, .))

* keep one row per period_date for plotting
bysort period_date: keep if _n==1

* optional: replace missing with 0 so lines show zeros instead of gaps
foreach v in pifu_female nonpifu_female pifu_male nonpifu_male {
    replace `v' = 0 if missing(`v')
}

* ---- Plot: 4 lines (PIFU/Non-PIFU by Sex) ----
twoway ///
    (line pifu_male    period_date, sort lcolor(blue)   lwidth(medium) lpatt(solid)) ///
    (line nonpifu_male period_date, sort lcolor(blue)   lwidth(medium) lpatt(dash))  ///
    (line pifu_female  period_date, sort lcolor(red)    lwidth(medium) lpatt(solid)) ///
    (line nonpifu_female period_date, sort lcolor(red)  lwidth(medium) lpatt(dash)) ///
    , ///
    title("Total outpatient visits — PIFU vs Non-PIFU, by Sex") ///
    xtitle("Time period") ytitle("Number of outpatient visits") ///
    legend(order(1 "PIFU — Male" 2 "Non-PIFU — Male" 3 "PIFU — Female" 4 "Non-PIFU — Female") ///
           cols (2) ring(1) pos(6)) ///
		    graphregion(margin(r+3)) ///
    name(g_pifu_sex_4line, replace)

graph export "$figdir/all_opa_by_pfu_sex_4line.png", name(g_pifu_sex_4line) replace width(1600)

restore

*====================================================
*PLOT 9: ALL OPAS PLOT By Diagnosis category: Rheumatoid, pSa, AxSpa, undiff
*=====================================================
preserve

* keep only the diag-category measure and exclude missing category values
keep if measure == "count_all_opa_by_latest_diag_category"
drop if missing(diag_category)   // comment out if you want to include missing as a series

* ensure numeric count exists
gen double cnt = numerator_num

* collapse to one observation per period_date x diag_category (sum counts)
collapse (sum) cnt, by(period_date diag_category)

* Create a safe cleaned category name for reshaping (lowercase, no spaces/slashes/etc.)
gen str cleaned = diag_category
replace cleaned = lower(cleaned)
replace cleaned = subinstr(cleaned, " ", "_", .)
replace cleaned = subinstr(cleaned, "/", "_", .)
replace cleaned = subinstr(cleaned, "-", "_", .)
replace cleaned = subinstr(cleaned, ".", "_", .)
replace cleaned = subinstr(cleaned, "(", "", .)
replace cleaned = subinstr(cleaned, ")", "", .)

* collapse again in case cleaned merged duplicates
collapse (sum) cnt, by(period_date cleaned)

* reshape wide so each category becomes its own column (cnt<cleaned>)
reshape wide cnt, i(period_date) j(cleaned) string


* labels for legend
label variable cntrheumatoid "Rheumatoid"
label variable cntpsa        "Psoriatic"
label variable cntaxialspa   "Axial spondyloarthritis"
label variable cntundiff_eia "Undifferentiated"



* Build a list of cnt* variables (the newly-created columns)
ds cnt*, has(type numeric)
local cats `r(varlist)'

* Diagnosics: If no categories found, stop and share this message
if "`cats'" == "" {
    di as err "No diag_category columns found for plotting — check data."
    restore
    exit 1
}

* Build the twoway plot list: (line var period_date, sort lwidth(medium))
local plots ""
local first 1
foreach v of local cats {
    if `first' {
        local plots "(line `v' period_date, sort lwidth(medium))"
        local first 0
    }
    else {
        local plots "`plots' (line `v' period_date, sort lwidth(medium))"
    }
}

* Final twoway call
twoway `plots', ///
    title("Total outpatient visits over time — by diagnosis category") ///
    xtitle("Time period") ytitle("Number of outpatient visits") ///
    legend(cols (2) ring(1) pos(6)) ///
	graphregion(margin(r+3)) ///
    name(g_diag, replace)

* Export PNG to your figure directory
graph export "$figdir/all_opa_by_diag_category.png", name(g_diag) replace width(1600)

restore

*====================================================
*PLOT 10: ALL OPAS PLOT By Ethnicity
*=====================================================
preserve

* 1) Keep only the ethnicity measure
keep if measure == "count_all_opa_by_ethnicity"

* 2) Drop missing ethnicity (comment out if you want to keep it)
drop if missing(ethnicity)

* 3) Ensure numeric count exists
gen double cnt = numerator_num

* 4) Collapse to one obs per period_date × ethnicity
collapse (sum) cnt, by(period_date ethnicity)

* 5) Create safe cleaned ethnicity names
gen str cleaned = ethnicity
replace cleaned = lower(cleaned)
replace cleaned = subinstr(cleaned, " ", "_", .)
replace cleaned = subinstr(cleaned, "/", "_", .)
replace cleaned = subinstr(cleaned, "-", "_", .)
replace cleaned = subinstr(cleaned, ".", "_", .)
replace cleaned = subinstr(cleaned, "(", "", .)
replace cleaned = subinstr(cleaned, ")", "", .)

* 6) Collapse again in case cleaning merged categories
collapse (sum) cnt, by(period_date cleaned)


* map long cleaned names to short names
replace cleaned = "asian" if cleaned == "asian_or_asian_british"
replace cleaned = "black" if cleaned == "black_or_black_british"
replace cleaned = "chinese_other" if cleaned == "chinese_or_other_ethnic_groups"
replace cleaned = "mixed" if cleaned == "mixed"
replace cleaned = "unknown" if cleaned == "unknown"
replace cleaned = "white" if cleaned == "white"

* confirm names are short enough
list cleaned

* 7) Reshape wide: one column per ethnicity
reshape wide cnt, i(period_date) j(cleaned) string

* 8) Label variables for legend (adjust if needed)
label variable cntasian     "Asian or Asian British"
label variable cntblack    "Black or Black British"
label variable cntchinese_other ///
                                             "Chinese or Other Ethnic Groups"
label variable cntmixed                      "Mixed"
label variable cntunknown                    "Unknown"
label variable cntwhite                      "White"

* 9) Build list of ethnicity series
ds cnt*, has(type numeric)
local cats `r(varlist)'


*Diagnistics: * If no categories found, stop and share this message
if "`cats'" == "" {
    di as err "No ethnicity columns found — check data."
    restore
    exit 1
}

* 10) Build plot commands
local plots ""
local first 1
foreach v of local cats {
    if `first' {
        local plots "(line `v' period_date, sort lwidth(medium))"
        local first 0
    }
    else {
        local plots "`plots' (line `v' period_date, sort lwidth(medium))"
    }
}

* 11) Draw plot
twoway `plots', ///
    title("Total outpatient visits over time — by ethnicity") ///
    xtitle("Time period") ///
    ytitle("Number of outpatient visits") ///
    legend(cols(2) ring(1) pos(6)) ///
    graphregion(margin(r+3)) ///
    name(g_eth, replace)

* 12) Export
graph export "$figdir/all_opa_by_ethnicity.png", ///
    name(g_eth) replace width(1600)

restore

*====================================================
*PLOT 11: ALL OPAS PLOT By IMD 
*=====================================================
preserve

* 1) Keep only the IMD measure
keep if measure == "count_all_opa_by_imd"
drop if missing(imd_quintile) | lower(trim(imd_quintile)) == "unknown"

* 2) Optionally drop missing IMD categories (comment out to keep missing)
drop if missing(imd_quintile)

* 3) Ensure numeric count exists
gen double cnt = numerator_num

* 4) Collapse to one obs per period_date × imd_quintile (sum counts)
collapse (sum) cnt, by(period_date imd_quintile)

* 5) Create a short safe name for imd_quintile to use in reshape
* We'll map to: imd1 .. imd5, imd_unknown (these are short and safe)
gen str cleaned = lower(trim(imd_quintile))

replace cleaned = "imd1"         if cleaned == "1 (most deprived)" | cleaned == "1" | cleaned == "1 (most deprived) "
replace cleaned = "imd2"         if cleaned == "2" 
replace cleaned = "imd3"         if cleaned == "3"
replace cleaned = "imd4"         if cleaned == "4"
replace cleaned = "imd5"         if cleaned == "5 (least deprived)" | cleaned == "5"


* If your imd_quintile has slightly different labels, you can add more replace lines above.
* Confirm mapping:
tab cleaned, missing

* 6) Collapse again in case mapping merged duplicates
collapse (sum) cnt, by(period_date cleaned)

* 7) Reshape wide so each IMD becomes its own column (cnt<cleaned>)
reshape wide cnt, i(period_date) j(cleaned) string

* 8) Label the cnt* variables for nicer legend entries (adjust if any names differ)
cap label variable cntimd1        "IMD 1(most deprived)"
cap label variable cntimd2        "IMD 2"
cap label variable cntimd3        "IMD 3"
cap label variable cntimd4        "IMD 4"
cap label variable cntimd5        "IMD 5(least deprived)"


* 9) Build the list of cnt* variables to plot
ds cnt*, has(type numeric)
local cats `r(varlist)'

if "`cats'" == "" {
    di as err "No IMD columns found for plotting — check data and cleaned mapping."
    restore
    exit 1
}

* 10) Build twoway plot list: one line per IMD group
local plots ""
local first 1
foreach v of local cats {
    if `first' {
        local plots "(line `v' period_date, sort lwidth(medium))"
        local first 0
    }
    else {
        local plots "`plots' (line `v' period_date, sort lwidth(medium))"
    }
}

* 11) Draw the twoway
twoway `plots', ///
    title("Total outpatient visits over time — by IMD quintile") ///
    xtitle("Time period") ///
    ytitle("Number of outpatient visits") ///
    legend(rows(2) ring(1) pos(6)) ///
    graphregion(margin(r+3)) ///
    name(g_imd, replace)

* 12) Export PNG
graph export "$figdir/all_opa_by_imd.png", name(g_imd) replace width(1600)

restore


*====================================================
*PLOT 12: ALL OPAS PLOT By Rural/Urban
*=====================================================



****
PLOT 10: Ethinicity
IMD 
work on medication and steriods
comorbidities 




