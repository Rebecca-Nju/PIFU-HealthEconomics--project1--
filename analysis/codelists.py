# ------------------------------------------------------------------
#analysis/codelists.py
# ------------------------------------------------------------------

from ehrql import codelist_from_csv
from itertools import chain


# Ethnicity (6-group categories)
#Source: https://www.opencodelists.org/codelist/opensafely/ethnicity-snomed-0removed/22911876/ 
#filename: analysis/codelists/ethnicity_codelist_with_categories.csv
#The full 6 Group Categories includes "6 - Not stated" which was not included in our codelist # missing

ethnicity_codelist = codelist_from_csv(
    "analysis/codelists/ethnicity_codelist_with_categories.csv",
    column="code",
    category_column="Grouping_6"
)

# BMI-recorded / measurement codes
# Source: https://www.opencodelists.org/codelist/nhsd-primary-care-domain-refsets/bmival_cod/20250912/
# Filename: analysis/codelists/bmival_cod.csv
bmi_codelist = codelist_from_csv(
    "analysis/codelists/bmival_cod.csv",
    column="code"
)

#Preferred language 
#Source: https://www.opencodelists.org/codelist/nhsd-primary-care-domain-refsets/preflang_cod/20250912/ 
#filename: analysis/codelists/preflang_cod.csv

language_codelist = codelist_from_csv(
    "analysis/codelists/preflang_cod.csv",
    column="code",
    category_column= "term"
)


# Learning disability codes
# Source: https://www.opencodelists.org/codelist/nhsd-primary-care-domain-refsets/ld_cod/20250912/
# Filename: analysis/codelists/ld_cod.csv
learning_disability_codelist = codelist_from_csv(
    "analysis/codelists/ld_cod.csv",
    column="code",
    category_column = "term"
)



# ------------------------------------------------------------------
#Disease definitions (Inflammatory arthritis subtypes)
# ------------------------------------------------------------------

# Rheumatoid Arthritis (SNOMED)
# Source: https://www.opencodelists.org/codelist/user/markdrussell/new-rheumatoid-arthritis/1697e230/
# Filename: analysis/codelists/rheumatoid_snomed.csv
rheumatoid_snomed_codelist = codelist_from_csv(
    "analysis/codelists/rheumatoid_snomed.csv",
    column="code"
)

# Rheumatoid Arthritis (ICD-10)
# Source: https://www.opencodelists.org/codelist/user/markdrussell/rheumatoid-arthritis-secondary-care/245780e9/
# Filename: analysis/codelists/rheumatoid_icd10.csv
rheumatoid_icd10_codelist = codelist_from_csv(
    "analysis/codelists/rheumatoid_icd10.csv",
    column="code"
)

# Psoriatic Arthritis (SNOMED)
# Source: https://www.opencodelists.org/codelist/user/markdrussell/psoriatic-arthritis/48b6c89a/
# Filename: analysis/codelists/psa_snomed.csv
psa_snomed_codelist = codelist_from_csv(
    "analysis/codelists/psa_snomed.csv",
    column="code"
)

# Psoriatic Arthritis (ICD-10)
# Source: https://www.opencodelists.org/codelist/user/markdrussell/psoriatic-arthritis-secondary-care/67a69bfb/
# Filename: analysis/codelists/psa_icd10.csv
psa_icd10_codelist = codelist_from_csv(
    "analysis/codelists/psa_icd10.csv",
    column="code"
)

# Axial Spondyloarthritis (SNOMED)
# Source: https://www.opencodelists.org/codelist/user/markdrussell/axial-spondyloarthritis/2fa75565/
# Filename: analysis/codelists/axialspa_snomed.csv
axialspa_snomed_codelist = codelist_from_csv(
    "analysis/codelists/axialspa_snomed.csv",
    column="code"
)

