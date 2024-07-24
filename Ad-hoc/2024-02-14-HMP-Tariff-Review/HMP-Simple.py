""" 
GOAL: 
Total HMP cohort broken down by:
    1. Date of sentence
    2. Current age
    3. Age at sentencing
    4. Age at time of the offence (I understand that this will depend on whether the correct PPUD field has been utilised, but the field is not mandatory)
    5. HMP halfway date
    6. Tariff expiry date
    7. Whether they have already had a hm tariff review and whether they have had any subsequent reviews
    8. If they have had a review already, what was the outcome
    9. HMP cases which pre-date the legislative change (change came into effect on 18 February 2021 – how many have already had a review under the old legislation
    10. Cases who have joined the cohort since the legislative change

By Eric Nyame, 14/02/2024
"""
#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys # for adding folders to the search path
import duckdb
from datetime import datetime
import importlib

import re

from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
from my_log import my_log
from Out_of_bounds_dates import date_out_of_bounds
import prepareMatch 
importlib.reload(prepareMatch)

# Set display options

pd.options.display.max_columns = None
pd.options.display.max_rows = None

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>


#----------------------------------Import PPUD data

hmp_simple = pd.read_excel("s3://alpha-omppg/Ad hoc/2024 02 14 HMP Tariff Review/HMP Simple As At 14Feb2024.xls")
hmp_simple.info()
hmp_simple.columns
keep_mask = ['FILE_REFERENCE','FAMILY_NAME','DOS','TARIFF_EXPIRY_DATE', 'INDEX_OFFENCE_DATE', 'DOB', 
       'CUSTODY_TYPE_DESCRIPTION', 'FIRST_NAMES', 'GENDER', 'INDEX_OFFENCE_DESCRIPTION', 'OFFENDER_ID', 'NOMS_ID', 'PRISON_NUMBER','STATUS_DESCRIPTION']

hmp_simple = hmp_simple[keep_mask]
hmp_simple.info()
hmp_simple.head(20)

hmp_tariff = pd.read_excel("s3://alpha-omppg/Ad hoc/2024 02 14 HMP Tariff Review/HMP Tariff As At 14Feb2024.xls")
hmp_tariff.info()
hmp_tariff.columns
keep_mask_2 = ['FILE_REFERENCE', 'HMP_HALFWAY', 'OFFENDER_ID', 'NOMS_ID', 'PRISON_NUMBER', 'DOS','TARIFF_EXPIRY_DATE']

hmp_tariff = hmp_tariff[keep_mask_2]
hmp_tariff.info()
hmp_tariff.head()

#----------------------------------Merge the two
query = """SELECT a.*, 
                  b.HMP_HALFWAY,
          FROM hmp_simple AS a LEFT JOIN hmp_tariff AS b 
            ON  
                ( (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) OR
                  (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                  (a.NOMS_ID = b.NOMS_ID AND a.NOMS_ID IS NOT NULL) 
                )          
                """

hmp_combined = duckdb.sql(query).df()
hmp_combined.info()
hmp_combined.head()

#----------------------------------View duplicated cases

hmp_combined[hmp_combined.duplicated(subset='OFFENDER_ID',keep=False)] # None, good
hmp_combined[hmp_combined.duplicated(subset='FILE_REFERENCE',keep=False)] # None, wow!

#---------------------------------- Add Tariff Review Data
cstt_Reviews_final = pd.read_pickle('cstt_Reviews_final.pkl')
cstt_Reviews_final.info()

query2 = """SELECT a.*, 
                  b.REVIEW_DATE,
                  b.n_COMPLETED,
                  b.n_REDUCED,
                  b. n_UNCHANGED,
                  b. n_ACTIVE,
                  b.REVIEW_RESULT_DESCRIPTION AS LATEST_REVIEW_OUTCOME
                  
          FROM hmp_combined AS a LEFT JOIN cstt_Reviews_final AS b 
            ON  
                ( (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) OR
                  (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                  (a.NOMS_ID = b.NOMS_ID AND a.NOMS_ID IS NOT NULL) 
                ) AND (a.TARIFF_EXPIRY_DATE == b.TARIFF_EXPIRY_DATE AND a.TARIFF_EXPIRY_DATE IS NOT NULL)        
                """

