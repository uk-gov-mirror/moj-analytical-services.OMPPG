""" 
FOI
Please provide the following data for each of the following prisons:
 
HMP Highpoint
HMP Peterborough
HMP Bure
HMP Wayland
 
For the period from 1 July 2024 to the present date:
The number of prisoners released from each prison.
Of those released, the number who were subsequently recalled to custody.

08-08-2025
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

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
#importlib.reload(Out_of_bounds_dates)
import prepareMatch
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


# Import NOMIS release data - from Dan's team

releases = pd.read_excel("s3://alpha-omppg/FOI/2025-08-08-Releases-and-Recalls/2025-08-08-FOI-25-07-16-020.xlsx")

"""
len(releases) # 1938 unique first-time releases (not individuals) on a sentence
"""

# upper case columns
releases.columns = releases.columns.str.upper()

"""
releases.head()

# check missing noms_no in the release data - should be none
sum(releases['NOMS_NO'].isna()) # 0 as expected

# check duplicate release date (same as movement date) (not individuals) in the release data
sum(releases.duplicated(['NOMS_NO','MOVEMENT_DATE'],keep=False)) # 0 as expected

# check duplicate individuals - this is for information only and is not to be corrected
# these are genuine duplicates because of releases on different sentences (different SED_PRIOR)

sum(releases.duplicated('NOMS_NO',keep=False)) # 213 rows.

releases = releases.sort_values(by =['NOMS_NO','MOVEMENT_DATE'])

releases[releases.duplicated('NOMS_NO',keep=False)].head(10)
"""
# Bring in recalls - to cover 1 July 2024 to 31 March 2025 inclusive 

rec1 = pd.read_parquet("s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2024q2.parquet")
rec2 = pd.read_parquet("s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2024q3.parquet")
rec3 = pd.read_parquet("s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2024q4.parquet")
rec4 = pd.read_parquet("s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2024q1.parquet")

# put the quarterly data together

recalls = pd.concat([rec1,rec2,rec3,rec4],axis=0)

"""
len(recalls) # 40259, check length against published totals

recalls.info()
recalls.pivot_table(index='NOMS_REGION_DESCRIPTION',columns='FURTHER_CHARGE',aggfunc='size')
recalls.head()
"""

# make upper case the columns of releases
releases.columns = releases.columns.str.upper() 

# Normalize licence revoke date as they can erroneously not be linked to release dates
# removes the time part of the licence revocation date

recalls.info() # check to see licence revocation date is datetime

recalls['LICENCE_REVOKE_DATE'] = recalls['LICENCE_REVOKE_DATE'].dt.normalize()

# Keep only recalls from 1 July 2024 to match when the releases start

recalls = recalls[recalls['LICENCE_REVOKE_DATE'] >= pd.Timestamp(2024,7,1)]

"""
len(recalls) # 30477

# Check missing NOMIS ID in recall data
recalls[recalls['NOMS_ID'].isna()].shape[0] # 2 cases

recalls[recalls['NOMS_ID'].isna()]
"""
# add Nomis id for one of them. The other has no NOmis id on PPUD 

recalls.loc[recalls['FILE_REFERENCE']=='PPU_420860','NOMS_ID'] = 'A4339FG'

# No NOMIS ID for file reference T17614. Not a problem because his last release was in 2020, outside this FOI period.

# There should be no duplicate recall date for the same offender

recalls[recalls.duplicated(['PRISON_NUMBER','LICENCE_REVOKE_DATE'],keep=False)] # 0 as expected

# Movement data or release date should be of type datetime
releases.info()

# There should be no duplicate movement date for the same offender
releases = releases.sort_values(['NOMS_NO','MOVEMENT_DATE'])

releases[releases.duplicated(['NOMS_NO','MOVEMENT_DATE'],keep=False)].head() # 0 as expected

"""
len(releases) # 1938
"""

# Identify next release dates to capture recalls appropriately
releases = releases.sort_values(by=['NOMS_NO', 'MOVEMENT_DATE'])

releases['NEXT_RELEASE'] = releases.groupby('NOMS_NO')['MOVEMENT_DATE'].shift(periods = -1)

"""
releases[releases.duplicated('NOMS_NO',keep=False)].head(10)
"""

   # if no next release, then set next release data to 31 March 2025 to capture releases up to and on 31March2025
releases.loc[releases['NEXT_RELEASE'].isna(),'NEXT_RELEASE'] = pd.Timestamp(2025,3,31)

"""
# check duplicate cases to see how next release data worked