# Axial Spondyloarthritis (ICD-10)
# Source: https://www.opencodelists.org/codelist/user/markdrussell/axial-spondyloarthritis-secondary-care/4e9728c6/
# Filename: analysis/codelists/axialspa_icd10.csv
axialspa_icd10_codelist = codelist_from_csv(
    "analysis/codelists/axialspa_icd10.csv",
    column="code"
)

# Undifferentiated Inflammatory Arthritis
# Source: https://www.opencodelists.org/codelist/user/markdrussell/undiff-eia/6478fbc5/
# Filename: analysis/codelists/undiff_eia.csv
undiff_eia_codelist = codelist_from_csv(
    "analysis/codelists/undiff_eia.csv",
    column="code"
   
)

# create a dict mapping category name -> SNOMED code list (used by to_category)
eia_snomed_categories = {
    "axialspa": axialspa_snomed_codelist,
    "psa":      psa_snomed_codelist,
    "rheumatoid": rheumatoid_snomed_codelist,
    "undiff_eia": undiff_eia_codelist,
}

# Combined Inflammatory Arthritis (SNOMED)
eia_snomed_codelist = (
    axialspa_snomed_codelist +
    psa_snomed_codelist +
    rheumatoid_snomed_codelist +
    undiff_eia_codelist
)


# Combined Inflammatory Arthritis (ICD-10)
eia_icd10_codelist = (
  axialspa_icd10_codelist +
  psa_icd10_codelist +
   rheumatoid_icd10_codelist
)

# ------------------------------------------------------------------
# Medications
# ------------------------------------------------------------------

# DMARDs (Disease-Modifying Anti-Rheumatic Drugs)
# Source: https://www.opencodelists.org/codelist/nhs-drug-refsets/dmardsdrug_cod/20250912/
#Mainly contains Conventional synthetic DMARDs (csDMARDs)
# Filename: analysis/codelists/csDMARD_cod.csv
DMARD_codelist = codelist_from_csv(
    "analysis/codelists/DMARD_cod.csv",
    column="code"
)

# Corticosteroids (systemic)
# Source: https://www.opencodelists.org/codelist/nhs-drug-refsets/c19corstedrug_cod/20250912/
# Filename: analysis/codelists/c19corstedrug_cod.csv
steroid_codelist = codelist_from_csv(
    "analysis/codelists/c19corstedrug_cod.csv",
    column="code"
)

# ------------------------------------------------------------------
# Lifestyle / Health behaviours
# ------------------------------------------------------------------

# Smoking status – current smoker
# Source: https://www.opencodelists.org/codelist/nhsd-primary-care-domain-refsets/lsmok_cod/20250912/
# Filename: analysis/codelists/lsmok_cod.csv
smoker_codelist = codelist_from_csv(
    "analysis/codelists/lsmok_cod.csv",
    column="code"
)

# Smoking status – ex-smoker
# Source: https://www.opencodelists.org/codelist/nhsd-primary-care-domain-refsets/exsmok_cod/20250912/
# Filename: analysis/codelists/exsmok_cod.csv
exsmoker_codelist = codelist_from_csv(
    "analysis/codelists/exsmok_cod.csv",
    column="code"
)

# Excessive alcohol use
# Source: https://www.opencodelists.org/codelist/nhsd-primary-care-domain-refsets/excessalc_cod/20250912/
# Filename: analysis/codelists/excessalc_cod.csv
excess_alcohol_codelist = codelist_from_csv(
    "analysis/codelists/excessalc_cod.csv",
    column="code"
)



# ------------------------------------------------------------------
#Carer status
# ------------------------------------------------------------------

#Carer status
#Source: https://www.opencodelists.org/codelist/https://www.opencodelists.org/codelist/nhsd-primary-care-domain-refsets/isacarer_cod/20250912/  
# Filename: analysis/codelists/isacarer_cod.csv
isacarer_codelist = codelist_from_csv(
    "analysis/codelists/isacarer_cod.csv",
    column="code"
)