hmp_combined_final = duckdb.sql(query2).df()
hmp_combined_final.info()
hmp_combined_final.head()

#----------------------------------View duplicated cases

hmp_combined_final[hmp_combined_final.duplicated(subset='OFFENDER_ID',keep=False)] # None, good
hmp_combined_final[hmp_combined_final.duplicated(subset='FILE_REFERENCE',keep=False)] # None, wow!

#---------------------------------- Determine answers

# ---------- Current age
hmp_combined_final['CURRENT_AGE'] = datetime.now().year - hmp_combined_final['DOB'].dt.year
    
    # adjust age by month and day
month_mask = hmp_combined_final['DOB'].dt.month < datetime.now().month
day_mask = ( (hmp_combined_final['DOB'].dt.month == datetime.now().month) & 
             (hmp_combined_final['DOB'].dt.day <= datetime.now().day)
           )
month_day_mask = month_mask | day_mask

hmp_combined_final['CURRENT_AGE2'] = np.where(month_day_mask,hmp_combined_final['CURRENT_AGE'],hmp_combined_final['CURRENT_AGE']-1)

hmp_combined_final[hmp_combined_final['CURRENT_AGE2'] !=hmp_combined_final['CURRENT_AGE']][['DOB','CURRENT_AGE','CURRENT_AGE2']].head()
hmp_combined_final['CURRENT_AGE']  = hmp_combined_final['CURRENT_AGE2']
hmp_combined_final.drop('CURRENT_AGE2', axis=1,inplace = True)

hmp_combined_final.info()
hmp_combined_final.head()

# ---------- Age at Sentence
hmp_combined_final['AGE_AT_SENTENCE'] = hmp_combined_final['DOS'].dt.year - hmp_combined_final['DOB'].dt.year
    
    # adjust age at sentence by month and day
month_mask = hmp_combined_final['DOB'].dt.month < hmp_combined_final['DOS'].dt.month
day_mask = ( (hmp_combined_final['DOB'].dt.month == hmp_combined_final['DOS'].dt.month) & 
             (hmp_combined_final['DOB'].dt.day <= hmp_combined_final['DOS'].dt.day)
           )
month_day_mask = month_mask | day_mask

hmp_combined_final['AGE_AT_SENTENCE2'] = np.where(month_day_mask,hmp_combined_final['AGE_AT_SENTENCE'],hmp_combined_final['AGE_AT_SENTENCE']-1)

hmp_combined_final[hmp_combined_final['AGE_AT_SENTENCE'] !=hmp_combined_final['AGE_AT_SENTENCE2']][['DOB','DOS','AGE_AT_SENTENCE','AGE_AT_SENTENCE2']].head()

hmp_combined_final['AGE_AT_SENTENCE']  = hmp_combined_final['AGE_AT_SENTENCE2']
hmp_combined_final.drop('AGE_AT_SENTENCE2', axis=1,inplace = True)

hmp_combined_final.info()
hmp_combined_final.head()

hmp_combined_final['STATUS_DESCRIPTION'].value_counts(dropna=False)

# ---------- Convert datetimes to date
datetimeCols = hmp_combined_final.select_dtypes(include = 'datetime64').columns
datetimeCols

for col in datetimeCols:
    hmp_combined_final[col] = hmp_combined_final[col].dt.date


# ---------- Cases before legislative change on 18 February 2021 
hmp_combined_final = pd.read_pickle('hmp_combined_final.pkl')
hmp_combined_final['REVIEW_DATE'].dt.year.value_counts().sort_index()
hmp_combined_final[~hmp_combined_final['REVIEW_DATE'].isna()]['HMP_HALFWAY'].dt.year.value_counts().sort_index()

hmp_combined_final.to_pickle('hmp_combined_final.pkl')
hmp_combined_final.to_excel('hmp_combined_final.xlsx',index_label=None)

