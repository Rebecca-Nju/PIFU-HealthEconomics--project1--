@echo off
REM =====================================================
REM using this script to write and save codes that I am running on OpenSAFELY CLI


REM  OpenSAFELY quick run script using .\run_opensafely.bat
REM  Uses direct path to opensafely.exe inside Anaconda, the word REM is used to comment out

REM =====================================================
echo  Changing directory
REM cd "C:\Users\Rebeccanj\GitHub\PIFU-HealthEconomics--project1--"

REM --- Pull latest OpenSAFELY images ---
echo Pulling latest OpenSAFELY images...
REM opensafely pull


REM checking ehqrl tables 
echo checking tables attributes...
echo checking opa table attributes... 
REM opensafely exec ehrql:v1 python -c "from ehrql.tables.tpp import opa; print('--- opa attrs ---'); print('\n'.join(sorted(a for a in dir(opa) if not a.startswith('_'))))"
echo checking ethnicity_from_sus table attributes...
REM opensafely exec ehrql:v1 python -c "from ehrql.tables.tpp import ethnicity_from_sus; print('--- ethnicity_from_sus attrs ---'); print('\n'.join(sorted(a for a in dir(ethnicity_from_sus) if not a.startswith('_'))))"
echo clinical events table 
REM  opensafely exec ehrql:v1 python -c "from ehrql.tables.tpp import clinical_events; print('--- clinical_events attrs ---'); print('\n'.join(sorted(a for a in dir(clinical_events) if not a.startswith('_'))))"
REM opensafely exec ehrql:v1 python -c "from ehrql.tables.tpp import opa; print('--- opa attrs ---'); print('\n'.join(sorted(a for a in dir(opa) if not a.startswith('_'))))"
REM opensafely exec ehrql:v1 python -c "from ehrql.tables.tpp import patients; print('--- patients attrs ---'); print('\n'.join(sorted(a for a in dir(patients) if not a.startswith('_'))))"      

REM --- Generate dataset ---
echo Generating dataset...
REM   opensafely run generate_dataset_definition_rheum

REM ---view dataset---
REM python -c "import gzip, shutil; shutil.copyfileobj(gzip.open('output/dataset_definition_rheum.csv.gz', 'rb'), open('output/dataset_definition_rheum.csv', 'wb'))"

echo.
echo ✅ Done! Dataset generated in the output folder.
pause


