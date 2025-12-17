#################################################################
# This code extracts monthly counts of inflammatory arthritis patients on personalised
#   folloup pathways, stratified by relevant characteristics

#################################################################
#coded Using measures framework in OS from here: https://docs.opensafely.org/ehrql/explanation/measures/
#################################################################


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

from dataset_definition_rheum import (
latest_diag_category,
ethnicity,
region,
imd_quintile,
rural_urban_classification,
)


from codelists import (
    ethnicity_codelist, language_codelist, learning_disability_codelist, bmi_codelist, 
    rheumatoid_snomed_codelist, rheumatoid_icd10_codelist,
    psa_snomed_codelist, psa_icd10_codelist,
    axialspa_snomed_codelist, axialspa_icd10_codelist,
    undiff_eia_codelist, eia_snomed_codelist, eia_icd10_codelist ,eia_snomed_categories
)

#=================================
#All patients with a rheumatology outpatient visit
#==================================
# treatment_function_code that identifies rheumatology appointment in opa
rheum_trt_code =["410"]

# codes that indicate an attended appointment ("5","6")
attendance_attended_codes = ["5", "6"]

# outcome_of_attendance codes that indicate personalised follow-up 
pifu_outcome_codes = ["4", "5"]
# ---------------------------------------------

#Population #a: Anyone who has had a rheumatology outpatient appointment (any time)
#
has_rheum_appt_in_interval = opa.where(
    opa.treatment_function_code.is_in(rheum_trt_code)
    & (opa.appointment_date.is_on_or_between(INTERVAL.start_date, INTERVAL.end_date))
).exists_for_patient()

#Population #b: Has a rheumatology diagnosis
#primary care - has ever been diagnosed
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
has_any_diagnosis = has_gp_diagnosis | has_apcs_diagnosis


# -------------------------
# Appointments within interval
# -------------------------
# All OPAs in the current interval (rheumatology and non-rheumatology)
#This definition (all_opa) here means all outpatient visits (both rheum and non_rheum) - later the denominator will limit population to only those with a rheumatology diagnosis 

all_opa = opa.where(
    opa.appointment_date.is_on_or_between(INTERVAL.start_date, INTERVAL.end_date)
    #& opa.attendance_status.is_in(attendance_attended_codes) #add back if we need to include attended only
)

# Of those all OPAs, define rheumatology only OPAs (treatment function identifies rheum treatment code)
rheum_opa = all_opa.where(
     all_opa.treatment_function_code.is_in(rheum_trt_code)
)

# Non-rheumatology OPAs
nonrheum_opa = all_opa.where(
    (all_opa.treatment_function_code.is_null()) |
    (~all_opa.treatment_function_code.is_in(rheum_trt_code))
)

# PIFU appointments for rheum patients 
pfu_rheum_opa = rheum_opa.where(
    rheum_opa.outcome_of_attendance.is_in(pifu_outcome_codes)
)

first_rheum_pfu = (
    pfu_rheum_opa
    .sort_by(pfu_rheum_opa.appointment_date)
    .first_for_patient()
)

first_rheum_pfu_date = first_rheum_pfu.appointment_date

#PIFU PHASES
pre_pifu_all_opa = all_opa.where(opa.appointment_date < first_rheum_pfu_date)
post_pifu_all_opa = all_opa.where(opa.appointment_date > first_rheum_pfu_date) #not including 

##checks
any_rheum_opa = rheum_opa.exists_for_patient()
any_nonrheum_opa = nonrheum_opa.exists_for_patient()
any_rheum_pfu= pfu_rheum_opa.exists_for_patient()
any_opa = all_opa.exists_for_patient()

# --- define a patient-level pfu flag (string) ---
pfu_group = case(
    when(any_rheum_pfu).then("pfu"),
    otherwise="non_pfu",
)

#counts per patient in interval for the defined visits
count_all_opa = all_opa.opa_ident.count_distinct_for_patient() #All opa per patient (pp)
count_rheum_opa = rheum_opa.opa_ident.count_distinct_for_patient() #rheum opa pp
count_nonrheum_opa = nonrheum_opa.opa_ident.count_distinct_for_patient() #nonrheum opa pp
count_pfu_rheum = pfu_rheum_opa.opa_ident.count_distinct_for_patient() #pfu rheum visits pp
count_all_opa_pre_pifu = pre_pifu_all_opa.opa_ident.count_distinct_for_patient()
count_all_opa_post_pifu = post_pifu_all_opa.opa_ident.count_distinct_for_patient()
#========================================
#Measures set up 
#========================================

#Measures object and intervals (2018-date)
measures = Measures ()
measures.configure_disclosure_control(enabled=False)
measures.configure_dummy_data(population_size=1000)


#counting months from jan 2018 - dec2025: months=(end year−start year)×12+(end month−start month)+1
#96 MONTHS IS UPTO DEC 2025 - EDIT FOR LATER MONTHS 
measures.define_defaults(
    intervals=months(96).starting_on("2018-01-01"),
)


denominator = (
       (patients.age_on(INTERVAL.start_date) >= 18) 
        & (patients.age_on(INTERVAL.start_date) < 130)
       # & has_rheum_appt_in_interval #commented out as it means appointments within the month
        & has_any_diagnosis
        #& ((patients.sex == "male") | (patients.sex == "female"))
        & (patients.date_of_death.is_after(INTERVAL.start_date) | patients.date_of_death.is_null())
                         #alive at start or death after start
        & (practice_registrations.for_patient_on(INTERVAL.start_date).exists_for_patient())
                         #registered with a practice on interval start
    )


#====================================
#Demographics
#====================================
# Age on the interval start date
age = patients.age_on(INTERVAL.start_date)

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

# Sex (keep as provided, but map NULL/other to "other")
sex = case(
    when((patients.sex == "male")).then("male"),
    when((patients.sex == "female")).then("female"),
    otherwise="other",
)

#-----------------------------
##other demographics imported from dataset_definition_rheum
#----------------------


##Base Measures
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


measures.define_measure(
    name="count_all_opa_pre_pifu",
    numerator=count_all_opa_pre_pifu,
    denominator=denominator & any_rheum_pfu,
)

measures.define_measure(
    name="count_all_opa_post_pifu",
    numerator=count_all_opa_post_pifu,
    denominator=denominator &any_rheum_pfu,
)

#====================================================
#GROUPING 
#=====================================================
##Group by PIFU

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


#Group by sex
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

#Group by DIAGNOSIS
measures.define_measure(
    name="count_all_opa_by_latest_diag_category",
    numerator=count_all_opa,
    denominator=denominator,
    group_by={"diag_category": latest_diag_category},
)


#Group by ethnicity 
measures.define_measure(
    name="count_all_opa_by_ethnicity",
    numerator=count_all_opa,
    denominator=denominator,
    group_by={"ethnicity": ethnicity},
)


#Group by imd_quintile
measures.define_measure(
    name="count_all_opa_by_imd",
    numerator=count_all_opa,
    denominator=denominator,
    group_by={"imd_quintile": imd_quintile},
)

#Group by rural_urban
measures.define_measure(
    name="count_all_opa_by_ruralurb",
    numerator=count_all_opa,
    denominator=denominator,
    group_by={"rural_urban_classification": rural_urban_classification},
)

















