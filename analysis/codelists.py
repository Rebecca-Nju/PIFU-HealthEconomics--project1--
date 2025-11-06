# ------------------------------------------------------------------
#analysis/codelists.py
# ------------------------------------------------------------------

from ehrql import codelist_from_csv


# Ethnicity (6-group categories)
#Source: https://www.opencodelists.org/codelist/opensafely/ethnicity-snomed-0removed/22911876/ 
#filename: analysis/codelists/ethnicity_codelist_with_categories.csv

ethnicity_codelist = codelist_from_csv(
    "codelists/ethnicity_codelist_with_categories.csv",
    column="snomedcode",
    category_column="Label_6"
)


#Preferred language 
#Source: https://www.opencodelists.org/codelist/nhsd-primary-care-domain-refsets/preflang_cod/20250912/ 
#filename: analysis/codelists/preflang_cod.csv

language_codelist = codelist_from_csv(
    "analysis/codelists/preflang_cod.csv",
    column="code"
)


# BMI-recorded / measurement codes
# Source: https://www.opencodelists.org/codelist/nhsd-primary-care-domain-refsets/bmival_cod/20250912/
# Filename: analysis/codelists/bmival_cod.csv
bmi_codelist = codelist_from_csv(
    "analysis/codelists/bmival_cod.csv",
    column="code"
)

# ------------------------------------------------------------------
#Disease definitions (Inflammatory arthritis subtypes)
# ------------------------------------------------------------------

# Rheumatoid Arthritis (primary care)
# Source: https://www.opencodelists.org/codelist/user/markdrussell/new-rheumatoid-arthritis/1697e230/
# Filename: analysis/codelists/ra_primary.csv
ra_primary_codelist = codelist_from_csv(
    "analysis/codelists/ra_primary.csv",
    column="code"
)

# Rheumatoid Arthritis (secondary care)
# Source: https://www.opencodelists.org/codelist/user/markdrussell/rheumatoid-arthritis-secondary-care/245780e9/
# Filename: analysis/codelists/ra_secondary.csv
ra_secondary_codelist = codelist_from_csv(
    "analysis/codelists/ra_secondary.csv",
    column="code"
)

# Psoriatic Arthritis (primary)
# Source: https://www.opencodelists.org/codelist/user/markdrussell/psoriatic-arthritis/48b6c89a/
# Filename: analysis/codelists/psa_primary.csv
psa_primary_codelist = codelist_from_csv(
    "analysis/codelists/psa_primary.csv",
    column="code"
)

# Psoriatic Arthritis (secondary)
# Source: https://www.opencodelists.org/codelist/user/markdrussell/psoriatic-arthritis-secondary-care/67a69bfb/
# Filename: analysis/codelists/psa_secondary.csv
psa_secondary_codelist = codelist_from_csv(
    "analysis/codelists/psa_secondary.csv",
    column="code"
)

# Axial Spondyloarthritis (primary)
# Source: https://www.opencodelists.org/codelist/user/markdrussell/axial-spondyloarthritis/2fa75565/
# Filename: analysis/codelists/axspa_primary.csv
axspa_primary_codelist = codelist_from_csv(
    "analysis/codelists/axspa_primary.csv",
    column="code"
)

# Axial Spondyloarthritis (secondary)
# Source: https://www.opencodelists.org/codelist/user/markdrussell/axial-spondyloarthritis-secondary-care/4e9728c6/
# Filename: analysis/codelists/axspa_secondary.csv
axspa_secondary_codelist = codelist_from_csv(
    "analysis/codelists/axspa_secondary.csv",
    column="code"
)

# Undifferentiated Inflammatory Arthritis
# Source: https://www.opencodelists.org/codelist/user/markdrussell/undiff-eia/6478fbc5/
# Filename: analysis/codelists/undiff_eia.csv
undiff_eia_codelist = codelist_from_csv(
    "analysis/codelists/undiff_eia.csv",
    column="code"
)


# Learning disability codes
# Source: https://www.opencodelists.org/codelist/nhsd-primary-care-domain-refsets/ld_cod/20250912/
# Filename: analysis/codelists/ld_cod.csv
learning_disability_codelist = codelist_from_csv(
    "analysis/codelists/ld_cod.csv",
    column="code"
)


# ------------------------------------------------------------------
# Medications
# ------------------------------------------------------------------

# DMARDs (Disease-Modifying Anti-Rheumatic Drugs)
# Source: https://www.opencodelists.org/codelist/nhs-drug-refsets/dmardsdrug_cod/20250912/
# Filename: analysis/codelists/dmardsdrug_cod.csv
dmard_codelist = codelist_from_csv(
    "analysis/codelists/dmardsdrug_cod.csv",
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

