""" 
PQ24924:
To ask the Secretary of State for Justice, how many people serving an imprisonment for a Public Protection sentence 
were held in secure hospitals at the start of the last 20 quarters.

By Eric Nyame, 08/05/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import os

# import importlib

sys.path.append('/home/jovyan/OMPPG/Macro Library')
import Out_of_bounds_dates
# importlib.reload(Out_of_bounds_dates)
import TimeDiffs

# Set display options

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.set_option('display.max_colwidth', None)

# Ensures no wrapping of cell contents - run it separately
%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

#************* MAIN ADMISSION CATEGORIES**********************************
"""
s45A/s45B = HOSPTAL DIRECTIONS. Court convicts but directs to hospital. 
       Prison sentence to be served after successful treatment in hospital.
    
s37/s41 = HOSPITAL ORDER with RESTRICTIONS added. 
          Issued by the court. Patient could be unfit or not guilty by insanity.
          Not guilty by isanity does not mean they didn't commit the offence?


s47/s49 =  TRANSFER OF CONVICTED PRISONERS with RESTRICTIONS added
           Secretary of State transfers a CONVICTED prisoner from prison to hospital. 

s48/s49 = TRANSFER OF UNCONVICTED PRISONERS with RESTRICTIONS added.
          Secretary of State transfers an UNSENTENCED prisoner from prison to hospital. 
          This could include remand, immigration detainees, unsentenced prisoners, civil prisoners.
"""
#*********************************************************************

# (A)------------------------------------ Import population data

# years to cover
years = [2019, 2020, 2021, 2022, 2023]

# loop through folders and try to import files with different file types but same name

for year in years:
    # import the file if it's a SAS file and name it pop_year
    try:
        globals()[f'pop_{year}'] = pd.read_sas(f"s3://alpha-omppg/Mental-Health/{year}/output/population_prepared_{year}.sas7bdat", encoding='latin1')
        print(f"Loaded SAS file for {year}")
    except Exception as e:
        print(f"Failed to load SAS file for {year}, error: {e}")
        
        # else if the file is not SAS, import it if it's an excel file
        try:
            globals()[f'pop_{year}'] = pd.read_excel(f"s3://alpha-omppg/Mental-Health/{year}/output/population_prepared_{year}.xls")
            print(f"Loaded Excel file for {year}")
        except Exception as e:
            print(f"Failed to load Excel file for {year}, error: {e}")
            
            # else if the file is not an excel file, import it if it's a parquet file
            try:
                globals()[f'pop_{year}'] = pd.read_parquet(f"s3://alpha-omppg/Mental-Health/{year}/output/population_prepared_{year}.parquet")
                print(f"Loaded Parquet file for {year}")
            except Exception as e:
                print(f"Failed to load Excel file for {year}, error: {e}")

# upper case columns
for year in years:
    globals()[f'pop_{year}'].columns = globals()[f'pop_{year}'].columns.str.upper()
    
# Check lengths match published population figures
for year in years:
    print(year,len(globals()[f'pop_{year}']))
    
# count IPPs
for year in years:
    x = globals()[f'pop_{year}']
    ipp_mask = x['DA_CUSTODY_TYPE_DESCRIPTION'].str.contains('IPP|DPP',case=False,na=False)
    count = len(x[ipp_mask])
    print(year,count)

# (B)------------------------------------ TRANSFERS FROM PRISON TO HOSPITAL

# similarly import admissions and recalls data

for year in years:
    try:
        globals()[f'admissions_{year}'] = pd.read_sas(f"s3://alpha-omppg/Mental-Health/{year}/output/admrec_prepared_{year}.sas7bdat", encoding='latin1')
        print(f"Loaded SAS file for {year}")
    except Exception as e:
        print(f"Failed to load SAS file for {year}, error: {e}")
        
        # Attempt to load Excel file
        try:
            globals()[f'admissions_{year}'] = pd.read_excel(f"s3://alpha-omppg/Mental-Health/{year}/output/admrec_prepared_{year}.xls")
            print(f"Loaded Excel file for {year}")
        except Exception as e:
            print(f"Failed to load Excel file for {year}, error: {e}")
            
            # Attempt to load Excel file
            try:
                globals()[f'admissions_{year}'] = pd.read_parquet(f"s3://alpha-omppg/Mental-Health/{year}/output/admrec_prepared_{year}.parquet")
                print(f"Loaded Parquet file for {year}")
            except Exception as e:
                print(f"Failed to load Excel file for {year}, error: {e}")

# upper case columns
for year in years:
    globals()[f'admissions_{year}'].columns = globals()[f'admissions_{year}'].columns.str.upper()
    
# Check lengths match puplished total admissions figures 
for year in years:
    print(year,len(globals()[f'admissions_{year}']))

# Check countrs of prison transfers to hospital match the published figures. 
# At the same time, count IPPs involved in the transfers
for year in years:
    x = globals()[f'admissions_{year}']
    if year != 2023:
        x['ADMISSION_CATEGORY'] = x['DETAUTH']
    prison_trans_mask = x['ADMISSION_CATEGORY'].str.contains('Transferred from Prison',case=False,na=False)
    ipp_mask = x['CUSTODY_TYPE_DESCRIPTION'].str.contains('IPP|DPP',case=False,na=False)
    count = len(x[prison_trans_mask]) 
    count2 = len(x[prison_trans_mask & ipp_mask]) 
    print(year,count,count2,sep=',')
