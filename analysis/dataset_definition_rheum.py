####################################################################
# This code extracts all people who had a rheumatology outpatient visit
####################################################################


from ehrql import create_dataset, case, when, years, days, weeks, show
from ehrql.tables.tpp import patients, ethnicity_from_sus, practice_registrations, clinical_events, opa, addresses
#from cohortextractor import StudyDefinition, patients, codelist, codelist_from_csv, combine_codelists, filter_codes_by_category


dataset = create_dataset()
dataset.configure_dummy_data(population_size=1000)


# rheumatology outpatient visits - to measure before / after start of personalised follow-up
all_opa = opa.where(
        opa.appointment_date.is_on_or_after("2018-06-01")
        & opa.treatment_function_code.is_in(["410"])
        & opa.attendance_status.is_in(["5","6"])
    )

# pfu only
pfu_only = all_opa.where(
        all_opa.outcome_of_attendance.is_in(["4","5"])
        & all_opa.appointment_date.is_on_or_after("2022-06-01")
    )

from analysis.variable_functions import opa_characteristics

from analysis.codelists import (
    ethnicity_codelist, language_codelist, bmi_codelist, 
    rheumatoid_snomed_codelist, rheumatoid_icd10_codelist,
    psa_snomed_codelist, psa_icd10_codelist,
    axialspa_snomed_codelist, axialspa_icd10_codelist,
    undiff_eia_codelist
)


dataset = opa_characteristics(dataset, all_opa, pfu_only)

#######################################################
#DEMOGRAPHICS
#######################################################

# define population - everyone with a rheum outpatient visit
#This defines the inclusion criteria - These are defined in variable_functions.py
#Age, sex (female/Male),date of death, practice registrations 
dataset.define_population(
    (dataset.age_opa >= 18) 
    #(dataset.age >= 0)
    & (dataset.age_opa < 110) 
    & ((dataset.sex == "male") | (dataset.sex == "female"))
    & (patients.date_of_death.is_after(dataset.first_opa_date) | patients.date_of_death.is_null())
    & (practice_registrations.for_patient_on(dataset.first_opa_date).exists_for_patient())
    & dataset.first_opa_date.is_not_null()
)

#Ethnicity-----------------------------------------
 # Define patient ethnicity
latest_ethnicity_code = (
        clinical_events.where(clinical_events.snomedct_code.is_in(ethnicity_codelist))
        .where(clinical_events.date.is_on_or_before(dataset.first_opa_date))
        .sort_by(clinical_events.date)
        .last_for_patient().snomedct_code.to_category(ethnicity_codelist)
    )

  # Extract ethnicity from SUS records if it isn't present in primary care data 
ethnicity_sus = ethnicity_from_sus.code

dataset.ethnicity = case(
        when((latest_ethnicity_code == "1") | ((latest_ethnicity_code.is_null()) & (ethnicity_sus.is_in(["A", "B", "C"])))).then("White"),
        when((latest_ethnicity_code == "2") | ((latest_ethnicity_code.is_null()) & (ethnicity_sus.is_in(["D", "E", "F", "G"])))).then("Mixed"),
        when((latest_ethnicity_code == "3") | ((latest_ethnicity_code.is_null()) & (ethnicity_sus.is_in(["H", "J", "K", "L"])))).then("Asian or Asian British"),
        when((latest_ethnicity_code == "4") | ((latest_ethnicity_code.is_null()) & (ethnicity_sus.is_in(["M", "N", "P"])))).then("Black or Black British"),
        when((latest_ethnicity_code == "5") | ((latest_ethnicity_code.is_null()) & (ethnicity_sus.is_in(["R", "S"])))).then("Chinese or Other Ethnic Groups"),
        otherwise="Unknown", 
    ) 


# BMI recorded (flag)-F/T----------------------------------
# any BMI measurement on/before first_opa_date
bmi_codes = clinical_events.where(
    clinical_events.snomedct_code.is_in(bmi_codelist)
    & clinical_events.date.is_on_or_before(dataset.first_opa_date)
)
dataset.bmi_recorded = bmi_codes.exists_for_patient()


# Preferred language--------------------------------
preflang_codes = clinical_events.where(
    clinical_events.snomedct_code.is_in(language_codelist)
    & clinical_events.date.is_on_or_before(dataset.first_opa_date)
)

dataset.language_code = (

    preflang_codes.sort_by(preflang_codes.date)
    .last_for_patient()
    .snomedct_code
    .to_category(language_codelist)
)


#IMD
#Source: https://docs.opensafely.org/ehrql/reference/schemas/tpp/

# 1) get the last address record on or before the anchor (first_opa_date)
last_address = (
    addresses
    .where(addresses.start_date.is_on_or_before(dataset.first_opa_date))
    .sort_by(addresses.start_date)
    .last_for_patient()
)

# pull the rounded IMD value from that last address (one value per patient)
imd_last = last_address.imd_rounded

# 2) create imd quintile (numeric) using the same fixed cutpoints (England LSOA count = 32844)
dataset.index_of_multiple_deprivation = imd_last

dataset.imd_quintile = case(
    # Although the lowest IMD rank is 1, we need to check >= 0 because
    # we're using the imd_rounded field rather than the actual imd
    when((imd_last >= 0) & (imd_last <= int(32844 * 1 / 5))).then("1 (most deprived)"),
    when(imd_last <= int(32844 * 2 / 5)).then("2"),
    when(imd_last <= int(32844 * 3 / 5)).then("3"),
    when(imd_last <= int(32844 * 4 / 5)).then("4"),
    when(imd_last <= int(32844 * 5 / 5)).then("5 (least deprived)"),
    otherwise="unknown",
)