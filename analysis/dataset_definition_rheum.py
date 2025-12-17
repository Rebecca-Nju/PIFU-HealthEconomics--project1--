####################################################################
# This code extracts all people who had a rheumatology outpatient visit

####################################################################

from ehrql import create_dataset, case, when, years, days, weeks, show, minimum_of
from ehrql.tables.tpp import patients, ethnicity_from_sus, practice_registrations, clinical_events, apcs, opa, addresses, ons_deaths
#from cohortextractor import StudyDefinition, patients, codelist, codelist_from_csv, combine_codelists, filter_codes_by_category

dataset = create_dataset()
dataset.configure_dummy_data(population_size=2000)


#from analysis.variable_functions import opa_characteristics

from analysis.codelists import (
    ethnicity_codelist,
    language_codelist,
    learning_disability_codelist,
    bmi_codelist,
    rheumatoid_snomed_codelist,
    rheumatoid_icd10_codelist,
    psa_snomed_codelist,
    psa_icd10_codelist,
    axialspa_snomed_codelist,
    axialspa_icd10_codelist,
    undiff_eia_codelist,
    eia_snomed_codelist,
    eia_icd10_codelist,
    eia_snomed_categories,
)

#DIAGNOSIS: DISEASE TYPE AND DURATIION OF DIAGNOSIS BEFORE FIRST RHEUM VISIT
#Most recent diagnosis
#SNOMED diagnosis have actual event dates (clinical_events.date)
#ICD-10 has admission/discharge dates:https://docs.opensafely.org/ehrql/reference/schemas/tpp/#apcs
#----------------------------------------------------------------------------

# --- Latest GP (SNOMED) diagnosis (most recent ever) ---
latest_gp_diag = (
    clinical_events
    .where(clinical_events.snomedct_code.is_in(eia_snomed_codelist))
    .sort_by(clinical_events.date)
    .last_for_patient()
)

dataset.latest_gp_diag_date = latest_gp_diag.date
dataset.latest_gp_diag_code = latest_gp_diag.snomedct_code

# Map SNOMED -> category via your mapping
code_to_category = {
    code: cat
    for cat, codes in eia_snomed_categories.items()
    for code in codes
}
dataset.latest_gp_diag_cat = latest_gp_diag.snomedct_code.to_category(code_to_category)


# --- Latest APC (ICD-10) diagnosis (most recent ever) ---
latest_apc_diag = (
    apcs
    .where(
        apcs.primary_diagnosis.is_in(eia_icd10_codelist)
        | apcs.secondary_diagnosis.is_in(eia_icd10_codelist)
        | apcs.all_diagnoses.contains_any_of(eia_icd10_codelist)
    )
    .sort_by(apcs.admission_date)
    .last_for_patient()
)

dataset.latest_apc_diag_date = latest_apc_diag.admission_date   # APC gives admission_date
dataset.latest_apc_diag_all = latest_apc_diag.all_diagnoses

# single-code ICD10 if available (keeps ICD10Code type)
dataset.latest_apc_diag_code = case(
    when(latest_apc_diag.primary_diagnosis.is_not_null()).then(latest_apc_diag.primary_diagnosis),
    when(latest_apc_diag.secondary_diagnosis.is_not_null()).then(latest_apc_diag.secondary_diagnosis),
    otherwise=None,
)

# APC category derived from all_diagnoses text (may be NULL)
dataset.latest_apc_diag_cat = case(
    when(latest_apc_diag.all_diagnoses.contains_any_of(rheumatoid_icd10_codelist)).then("rheumatoid"),
    when(latest_apc_diag.all_diagnoses.contains_any_of(psa_icd10_codelist)).then("psa"),
    when(latest_apc_diag.all_diagnoses.contains_any_of(axialspa_icd10_codelist)).then("axialspa"),
    otherwise=None,
)


# --- Choose the single LATEST DATE between GP and APC and give a source flag ---
dataset.latest_diag_date = case(
    when(dataset.latest_gp_diag_date.is_not_null() & dataset.latest_apc_diag_date.is_not_null() & (dataset.latest_gp_diag_date >= dataset.latest_apc_diag_date)).then(dataset.latest_gp_diag_date),
    when(dataset.latest_gp_diag_date.is_not_null() & dataset.latest_apc_diag_date.is_not_null() & (dataset.latest_apc_diag_date > dataset.latest_gp_diag_date)).then(dataset.latest_apc_diag_date),
    when(dataset.latest_gp_diag_date.is_not_null()).then(dataset.latest_gp_diag_date),
    when(dataset.latest_apc_diag_date.is_not_null()).then(dataset.latest_apc_diag_date),
    otherwise=None,
)

