#################################################################
#Purpose
#-----------
# This code extracts monthly counts of inflammatory arthritis patients on personalised
#   followup (PIFU) pathways, stratified by a set of demographic and clinical groupings, using OS Measures framework 
# (https://docs.opensafely.org/ehrql/explanation/measures/)

#High-level logic
#----------------
#- Build patient-level boolean flags and visit-level subsets (rheum vs non-rheum, PIFU outcomes).
#- Define counts per-patient within each monthly interval.
#- Define a denominator of eligible patients (age >=18, registered, alive at
  # interval start, and with a recorded diagnosis in primary or secondary care).
#- Register multiple measures (unstratified and grouped) in the Measures object,
  #  configured to output per-month intervals.

#Outputs
#-------
#- `measures` object includes measures named like:
 #   - patient_count
  #  - count_all_opa, count_rheum_opa, count_nonrheum_opa, count_pfu_rheum
   #  - pre/post PIFU counts for patients who had PIFU
    # - grouped counts by pfu / sex / diagnosis / ethnicity / IMD / rural-urban

#Configurable (to be changed)
#---------------------------------------------------------
#- Interval length: `months(N_months).starting_on("study_index_date")` — change `N_months` & study_index_date
  #to extend/reduce the time range.
#- Codelists (`eia_snomed_codelist`, `eia_icd10_codelist`, etc.) are imported
  #local `codelists` module. Ensure those are kept up-to-date externally.
#- Measures disclosure control is disabled in this script (`enabled=False`) —
  #remember to change to `enabled=True` when producing outputs intended for release
  

#Imports (ehrQl and modules )
from ehrql import months, INTERVAL, Measures, case, when 
from ehrql.tables.tpp import (
    patients,
    practice_registrations,
    opa,
    clinical_events,
    apcs,
    ethnicity_from_sus,
    addresses,
    ons_deaths,
)


#project-specific data definition:from analysis/datadefinition_rheum
from dataset_definition_rheum import (
latest_diag_category,
ethnicity,
region,
imd_quintile,
rural_urban_classification,
)

#Codelists used for diagnosis and demographic mappings 
from codelists import (
    ethnicity_codelist, language_codelist, learning_disability_codelist, bmi_codelist, 
    rheumatoid_snomed_codelist, rheumatoid_icd10_codelist,
    psa_snomed_codelist, psa_icd10_codelist,
    axialspa_snomed_codelist, axialspa_icd10_codelist,
    undiff_eia_codelist, eia_snomed_codelist, eia_icd10_codelist ,eia_snomed_categories
)

#======================================================
#Constants & code-based definitions
#======================================================
# treatment_function_code that identifies rheumatology appointment in opa
rheum_trt_code =["410"]

# codes that indicate an attended appointment ("5","6")
attendance_attended_codes = ["5", "6"]

# outcome_of_attendance codes that indicate personalised follow-up 
pifu_outcome_codes = ["4", "5"]
# ---------------------------------------------

# Study start date for Measures intervals
# (All monthly intervals begin from this date)
study_index_date = "2018-01-01"

#Months after index date (follow-up period)
#To change 
N_months = 120

#=======================================================
#Define groups based on OPA table 
#=======================================================

# Any outpatient appointment that is classified as rheumatology in the given interval
has_rheum_appt_in_interval = opa.where(
    opa.treatment_function_code.is_in(rheum_trt_code)
    & (opa.appointment_date.is_on_or_between(INTERVAL.start_date, INTERVAL.end_date))
    #Interval_start/end date -first/end of every month
).exists_for_patient()

# -------------------------
# Diagnosis definitions
# -------------------------
# Primary care (GP) diagnosis: any clinical event with a matching SNOMED code (ever)
has_gp_diagnosis = clinical_events.where(
    clinical_events.snomedct_code.is_in(eia_snomed_codelist)   
).exists_for_patient()

# Secondary care (APCS) diagnosis: check primary, secondary and all_diagnoses fields
# This covers hospital-coded ICD-10 entries in any diagnosis slot
#from here: https://docs.opensafely.org/ehrql/reference/schemas/tpp/#apcs
has_apcs_diagnosis = (
    apcs.where(apcs.primary_diagnosis.is_in(eia_icd10_codelist)).exists_for_patient()
    | apcs.where(apcs.secondary_diagnosis.is_in(eia_icd10_codelist)).exists_for_patient()
    | apcs.where(apcs.all_diagnoses.contains_any_of(eia_icd10_codelist)).exists_for_patient()
)

# Combined diagnosis: either primary care OR secondary care diagnosis (ever/any time in their history)
has_any_diagnosis = has_gp_diagnosis | has_apcs_diagnosis