releases[releases.duplicated('NOMS_NO',keep=False)][['NOMS_NO','SURNAME','MOVEMENT_DATE','NEXT_RELEASE']].head(10)

# Check releasing prisons match those requested

releases['PRISON_NAME'].unique()
"""

# Function to clean recall nomis id and prison numbers for matching
recalls = prepareMatch.prepareMatch(recalls)

recalls['NOMS_LENGTH'].value_counts(dropna=False)
recalls.head()
recalls[recalls['NOMS_LENGTH'] > 7]
# join query

query = """SELECT a.*, 
                  b.LICENCE_REVOKE_DATE,
                  b.RTC_DATE
                  
            FROM releases AS a LEFT JOIN recalls AS b
            
            ON  
                (a.NOMS_NO = b.NOMS_ID OR
                 a.NOMS_NO = b.NOMS_TRIM OR
                 a.NOMS_NO = b.NOMS_START OR
                 a.NOMS_NO = b.NOMS_END OR
                 a.NOMS_NO = b.PRISON_NUMBER OR
                 a.NOMS_NO = b.PN_TRIM OR
                 a.NOMS_NO = b.PN_START OR
                 a.NOMS_NO = b.PN_END) AND
            a.MOVEMENT_DATE <= b.LICENCE_REVOKE_DATE AND
            a.NEXT_RELEASE >= b.LICENCE_REVOKE_DATE""" # next release is from a new sentence

matched = duckdb.sql(query).df()
len(matched) # 2184
matched.head()

"""
matched.to_excel('matched_cases.xlsx',index=False)
"""

# Isolate releases that had no recalls
non_matches = matched[matched['LICENCE_REVOKE_DATE'].isna()]

"""
len(non_matches) # 1371 
"""

# keep only cases that had a match to recall data

matched = matched[~matched['LICENCE_REVOKE_DATE'].isna()]

"""
len(matched) # 813 including multiple recalls on the same sentence

matched.head()

# Number of recalls per person
matched['RECALL_NUM'] = matched.groupby(['NOMS_NO','MOVEMENT_DATE']).transform('size')
len(matched)
matched.head()

# identify multiple recalls
matched['MULT_RECALL']= 'once'
matched.loc[matched['RECALL_NUM'] > 1,'MULT_RECALL'] = 'mult'
"""

# Deduplicate by Noms and movement date

matched = matched.sort_values(['NOMS_NO','MOVEMENT_DATE'])

"""
matched[matched.duplicated(['NOMS_NO','MOVEMENT_DATE'],keep=False)][['NOMS_NO','SURNAME','MOVEMENT_DATE','LICENCE_REVOKE_DATE','NEXT_RELEASE','SED_PRIOR','RECALL_NUM']].head(10) # 0

matched[matched.duplicated('NOMS_NO',keep=False)][['NOMS_NO','SURNAME','MOVEMENT_DATE','LICENCE_REVOKE_DATE','NEXT_RELEASE','SED_PRIOR','RECALL_NUM']].tail(10)
"""

matched2 = matched.drop_duplicates(['NOMS_NO','MOVEMENT_DATE'],keep='first')

"""
len(matched2) # 567 out of 1938

# Save to folder

matched2.to_excel('s3://alpha-omppg/FOI/2025-08-08-Releases-and-Recalls/matched_cases.xlsx',index=False)
"""