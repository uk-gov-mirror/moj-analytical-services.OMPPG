""" 
1. The approximate cost of a 2- and 4-week FTR
2. The total number of quarterly FTRs issued in 2017, 2018, 2019, 2020, 2021, 2022, 2023 and 2024 (if available)
3. The total number of quarterly standard recalls issued in 2017, 2018, 2019, 2020, 2021, 2022, 2023 and 2024 (if available)
4. The total number of quarterly recalls (all types) issued in 2017, 2018, 2019, 2020, 2021, 2022, 2023 and 2024 (if available)
5. The breakdown of annual FTRs issued by age groups [e.g. X (20-25 years old), Y (26-30 years old), Z (31-35 years old)] across 2017, 2018, 2019, 2020, 2021, 2022 and 2023
6. As a percentage, the proportion of FTRs given to each age group compared to the total number of that age group eligible for an FTR.
a.  For context, I am wanting to understand if FTRs are skewed across different age groups. I'd like to understand, of the total number of people of each age group on licence (and therefore eligible for FTR), the proportion that receive an FTR.
7. In 2023, the proportion of fixed-term recalls that were the second fixed-term recall on the same sentence.


By Eric Nyame, 29/05/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib
import os

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
# from my_log import my_log
import Out_of_bounds_dates
#importlib.reload(Out_of_bounds_dates)
#import prepareMatch
#importlib.reload(prepareMatch)
#import openMatch
#importlib.reload(openMatch)
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


# Import data ------------------
    # load data from 2017 to 2023 latest publication full year------------------
years = [2017, 2018, 2019, 2020, 2021, 2022, 2023]
quarters =['q1','q2','q3','q4']

recalls = pd.DataFrame() 

for i in years[:-1]: # exclude 2023 for now as it has parquet files ------------------
    for j in quarters:
        rec = pd.read_sas(f"s3://alpha-omppg/Recalls/final_data/recalls/recalls_final_{i}{j}.sas7bdat", encoding='latin1')
        rec.columns = rec.columns.str.upper() # capitalise all headers
        recalls = pd.concat([recalls,rec],axis = 0, ignore_index= True) # concatenate 

recalls.shape # 142,799

    # Add 2023 data separately------------------

for quarter in quarters:
    
    try: # SAS files------------------
        quart_recs = pd.read_sas(f"s3://alpha-omppg/Recalls/final_data/recalls/recalls_final_2023{quarter}.sas7bdat", encoding='latin1')
        quart_recs.columns = quart_recs.columns.str.upper()
        print(f"Loaded SAS file for {quarter}")
    except Exception as e:
        print(f"Failed to load SAS file for {quarter}, error: {e}")
        # else if the file is not SAS, import it if it's a parquet file
        try: # Parquet files ------------------
            quart_recs = pd.read_parquet(f"s3://alpha-omppg/Recalls/final_data/recalls/recalls_final_2023{quarter}.parquet")
            quart_recs.columns = quart_recs.columns.str.upper()
            print(f"Loaded Parquet file for {quarter}")
        except Exception as e:
            print(f"Failed to load Excel file for {quarter}, error: {e}")
  
    recalls = pd.concat([recalls,quart_recs],axis=0)

recalls.shape[0] # 170,619

# save a copy in case something goes wrong you don't have to repeat above-----------------------------
recalls_back_up = recalls.copy()

# Add age groups to the recall data-------------- ------------

recalls['DOB'].isna().sum() # 0
recalls['DOB'].dt.year.min(), recalls['DOB'].dt.year.max() # question DOB 1900

recalls['AGE_AT_RECALL'] = recalls.apply(lambda x: TimeDiffs.year_diff(x['DOB'],x['LICENCE_REVOKE_DATE']),axis=1)

# recalls['AGE_AT_RECALL'].isna().sum() # 0
# recalls['AGE_AT_RECALL'].value_counts(dropna=False).sort_index()
# recalls[['DOB','LICENCE_REVOKE_DATE','AGE_AT_RECALL']].head()

recalls['AGEBAND_AT_RECALL'] = ''
recalls.loc[recalls['AGE_AT_RECALL'] <= 20,'AGEBAND_AT_RECALL'] = 'Less than or equal to 20'
recalls.loc[(recalls['AGE_AT_RECALL'] > 20) & (recalls['AGE_AT_RECALL'] <= 25),'AGEBAND_AT_RECALL'] = '21-25'
recalls.loc[(recalls['AGE_AT_RECALL'] > 25) & (recalls['AGE_AT_RECALL'] <= 30),'AGEBAND_AT_RECALL'] = '26-30'
recalls.loc[(recalls['AGE_AT_RECALL'] > 30) & (recalls['AGE_AT_RECALL'] <= 35),'AGEBAND_AT_RECALL'] = '31-35'
recalls.loc[recalls['AGE_AT_RECALL'] > 35 ,'AGEBAND_AT_RECALL'] = '36 or more' # 36+

# recalls[['DOB','LICENCE_REVOKE_DATE','AGE_AT_RECALL','AGEBAND_AT_RECALL']].head()

# Identify fixed-term recalls ----------------------------------------------
recalls['RECALL_TYPE_DESCRIPTION'].value_counts(dropna=False)

ftrMask = recalls['RECALL_TYPE_DESCRIPTION'].str.contains('FTR|Fixed', case=False)

recalls['FIXED_OR_STANDARD'] = 'Standard'
recalls.loc[ftrMask,'FIXED_OR_STANDARD']='Fixed'

# Create quarter and year variables ------------------------------------
recalls['YEAR'] = recalls['LICENCE_REVOKE_DATE'].dt.to_period('Y')
recalls['YEAR_QUARTER'] = recalls['LICENCE_REVOKE_DATE'].dt.to_period('Q')

# recalls[['DOB','LICENCE_REVOKE_DATE','YEAR_QUARTER','AGE_AT_RECALL','AGEBAND_AT_RECALL']].tail()

# Breakdown to answer the FOI questions -------------------------------------
    # (2,3,4) Total FTR, STD recalls by quarter, 2017,...,2023

pd.pivot_table(recalls,
               index=['YEAR_QUARTER'],
               columns=['FIXED_OR_STANDARD'],
               dropna=False,
               aggfunc='size',  # Counting the number of occurrences
               fill_value=0     # Replace NaN with 0
              ).reset_index()

     # (5) Total FTR recalls by year, 2017,...,2023

pd.pivot_table(recalls[recalls['FIXED_OR_STANDARD'] == 'Fixed'],
               index=['AGEBAND_AT_RECALL'],
               columns=['YEAR'],
               dropna=False,
               aggfunc='size',  # Counting the number of occurrences
               fill_value=0     # Replace NaN with 0
              ).reset_index()


# ----------------------------------------Second FTR recalls in 2023-----------------------------------
    # Concatenate fresh extracts
rec_file_names = ['Recalls_up_to_2009.xls','Recalls_2012_2013.xls','Recalls_2014_2016.xls','Recalls_2017_2018.xls','Recalls_2019_2020.xls','Recalls_2021_2022.xls','Recalls_2023.xls'] # file names on amazon

extract_fixed = pd.DataFrame() # start with an empty dataframe to capture all PPUD fixed term recalls up to Sep 2023

for filename in rec_file_names:
    rec = pd.read_excel(f"s3://alpha-omppg/Data Central/PPUD Recalls/{filename}")
    rec = rec[rec['RECALL_TYPE_DESCRIPTION'].str.contains('FTR|Fixed', case=False)] # keep only fixed-term recalls
    extract_fixed = pd.concat([extract_fixed,rec],axis = 0, ignore_index= True) # concatenate

extract_fixed.shape # 96804.

extract_fixed['RECALL_TYPE_DESCRIPTION'].value_counts(dropna=False)

  
# Create year variables in both datasets

# pub_fixed['YEAR'] = pub_fixed['LICENCE_REVOKE_DATE'].dt.to_period('Y')
extract_fixed['YEAR'] = extract_fixed['LICENCE_REVOKE_DATE'].dt.to_period('Y')

# Determine recall number for each combination of date of sentence and licence revocation date

extract_fixed['DOS'].isna().sum() # 2 cases with missing date of sentece, good
extract_fixed['LICENCE_REVOKE_DATE'].isna().sum() # 0
extract_fixed['NOMS_ID'].isna().sum() # 2839
extract_fixed['FILE_REFERENCE'].isna().sum() # 36
extract_fixed['PRISON_NUMBER'].isna().sum() # 2

# check duplicates
extract_fixed.duplicated(['PRISON_NUMBER','DOS','LICENCE_REVOKE_DATE'],keep='first').sum() # 8
extract_fixed.duplicated(['PRISON_NUMBER','LICENCE_REVOKE_DATE'],keep='first').sum() # 13

    # remove duplicate prison number and licence revoke date
extract_fixed = extract_fixed.sort_values(['PRISON_NUMBER','LICENCE_REVOKE_DATE'])

extract_fixed = extract_fixed.drop_duplicates(['PRISON_NUMBER','LICENCE_REVOKE_DATE'])
extract_fixed.shape #96791,42

    # Count fixed-term recalls per year
# pub_fixed['YEAR'].value_counts(dropna=False).sort_index() # should start from 2013 Q4 to 2023 Q3.
year = 2023
extract_fixed[extract_fixed['LICENCE_REVOKE_DATE'].dt.year == year]['YEAR'].value_counts(dropna=False).sort_index() #6642

    # count the recall number for each combination of prison number, dos and licence revoke date

extract_fixed = extract_fixed.sort_values(['PRISON_NUMBER','DOS','LICENCE_REVOKE_DATE'])

extract_fixed['RECALL_NUMBER'] = extract_fixed.groupby(['PRISON_NUMBER','DOS']).cumcount() + 1

retain = ['FILE_REFERENCE','FAMILY_NAME','DOS','LICENCE_REVOKE_DATE','RECALL_NUMBER','RECALL_TYPE_DESCRIPTION']

extract_fixed = extract_fixed[retain +[col for col in extract_fixed.columns if col not in retain]]

extract_fixed.head(50)

# Keep only the second fixed-term recalls
rec_2023 = extract_fixed[extract_fixed['LICENCE_REVOKE_DATE'].dt.year == year].copy()
second_ft_recalls_2023 = rec_2023[rec_2023['RECALL_NUMBER'] == 2]

second_ft_recalls_2023.shape[0] # 951

# tabulate to answer
    # number of second recall per year
    second_ft_recalls_2023['YEAR'].value_counts(dropna=False).sort_index()
    
    # number of recalls per year
    rec_2023['YEAR'].value_counts(dropna=False).sort_index()

#Conclusion
"""
Whave 951/6642 approx 14% of all FTR in 2023 being second fixed-term recall."""