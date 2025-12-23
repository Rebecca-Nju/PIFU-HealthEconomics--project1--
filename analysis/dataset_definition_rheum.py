####################################################################
#Purpose
#-------
#Create a person-level dataset of patients who had an outpatient (OPA) visit,
#with a focus on rheumatology (treatment_function_code "410") and related
#diagnostic and demographic derivations.

#What the script does (high level)
#--------------------------------
#- Identifies patients with inflammatory arthritis diagnoses (primary and/or secondary care)
#- Finds every patient's first outpatient appointment since 2018-01-01 and related dates/counts
#- Identifies rheumatology-specific OPAs and the first personalised follow-up (PFU/PIFU) appointment
#- Derives demographics and socio-economic stratifiers at the time of the first OPA
#- Exposes booleans and categorical fields that are convenient for downstream analyses
 # (e.g., import into the Measures pipeline)

#Notes 
#-------------------
#- SNOMED-coded diagnoses come from `clinical_events` (GP / primary care).
#- ICD-10-coded diagnoses come from `apcs` (secondary care / hospital admissions) and
 # admission_date is used as the diagnosis date for APCS events.
#- "First OPA" anchors many derived fields (age, region, registration status).



#Imports (ehrQl and modules )
from ehrql import create_dataset, case, when, years, days, weeks, show, minimum_of
from ehrql.tables.tpp import patients, medications, ethnicity_from_sus, practice_registrations, clinical_events, apcs, opa, addresses, ons_deaths

#from cohortextractor import StudyDefinition, patients, codelist, codelist_from_csv, combine_codelists, filter_codes_by_category


# Create dataset object and optional dummy data configuration (useful for local dev)
dataset = create_dataset()
dataset.configure_dummy_data(population_size=2000)

# Project-specific codelists (SNOMED/ICD mappings, ethnicity, language, etc.)
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
    DMARD_codelist,
    steroid_codelist,
)

# -------------------------------------------------------------------------
# DIAGNOSIS: identify patients with inflammatory arthritis (IA) diagnoses
# - SNOMED codes from primary care (clinical_events)
# - ICD-10 codes from secondary care (apcs)
# Combined boolean flag indicates diagnosis in either source (ever)
# -------------------------------------------------------------------------
has_gp_diagnosis = clinical_events.where(
    clinical_events.snomedct_code.is_in(eia_snomed_codelist)   
).exists_for_patient()

# Secondary care diagnosis (TPP APCS) - use primary, secondary, and all_diagnoses
#from here: https://docs.opensafely.org/ehrql/reference/schemas/tpp/#apcs
has_apcs_diagnosis = (
    apcs.where(apcs.primary_diagnosis.is_in(eia_icd10_codelist)).exists_for_patient()
    | apcs.where(apcs.secondary_diagnosis.is_in(eia_icd10_codelist)).exists_for_patient()
    | apcs.where(apcs.all_diagnoses.contains_any_of(eia_icd10_codelist)).exists_for_patient()
)

#combined
# Combined: diagnosis in either primary OR secondary care (ever)
dataset.has_any_diagnosis = has_gp_diagnosis | has_apcs_diagnosis


# -------------------------------------------------------------------------
# LATEST DIAGNOSIS - classify most recent diagnosis and derive a category
# Approach:
#  - get patient's most recent SNOMED event (GP) matching IA codes
#  - get patient's most recent APCS admission with any IA ICD10 in any diagnosis slot
#  - choose the later of the two dates as the patient's "latest diagnosis"
#  - record source ('primary_care' or 'secondary_care') and a single category string
# -------------------------------------------------------------------------
# Latest GP (SNOMED) diagnosis (primary care) - last event chronologically per patient
latest_gp_diag = (
    clinical_events
    .where(clinical_events.snomedct_code.is_in(eia_snomed_codelist))
    .sort_by(clinical_events.date)
    .last_for_patient()
)

dataset.latest_gp_diag_date = latest_gp_diag.date
dataset.latest_gp_diag_code = latest_gp_diag.snomedct_code

