* rheum_table3.do
* Produce Table 3: Rheumatology PFU patients since 1 Jun 2018

*------------------------------------------------------------
* Import dataset and keep PFU patients
*------------------------------------------------------------
import delimited using "output/dataset_rheum.csv", clear
keep if (any_pfu == "T" | any_pfu == "True" | any_pfu == "1") ///
    & first_pfu_date >= "2018-06-01"

* Overall total
count
local total = r(N)

* Start results dataset
clear
set obs 1
gen subgroup = "Total"
gen category = "All patients"
gen count = `total'
gen percent = 100 * count / `total'
gen formatted = string(count, "%9.0f") + " (" + string(percent, "%4.1f") + "%)"
tempfile results
save "`results'"

*------------------------------------------------------------
* 1. Counts by sex
import delimited using "output/dataset_rheum.csv", clear
keep if (any_pfu == "T" | any_pfu == "True" | any_pfu == "1") ///
    & first_pfu_date >= "2018-06-01"
contract sex, freq(count)
gen subgroup = "Sex"
rename sex category
gen percent = 100 * count / `total'
gen formatted = string(count, "%9.0f") + " (" + string(percent, "%4.1f") + "%)"
append using "`results'"
save "`results'", replace

*------------------------------------------------------------
* 2. Counts by age group
import delimited using "output/dataset_rheum.csv", clear
keep if (any_pfu == "T" | any_pfu == "True" | any_pfu == "1") ///
    & first_pfu_date >= "2018-06-01"
contract age_group, freq(count)
gen subgroup = "Age group"
rename age_group category
gen percent = 100 * count / `total'
gen formatted = string(count, "%9.0f") + " (" + string(percent, "%4.1f") + "%)"
append using "`results'"
save "`results'", replace

*------------------------------------------------------------
* 3. Counts by region
import delimited using "output/dataset_rheum.csv", clear
keep if (any_pfu == "T" | any_pfu == "True" | any_pfu == "1") ///
    & first_pfu_date >= "2018-06-01"
replace region = "Missing" if region == ""
contract region, freq(count)
gen subgroup = "Region"
rename region category
gen percent = 100 * count / `total'
gen formatted = string(count, "%9.0f") + " (" + string(percent, "%4.1f") + "%)"
append using "`results'"
save "`results'", replace

*------------------------------------------------------------
* 4. Counts by year of first PFU
import delimited using "output/dataset_rheum.csv", clear
keep if (any_pfu == "T" | any_pfu == "True" | any_pfu == "1") ///
    & first_pfu_date >= "2018-06-01"
contract first_pfu_year, freq(count)
gen subgroup = "First PFU year"
tostring first_pfu_year, replace   // ensure string
rename first_pfu_year category
gen percent = 100 * count / `total'
gen formatted = string(count, "%9.0f") + " (" + string(percent, "%4.1f") + "%)"
append using "`results'"
save "`results'", replace

*------------------------------------------------------------
* 5. Attendances 1 year before PFU
import delimited using "output/dataset_rheum.csv", clear
keep if (any_pfu == "T" | any_pfu == "True" | any_pfu == "1") ///
    & first_pfu_date >= "2018-06-01"

* ≥1 attendance in year before
gen att1 = (before_1yr >= 1)
summarize att1
local prop1 = 100 * r(mean)

clear
set obs 1
gen subgroup = "Attendances 1yr before PFU"
gen category = "1+ attendance"
gen count = round(`prop1' * `total'/100, 5)
gen percent = `prop1'
gen formatted = string(count, "%9.0f") + " (" + string(percent, "%4.1f") + "%)"
tempfile attend1
save "`attend1'"

* Median (IQR) attendances
import delimited using "output/dataset_rheum.csv", clear
keep if (any_pfu == "T" | any_pfu == "True" | any_pfu == "1") ///
    & first_pfu_date >= "2018-06-01"
summarize before_1yr, detail
local median1 = r(p50)
local iqr1l = r(p25)
local iqr1u = r(p75)

clear
set obs 1
gen subgroup = "Attendances 1yr before PFU"
gen category = "No. attendances (median [IQR])"
gen count = .
gen formatted = "`median1' (" + string(`iqr1l',"%9.0f") + "-" + string(`iqr1u',"%9.0f") + ")"
append using "`attend1'"
append using "`results'"
save "`results'", replace

*------------------------------------------------------------
* 6. Attendances 2 years before PFU
import delimited using "output/dataset_rheum.csv", clear
keep if (any_pfu == "T" | any_pfu == "True" | any_pfu == "1") ///
    & first_pfu_date >= "2018-06-01"

* ≥1 attendance in 2 years before
gen att2 = (before_2yr >= 1)
summarize att2
local prop2 = 100 * r(mean)

clear
set obs 1
gen subgroup = "Attendances 2yr before PFU"
gen category = "1+ attendance"
gen count = round(`prop2' * `total'/100, 5)
gen percent = `prop2'
gen formatted = string(count, "%9.0f") + " (" + string(percent, "%4.1f") + "%)"
tempfile attend2
save "`attend2'"

* Median (IQR) attendances
import delimited using "output/dataset_rheum.csv", clear
keep if (any_pfu == "T" | any_pfu == "True" | any_pfu == "1") ///
    & first_pfu_date >= "2018-06-01"
summarize before_2yr, detail
local median2 = r(p50)
local iqr2l = r(p25)
local iqr2u = r(p75)

clear
set obs 1
gen subgroup = "Attendances 2yr before PFU"
gen category = "No. attendances (median [IQR])"
gen count = .
gen formatted = "`median2' (" + string(`iqr2l',"%9.0f") + "-" + string(`iqr2u',"%9.0f") + ")"
append using "`attend2'"
append using "`results'"
save "`results'", replace

*------------------------------------------------------------
* 7. Round counts (disclosure control)
use "`results'", clear
replace count = round(count, 5) if count < .

*------------------------------------------------------------
* 8. Keep clean variables for output
keep subgroup category formatted

*------------------------------------------------------------
* 9. Export final table
export delimited using "output/processed/rheum_table3.csv", replace