# -------------------------
# Appointments within interval
# -------------------------
# `all_opa`: all outpatient appointments in the interval, regardless of specialty
# Note: attendance filtering is commented out — re-enable if you only want attended visits
all_opa = opa.where(
    opa.appointment_date.is_on_or_between(INTERVAL.start_date, INTERVAL.end_date)
    #& opa.attendance_status.is_in(attendance_attended_codes) 
)

# Subset: rheumatology outpatient appointments in the interval
rheum_opa = all_opa.where(
     all_opa.treatment_function_code.is_in(rheum_trt_code)
)

# Subset: non-rheumatology outpatient appointments
# Treats NULL treatment function code as non-rheum (explicit)
nonrheum_opa = all_opa.where(
    (all_opa.treatment_function_code.is_null()) |
    (~all_opa.treatment_function_code.is_in(rheum_trt_code))
)

# Subset: rheumatology appointments whose outcome indicates PIFU
pfu_rheum_opa = rheum_opa.where(
    rheum_opa.outcome_of_attendance.is_in(pifu_outcome_codes)
)

# For each patient, find their first rheumatology appointment in the interval with a PIFU outcome
first_rheum_pfu = (
    pfu_rheum_opa
    .sort_by(pfu_rheum_opa.appointment_date)
    .first_for_patient()
)

# A convenient scalar (column) representing the first PIFU appointment date per patient
first_rheum_pfu_date = first_rheum_pfu.appointment_date

# Define pre- and post-PIFU appointment sets (relative to the first PIFU date)
# Note: these are defined on all OPAs (rheum and non-rheum) — i.e., visits before/after that first PIFU
pre_pifu_all_opa = all_opa.where(opa.appointment_date < first_rheum_pfu_date)
post_pifu_all_opa = all_opa.where(opa.appointment_date > first_rheum_pfu_date)  

# Existence checks (patient-level booleans used in various measures / groups)
any_rheum_opa = rheum_opa.exists_for_patient()
any_nonrheum_opa = nonrheum_opa.exists_for_patient()
any_rheum_pfu= pfu_rheum_opa.exists_for_patient()
any_opa = all_opa.exists_for_patient()

# ------------------------------
# Patient-level PIFU group flag
# ------------------------------
# This creates a string classification per patient:
# - "pfu" if the patient had any rheumatology appointment with a PIFU outcome in interval
# - "non_pfu" otherwise
pfu_group = case(
    when(any_rheum_pfu).then("pfu"),
    otherwise="non_pfu",
)

# --------------------------------------------
# Counts per patient in each interval (per-month)
# --------------------------------------------
# These count *distinct* outpatient identifiers per patient inside the interval
# Use .count_distinct_for_patient() to get per-patient totals within the measure interval.
count_all_opa = all_opa.opa_ident.count_distinct_for_patient() # All OPAs per patient
count_rheum_opa = rheum_opa.opa_ident.count_distinct_for_patient() # Rheum OPAs per patient
count_nonrheum_opa = nonrheum_opa.opa_ident.count_distinct_for_patient() # Non-rheum OPAs per patient
count_pfu_rheum = pfu_rheum_opa.opa_ident.count_distinct_for_patient() # Rheum PIFU visits per patient

# Counts restricted to visits before/after the first PIFU (for patients on PIFU)
count_all_opa_pre_pifu = pre_pifu_all_opa.opa_ident.count_distinct_for_patient()
count_all_opa_post_pifu = post_pifu_all_opa.opa_ident.count_distinct_for_patient()


# =========================
# Demographics / stratifiers
# =========================
# Age measured at interval start (so the age band is stable within each interval)
age = patients.age_on(INTERVAL.start_date)

# Create age bands (strings) for grouping. Any patient under 18 will fall outside denominator.
age_band = case(  
    when((age >= 18) & (age <= 29)).then("age_18_29"),
    when((age >= 30) & (age <= 39)).then("age_30_39"),
    when((age >= 40) & (age <= 49)).then("age_40_49"),
    when((age >= 50) & (age <= 59)).then("age_50_59"),
    when((age >= 60) & (age <= 69)).then("age_60_69"),
    when((age >= 70) & (age <= 79)).then("age_70_79"),
    when((age >= 80) & (age <= 89)).then("age_80_89"),
    when((age >= 90)).then("age_90+"),
    otherwise="missing",
)

# Sex mapping: keep male/female labels, collapse NULL/other to "other"
sex = case(
    when((patients.sex == "male")).then("male"),
    when((patients.sex == "female")).then("female"),
    otherwise="other",
)
# Other demographic stratifiers — imported from dataset_definition_rheum:
# latest_diag_category, ethnicity, imd_quintile, rural_urban_classification

# ======================
# Measures configuration
# ======================

#Measures object and intervals (2018-date)
measures = Measures ()
# Turn off disclosure control for local exploration; *set True for production outputs*
measures.configure_disclosure_control(enabled=False)
# Create dummy data for local development / small-run testing (change population_size as needed)
measures.configure_dummy_data(population_size=1000)