# Map SNOMED codes to categories using the eia_snomed_categories mapping
# eia_snomed_categories is expected to be a dict like {"rheumatoid": [code1, code2], ...}
code_to_category = {
    code: cat
    for cat, codes in eia_snomed_categories.items()
    for code in codes
}
dataset.latest_gp_diag_cat = latest_gp_diag.snomedct_code.to_category(code_to_category)


# Latest APCS (ICD-10) diagnosis (secondary care) - use admission_date as the event date
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

# Prefer primary diagnosis if present, otherwise use secondary diagnosis (keeps ICD10 type)
dataset.latest_apc_diag_code = case(
    when(latest_apc_diag.primary_diagnosis.is_not_null()).then(latest_apc_diag.primary_diagnosis),
    when(latest_apc_diag.secondary_diagnosis.is_not_null()).then(latest_apc_diag.secondary_diagnosis),
    otherwise=None,
)

# Heuristic ICD-10 categorisation by searching `all_diagnoses` text for lists of codes
dataset.latest_apc_diag_cat = case(
    when(latest_apc_diag.all_diagnoses.contains_any_of(rheumatoid_icd10_codelist)).then("rheumatoid"),
    when(latest_apc_diag.all_diagnoses.contains_any_of(psa_icd10_codelist)).then("psa"),
    when(latest_apc_diag.all_diagnoses.contains_any_of(axialspa_icd10_codelist)).then("axialspa"),
    otherwise=None,
)


# Choose the single LATEST date between GP and APC and flag the source
dataset.latest_diag_date = case(
     # Both present -> choose later date
    when(
        dataset.latest_gp_diag_date.is_not_null()
          & dataset.latest_apc_diag_date.is_not_null()
            & (dataset.latest_gp_diag_date >= dataset.latest_apc_diag_date)
            ).then(dataset.latest_gp_diag_date),
    when(
        dataset.latest_gp_diag_date.is_not_null()
          & dataset.latest_apc_diag_date.is_not_null()
            & (dataset.latest_apc_diag_date > dataset.latest_gp_diag_date)
            ).then(dataset.latest_apc_diag_date),
    # Only GP present    
    when(dataset.latest_gp_diag_date.is_not_null()).then(dataset.latest_gp_diag_date),
     # Only APC present
    when(dataset.latest_apc_diag_date.is_not_null()).then(dataset.latest_apc_diag_date),
    otherwise=None,
)

dataset.latest_diag_source = case(
    when(dataset.latest_diag_date == dataset.latest_gp_diag_date).then("primary_care"),
    when(dataset.latest_diag_date == dataset.latest_apc_diag_date).then("secondary_care"),
    otherwise=None,
)

# Derive a single category string from whichever source was chosen above
dataset.latest_diag_category = case(
    when(dataset.latest_diag_source == "primary_care").then(dataset.latest_gp_diag_cat),
    when(dataset.latest_diag_source == "secondary_care").then(dataset.latest_apc_diag_cat),
    otherwise=None,
)

# For convenience: boolean flags per diagnostic category (derived from the chosen string)
latest_diag_category  = dataset.latest_diag_category  # exported local var for downstream import convenience

# boolean flags for convenience (derived from the single string category)
dataset.rheumatoid = (dataset.latest_diag_category == "rheumatoid")
dataset.psa = (dataset.latest_diag_category == "psa")
dataset.axialspa = (dataset.latest_diag_category == "axialspa")
dataset.undiffia = (dataset.latest_diag_category == "undiffia")


# -------------------------------------------------------------------------
# OUTPATIENT VISITS (OPAs) — ALL visits since 2018-01-01
# Rationale: using 2018 as a start date to match measures pipeline interval anchoring
# - compute counts, first date, and existence flag
# - first_opa is used as an anchor for many later derived fields (age, region, etc.)
# -------------------------------------------------------------------------
all_opa= opa.where(
    opa.appointment_date.is_on_or_after("2018-01-01")
   # & opa.attendance_status.is_in(["5","6"]) # re-enable to restrict to attended only
)

   #first opa visit
