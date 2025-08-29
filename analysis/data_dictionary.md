\# Data Dictionary: dataset\_rheum



This file describes the derived variables in `dataset\_rheum.csv.gz`.



| Variable                           | Type  | Description                                                               |

| ---------------------------------- | ----- | ------------------------------------------------------------------------- |

| \*\*patient\\\_id\*\*                    | int   | Unique patient identifier (dummy IDs locally; pseudonymised in TRE).      |

| \*\*pfu\\\_cat\*\*                       | int   | PFU category code from `opa.outcome\_of\_attendance` (codes 4/5 = PFU).     |

| \*\*first\\\_pfu\\\_date\*\*               | date  | Date of the patient’s \*\*first\*\* PFU attendance (on/after 2018-06-01).     |

| \*\*first\\\_pfu\\\_year\*\*               | int   | Calendar year of first PFU attendance (derived from `first\_pfu\_date`).    |

| \*\*any\\\_pfu\*\*                       | str1  | Indicator if patient has \*\*any PFU attendance\*\* (T/F).                    |

| \*\*count\\\_pfu\*\*                     | int   | Number of PFU attendances for the patient since 2018-06-01.               |

| \*\*first\\\_opa\\\_date\*\*               | date  | Date of the patient’s \*\*first rheumatology outpatient attendance\*\*.       |

| \*\*any\\\_opa\*\*                       | str1  | Indicator if patient has any rheumatology OPA attendance (T/F).           |

| \*\*treatment\\\_function\\\_code\*\*      | int   | Specialty code of the patient’s \*\*first OPA\*\* (e.g., 410 = Rheumatology). |

| \*\*pfu\\\_treatment\\\_function\\\_code\*\* | int   | Specialty code of the patient’s \*\*first PFU attendance\*\*.                 |

| \*\*before\\\_3yr\*\*                    | int   | Count of outpatient attendances in the \*\*3 years before first PFU\*\*.      |

| \*\*before\\\_2yr\*\*                    | int   | Count of outpatient attendances in the \*\*2 years before first PFU\*\*.      |

| \*\*before\\\_1yr\*\*                    | int   | Count of outpatient attendances in the \*\*1 year before first PFU\*\*.       |

| \*\*after\\\_1yr\*\*                     | int   | Count of outpatient attendances in the \*\*1 year after first PFU\*\*.        |

| \*\*before\\\_last\\\_date\*\*             | date  | Date of the \*\*last attendance\*\* before PFU (within 3 years).              |

| \*\*after\\\_next\\\_date\*\*              | date  | Date of the \*\*first attendance after PFU\*\*.                               |

| \*\*days\\\_from\\\_last\\\_visit\*\*        | int   | Days between the last pre-PFU visit and the first PFU visit.              |

| \*\*days\\\_to\\\_next\\\_visit\*\*          | int   | Days between the first PFU visit and the next OPA.                        |

| \*\*sex\*\*                            | str6  | Patient’s sex (`male`/`female`).                                          |

| \*\*age\*\*                            | int   | Age at first rheumatology outpatient attendance.                          |

| \*\*age\\\_group\*\*                     | str5  | Age band: `18–29`, `30–39`, …, `90+`.                                     |

| \*\*region\*\*                         | str24 | NUTS1 region of the patient’s GP practice at first OPA.                   |