# ------------------------
# Define the reporting time intervals (monthly intervals)
# ------------------------
# months(96) creates 96 consecutive monthly intervals starting 2018-01-01
# If you want to extend beyond Dec 2025, increase `96` appropriately.
measures.define_defaults(
    intervals=months(N_months).starting_on("study_index_date"),
)

# ------------------------
# Denominator (eligible population at interval start)
# ------------------------
denominator = (
       (patients.age_on(INTERVAL.start_date) >= 18) 
        & (patients.age_on(INTERVAL.start_date) < 130)
        & has_any_diagnosis
        #& ((patients.sex == "male") | (patients.sex == "female")) #commented out to remove restrictions - all included 
        & (patients.date_of_death.is_after(INTERVAL.start_date) | patients.date_of_death.is_null())
                         #alive at start or death after start
        & (practice_registrations.for_patient_on(INTERVAL.start_date).exists_for_patient())
                         #registered with a practice on interval start
    )


# ------------------------
# Base measures (unstratified)
# ------------------------
# patient_count: simple count of eligible patients at interval start
patient_indicator = case(
    when(denominator).then(1),
    otherwise=0
)

measures.define_measure(
    name="patient_count",
    numerator=patient_indicator,
    denominator=denominator
)

# Visit-count measures (per-patient counts aggregated across the denominator)
measures.define_measure(
    name="count_all_opa",
    numerator=count_all_opa,
    denominator=denominator,
)

measures.define_measure(
    name="count_rheum_opa",
    numerator=count_rheum_opa,
    denominator=denominator,
)

measures.define_measure(
    name="count_nonrheum_opa",
    numerator=count_nonrheum_opa,
    denominator=denominator,
)

measures.define_measure(
    name="count_pfu_rheum",
    numerator=count_pfu_rheum, 
    denominator=denominator,
)

# Pre/post PIFU counts should be restricted to patients who had a rheum PIFU
#These two measures 
measures.define_measure(
    name="count_all_opa_pre_pifu",
    numerator=count_all_opa_pre_pifu,
    denominator=denominator & any_rheum_pfu,
    #Q: Added & any_rheum_pfu to add restriction that visits counted should be specifically rheum PIFU, should i change this and leave main denominator?
)

measures.define_measure(
    name="count_all_opa_post_pifu",
    numerator=count_all_opa_post_pifu,
    denominator=denominator &any_rheum_pfu,
)

#====================================================
#GROUPING 
#=====================================================
#
#----------------------------------------
#PIFU
#Notes: ##Group by PIFU ####### need to recheck this grouping; 
# #Should not group as pfu group vs non-pfu group but number of visits before and after PIFU
#---------------------------------------


# --- define a patient-level pfu flag (string) ---
##THis is for all appointments - rheumatology and non-rheumatology
measures.define_measure(
    name="count_all_opa_by_pfu",
    numerator=count_all_opa,
    denominator=denominator,
    group_by={"pfu_group": pfu_group},
)

##this is for rheumatology appointments only
measures.define_measure(
    name="count_rheum_opa_by_pfu",
    numerator=count_rheum_opa,
    denominator=denominator,
    group_by={"pfu_group": pfu_group},
)

#----------------------------------------
#Group by sex
#----------------------------------------
#Total opa
measures.define_measure(
    name="count_all_opa_by_sex",
    numerator=count_all_opa,
    denominator=denominator,
    group_by={
        "sex": sex
    },
)

#Group by both PIFU and sex
#Total opa
measures.define_measure(
    name="count_all_opa_by_pfu_sex",
    numerator=count_all_opa,
    denominator=denominator,
    group_by={
        "pfu_group": pfu_group,
        "sex": sex
    },
)


#----------------------------------------
# Group by most recent diagnosis category (stratifier imported from dataset_definition_rheum)
#----------------------------------------


measures.define_measure(
    name="count_all_opa_by_latest_diag_category",
    numerator=count_all_opa,
    denominator=denominator,
    group_by={"diag_category": latest_diag_category},
)


# Group by ethnicity (imported stratifier) 
measures.define_measure(
    name="count_all_opa_by_ethnicity",
    numerator=count_all_opa,
    denominator=denominator,
    group_by={"ethnicity": ethnicity},
)


#----------------------------------------
# Group by IMD quintile (imported)
#----------------------------------------

measures.define_measure(
    name="count_all_opa_by_imd",
    numerator=count_all_opa,
    denominator=denominator,
    group_by={"imd_quintile": imd_quintile},
)

#----------------------------------------
# Group by rural / urban classification (imported)
#----------------------------------------

measures.define_measure(
    name="count_all_opa_by_ruralurb",
    numerator=count_all_opa,
    denominator=denominator,
    group_by={"rural_urban_classification": rural_urban_classification},
)

