dataset.latest_diag_source = case(
    when(dataset.latest_diag_date == dataset.latest_gp_diag_date).then("primary_care"),
    when(dataset.latest_diag_date == dataset.latest_apc_diag_date).then("secondary_care"),
    otherwise=None,
)

# presence flag (based on date)
dataset.has_any_diagnosis = dataset.latest_diag_date.is_not_null()

## --- Derive a single category (string) from whichever source was chosen ---
dataset.latest_diag_category = case(
    when(dataset.latest_diag_source == "primary_care").then(dataset.latest_gp_diag_cat),
    when(dataset.latest_diag_source == "secondary_care").then(dataset.latest_apc_diag_cat),
    otherwise=None,
)

latest_diag_category  = dataset.latest_diag_category

# boolean flags for convenience (derived from the single string category)
dataset.rheumatoid = (dataset.latest_diag_category == "rheumatoid")
dataset.psa = (dataset.latest_diag_category == "psa")
dataset.axialspa = (dataset.latest_diag_category == "axialspa")
dataset.undiffia = (dataset.latest_diag_category == "undiffia")


# =======================================================================
# All patients with a rheumatology outpatient visit  (treatment code 410)
# =======================================================================
all_rheum_opa = opa.where(
        opa.appointment_date.is_on_or_after("2018-01-01")
        & opa.treatment_function_code.is_in(["410"])
       # & opa.attendance_status.is_in(["5","6"]) ## Add back non-attendees
    )

first_rheum = (
    all_rheum_opa
    .sort_by(all_rheum_opa.appointment_date)
    .first_for_patient()
)

dataset.first_rheum_date = first_rheum.appointment_date



#COVID PHASES
dataset.covid_phase = case(
    when(dataset.first_rheum_date.is_on_or_before("2019-12-31")).then("pre"),
    when(
        (dataset.first_rheum_date.is_on_or_after("2020-01-01"))
        & (dataset.first_rheum_date.is_on_or_before("2021-12-31"))
    ).then("peri"),
    when(dataset.first_rheum_date.is_on_or_after("2022-01-01")).then("post"),
    otherwise=None,
)

# ======================================================
#  RHEUMATOLOGY Personalised Follow-up (PFU) VISITS (subset of rheum)
#4,5 - outcome of attendance moved & discharged to pfu
# ====================================================== 
rheum_pfu= all_rheum_opa.where(
        all_rheum_opa.outcome_of_attendance.is_in(["4","5"]) ### describe what this is in data disctionary 
       # & all_rheum_opa.appointment_date.is_on_or_after("2022-01-01") ## check if there are flags before 2022
    )

# First personalised follow-up appointment FOR RHEUMATOLOGY visit only
first_rheum_pfu = (
    rheum_pfu
    .sort_by(rheum_pfu.appointment_date)
    .first_for_patient()
)

dataset.first_rheum_pfu_date = first_rheum_pfu.appointment_date
dataset.any_rheum_pfu = dataset.first_rheum_pfu_date.is_not_null()
# ---------------------------
# NON-RHEUM outpatient visits (exclude treatment_function_code "410")
#Including only the count of non-rheumatology visits for now since 2018-01-01
# ---------------------------
all_non_rheum_opa = opa.where(
    opa.treatment_function_code.is_null()
    | (opa.treatment_function_code == "") #include if missing treatment code
    | (opa.treatment_function_code == " ")
    | (~opa.treatment_function_code.is_in(["410"]))
)

dataset.non_rheum_opa_any   = all_non_rheum_opa.exists_for_patient()
dataset.non_rheum_opa_count = all_non_rheum_opa.opa_ident.count_distinct_for_patient()
dataset.non_rheum_opa_first_date = all_non_rheum_opa.sort_by(all_non_rheum_opa.appointment_date).first_for_patient().appointment_date
dataset.non_rheum_opa_last_date  = all_non_rheum_opa.sort_by(all_non_rheum_opa.appointment_date).last_for_patient().appointment_date


#######################################################
#DEMOGRAPHICS
#######################################################
dataset.sex = patients.sex

dataset.age_rheum = patients.age_on(dataset.first_rheum_date)
dataset.age_rheum_group = case(
            when(dataset.age_rheum < 18).then("0-17"),
            when(dataset.age_rheum < 30).then("18-29"),
            when(dataset.age_rheum < 40).then("30-39"),
            when(dataset.age_rheum < 50).then("40-49"),
            when(dataset.age_rheum < 60).then("50-59"),
            when(dataset.age_rheum < 70).then("60-69"),
            when(dataset.age_rheum < 80).then("70-79"),
            when(dataset.age_rheum < 90).then("80-89"),
            when(dataset.age_rheum >= 90).then("90+"),
            otherwise="missing",
    )