first_opa = all_opa.where(
            all_opa.appointment_date.is_on_or_after("2018-01-01")
        ).sort_by(
            all_opa.appointment_date
        ).first_for_patient()


# Number of distinct OPAs per patient (since 2018-01-01)
dataset.count_all_opa = all_opa.opa_ident.count_distinct_for_patient()

# First OPA date and existence flag
dataset.first_opa_date = first_opa.appointment_date
dataset.any_opa = first_opa.exists_for_patient()

# Treatment code recorded at the first OPA (useful to detect specialty at first visit)
dataset.first_opa_treatment_code = first_opa.treatment_function_code

# -------------------------------------------------------------------------
# RHEUMATOLOGY OPAs (treatment_function_code == "410")
# - get ALL rheum OPAs since 2018 and the first rheum appointment
# -------------------------------------------------------------------------
all_rheum_opa = opa.where(
        opa.appointment_date.is_on_or_after("2018-01-01")
        & opa.treatment_function_code.is_in(["410"])
       # & opa.attendance_status.is_in(["5","6"]) # uncomment to require attended
    )

first_rheum = (
    all_rheum_opa
    .sort_by(all_rheum_opa.appointment_date)
    .first_for_patient()
)

dataset.first_rheum_date = first_rheum.appointment_date


# ======================================================
#  RHEUMATOLOGY Personalised Follow-up (PFU) VISITS (subset of rheum)
#4,5 - outcome of attendance moved & discharged to pfu
#for rheumatolofy PIFU patients 
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

#age at the first outpatient appointment
#Can we get age as continous variable or is recorded once? 
#           or use date of birth instead?
dataset.age_opa = patients.age_on(dataset.first_opa_date)
dataset.age_opa_group = case(
            when(dataset.age_opa < 18).then("0-17"),
            when(dataset.age_opa < 30).then("18-29"),
            when(dataset.age_opa < 40).then("30-39"),
            when(dataset.age_opa < 50).then("40-49"),
            when(dataset.age_opa < 60).then("50-59"),
            when(dataset.age_opa < 70).then("60-69"),
            when(dataset.age_opa < 80).then("70-79"),
            when(dataset.age_opa < 90).then("80-89"),
            when(dataset.age_opa >= 90).then("90+"),
            otherwise="missing",
    )

#AGe ar first pifu appointment
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

dataset.region = practice_registrations.for_patient_on(dataset.first_opa_date).practice_nuts1_region_name
region=dataset.region ## done this to import to measures.py file easily, other easier method?

dataset.deregister_date = practice_registrations.for_patient_on(dataset.first_opa_date).end_date
dataset.tpp_dod = patients.date_of_death
dataset.ons_dod = ons_deaths.date
dataset.dod = minimum_of(dataset.tpp_dod, dataset.ons_dod)
dataset.fu_days = (minimum_of(dataset.dod, dataset.deregister_date, "2026-12-31") - dataset.first_rheum_pfu_date).days

# define population - everyone with a rheum outpatient visit
#This defines the inclusion criteria 
#Age, sex (female/Male),date of death, practice registrations 
dataset.define_population(
    (dataset.age_opa >= 18) #use most recent visit
    #(dataset.age >= 0)
    #& (dataset.age_opa < 110) 
   # & ((dataset.sex == "male") | (dataset.sex == "female")) #use if restricting to male/female
    & dataset.has_any_diagnosis #has any IA diagnosis
    & (patients.date_of_death.is_after(dataset.first_opa_date) | patients.date_of_death.is_null())
    & (practice_registrations.for_patient_on(dataset.first_opa_date).exists_for_patient())
    & dataset.first_opa_date.is_not_null()
)

#Ethnicity-----------------------------------------
 # Define patient ethnicity at the first outpatient visit   
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

ethnicity=dataset.ethnicity