dataset.age_rheum_pfu = patients.age_on(dataset.first_rheum_pfu_date)
dataset.age_rheum_pfu_group = case(
            when(dataset.age_rheum_pfu < 18).then("0-17"),
            when(dataset.age_rheum_pfu < 30).then("18-29"),
            when(dataset.age_rheum_pfu < 40).then("30-39"),
            when(dataset.age_rheum_pfu < 50).then("40-49"),
            when(dataset.age_rheum_pfu < 60).then("50-59"),
            when(dataset.age_rheum_pfu < 70).then("60-69"),
            when(dataset.age_rheum_pfu < 80).then("70-79"),
            when(dataset.age_rheum_pfu < 90).then("80-89"),
            when(dataset.age_rheum_pfu >= 90).then("90+"),
            otherwise="missing",
    )

dataset.region = practice_registrations.for_patient_on(dataset.first_rheum_date).practice_nuts1_region_name
region=dataset.region ## done this to import to measures.py file easily

dataset.deregister_date = practice_registrations.for_patient_on(dataset.first_rheum_date).end_date
dataset.tpp_dod = patients.date_of_death
dataset.ons_dod = ons_deaths.date
dataset.dod = minimum_of(dataset.tpp_dod, dataset.ons_dod)
dataset.fu_days = (minimum_of(dataset.dod, dataset.deregister_date, "2026-12-31") - dataset.first_rheum_pfu_date).days

# define population - everyone with a rheum outpatient visit
#This defines the inclusion criteria 
#Age, sex (female/Male),date of death, practice registrations 
dataset.define_population(
    (dataset.age_rheum >= 18) #use most recent visit
    #(dataset.age >= 0)
    #& (dataset.age_opa < 110) 
   # & ((dataset.sex == "male") | (dataset.sex == "female")) #use if restricting to male/female
    & (patients.date_of_death.is_after(dataset.first_rheum_date) | patients.date_of_death.is_null())
    & (practice_registrations.for_patient_on(dataset.first_rheum_date).exists_for_patient())
    & dataset.first_rheum_date.is_not_null()
)

#Ethnicity-----------------------------------------
 # Define patient ethnicity
latest_ethnicity_code = (
        clinical_events.where(clinical_events.snomedct_code.is_in(ethnicity_codelist))
        .where(clinical_events.date.is_on_or_before(dataset.first_rheum_date))
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

ethnicity=dataset.ethnicity

# Preferred language--------------------------------
preflang_codes = clinical_events.where(
    clinical_events.snomedct_code.is_in(language_codelist)
    & clinical_events.date.is_on_or_before(dataset.first_rheum_date)
)

# Flag: any language code on/before first_opa_date
dataset.language_flag = preflang_codes.exists_for_patient()
# Latest language event (local variable)
latest_lang = preflang_codes.sort_by(preflang_codes.date).last_for_patient()
# Raw SNOMED code
dataset.language_code_raw = latest_lang.snomedct_code
# Category (mapped from codelist 'term' column)
dataset.language_category = latest_lang.snomedct_code.to_category(language_codelist)
# Date of the latest language record
dataset.language_date = latest_lang.date

#Learning disabilities
learningdis_codes = clinical_events.where(
    clinical_events.snomedct_code.is_in(learning_disability_codelist)
    & clinical_events.date.is_on_or_before(dataset.first_rheum_date)
)

# Flag: any LD recorded
dataset.learning_disability_flag = learningdis_codes.exists_for_patient()
# Latest LD recorded
latest_ld = learningdis_codes.sort_by(learningdis_codes.date).last_for_patient()
# Raw SNOMED code (series)
dataset.learning_disability_code = latest_ld.snomedct_code
# Category (uses the 'term' column from the codelist)
dataset.learning_disability_category = latest_ld.snomedct_code.to_category(learning_disability_codelist)
#LD latest dates recorded
dataset.learning_disability_date = latest_ld.date

# dementia ### RDCI

#-------------------------------
#Socio-economic status
#-------------------------------
#IMD
#Source: https://docs.opensafely.org/ehrql/reference/schemas/tpp/   #check why IMD is missing - one option is to use GP adress###################

# 1) get the last address record on or before the anchor (first_opa_date)
last_address = (
    addresses
    .where(addresses.start_date.is_on_or_before(dataset.first_rheum_date))
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

imd_quintile= dataset.imd_quintile
#-------------------------------
#Urban/Rural setting
#------------------------------- 
# get last address on or before the anchor date (same pattern as IMD)
last_address = (
    addresses
    .where(addresses.start_date.is_on_or_before(dataset.first_rheum_date))
    .sort_by(addresses.start_date)
    .last_for_patient()
)

dataset.rural_urban_classification  = last_address.rural_urban_classification
rural_urban_classification = dataset.rural_urban_classification   


#Co-morbidity burden
#Treatment
#DMARD use
#Steroid use
# 