# Preferred language--------------------------------
preflang_codes = clinical_events.where(
    clinical_events.snomedct_code.is_in(language_codelist)
    & clinical_events.date.is_on_or_before(dataset.first_opa_date)
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
    & clinical_events.date.is_on_or_before(dataset.first_opa_date)
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

#-------------------------------
#Socio-economic status
#-------------------------------
#IMD
#Source: https://docs.opensafely.org/ehrql/reference/schemas/tpp/   #check why IMD is missing - one option is to use GP adress###################

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

imd_quintile= dataset.imd_quintile
#-------------------------------
#Urban/Rural setting
#------------------------------- 
# get last address on or before the anchor date (same pattern as IMD)
last_address = (
    addresses
    .where(addresses.start_date.is_on_or_before(dataset.first_opa_date))
    .sort_by(addresses.start_date)
    .last_for_patient()
)

dataset.rural_urban_classification  = last_address.rural_urban_classification
rural_urban_classification = dataset.rural_urban_classification   


# -------------------------------------------------------------------------
# COVID PHASES - simple categorisation using the first rheum appointment date
# - pre: first_rheum_date <= 2019-12-31
# - peri: 2020-01-01 to 2021-12-31
# - post: 2022-01-01 onwards
# These are coarse categories useful for stratified analyses.
# -------------------------------------------------------------------------
dataset.covid_phase = case(
    when(dataset.first_opa_date.is_on_or_before("2019-12-31")).then("pre"),
    when(
        (dataset.first_opa_date.is_on_or_after("2020-01-01"))
        & (dataset.first_opa_date.is_on_or_before("2021-12-31"))
    ).then("peri"),
    when(dataset.first_opa_date.is_on_or_after("2022-01-01")).then("post"),
    otherwise=None,
)

#Treatment
#csDMARD use
# Filter medication records to csDMARDs only - This is the codelist i have saved currently 
dmard_records = medications.where(
    medications.dmd_code.is_in(DMARD_codelist)
)

# Ever on DMARD (any time)
dataset.ever_on_DMARD = dmard_records.exists_for_patient()

# First-ever DMARD prescription
first_dmard_row = dmard_records.sort_by(dmard_records.date).first_for_patient()
if first_dmard_row:
    dataset.DMARD_first_date = first_dmard_row.date
    dataset.DMARD_first_code = first_dmard_row.dmd_code
else:
    dataset.DMARD_first_date = None
    dataset.DMARD_first_code = None

# Last-ever DMARD prescription
last_dmard_row = dmard_records.sort_by(dmard_records.date).last_for_patient()
if last_dmard_row:
    dataset.DMARD_last_date = last_dmard_row.date
    dataset.DMARD_last_code = last_dmard_row.dmd_code
else:
    dataset.DMARD_last_date = None
    dataset.DMARD_last_code = None
    #Need to add category of DMARDs prescribed accordeing to the SNOMED codes

# Count of csDMARD prescriptions (ever)
dataset.DMARD_prescription_count = dmard_records.count_for_patient()

#Next step: Identify specific prescriptions (add codelist for each eg separate leflunomide_codes)-(Reference: MR repository: https://github.com/opensafely/inflammatory_rheum/tree/main/codelists)



#Steroid use
# Filter medication records to steroids only
steroid_records = medications.where(
    medications.dmd_code.is_in(steroid_codelist)
)

# Ever on steroids (boolean)
dataset.ever_on_steroids = steroid_records.exists_for_patient()

# First-ever steroid prescription
first_steroid_row = steroid_records.sort_by(medications.date).first_for_patient()
dataset.steroid_first_date = first_steroid_row.date
dataset.steroid_first_code = first_steroid_row.dmd_code

# Last-ever steroid prescription
last_steroid_row = steroid_records.sort_by(medications.date).last_for_patient()
dataset.steroid_last_date = last_steroid_row.date
dataset.steroid_last_code = last_steroid_row.dmd_code
#Add category of steroids prescribed according to SNOMED codes

# Count of steroid prescriptions (ever)
dataset.steroid_prescription_count = steroid_records.count_for_patient()


#Co-morbidity burden
#To be created using the Cambridge multimorbidity score - Reference paper here (Payne et al 2020): https://www.cmaj.ca/content/192/5/E107#T4
#Noticed most people creating this in R? - checked on GitHUb.

