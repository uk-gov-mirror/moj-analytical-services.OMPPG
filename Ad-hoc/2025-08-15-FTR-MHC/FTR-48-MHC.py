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

15-08-2025
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

mhc = pd.read_excel("s3://alpha-omppg/Ad-hoc/2025-08-15-FTR-MHC/DA-as-at-14-08.xlsx")

recalls =  pd.read_excel("s3://alpha-omppg/Ad-hoc/2025-08-15-FTR-MHC/recalls_3_years_to_14_Aug_2025.xlsx")

"""
mhc.head()

# check missing NOMS_ID in the release data - should be none
sum(mhc['NOMS_ID'].isna()) # 0 as expected

# check duplicate release date (same as movement date) (not individuals) in the release data
sum(mhc.duplicated(['NOMS_ID','MOVEMENT_DATE'],keep=False)) # 0 as expected

# check duplicate individuals - this is for information only and is not to be corrected
# these are genuine duplicates because of releases on different sentences (different SED_PRIOR)

sum(mhc.duplicated('NOMS_ID',keep=False)) # 213 rows.

releases = mhc.sort_values(by =['NOMS_ID','MOVEMENT_DATE'])

mhc[mhc.duplicated('NOMS_ID',keep=False)].head(10)

len(recalls) # 40259, check length against published totals

recalls.info()
recalls.pivot_table(index='NOMS_REGION_DESCRIPTION',columns='FURTHER_CHARGE',aggfunc='size')
recalls.head()
"""

"""
len(recalls) # 30477

# Check missing NOMIS ID in recall data
recalls[recalls['NOMS_ID'].isna()].shape[0] # 2 cases

recalls[recalls['NOMS_ID'].isna()]
"""

mhc.info()

"""
len(releases) # 1938
"""

# Missing nomis id
mhc.loc[mhc['NOMS_ID'].isna(),'NOMS_ID'] = mhc['FILE_REFERENCE']
recalls.loc[recalls['NOMS_ID'].isna(),'NOMS_ID'] = recalls['FILE_REFERENCE']

len(mhc) # 366

recalls.info()
# join query

query = """SELECT a.*, 
                  b.LICENCE_REVOKE_DATE,
                  b.RTC_DATE,
                  b.CURRENT_ESTABLISHMENT_DESCRIPTION AS RECALL_EST,
                  b.PART_TOTAL_IN_DAYS,
                  b.RECALL_TYPE_DESCRIPTION,
                  b.RELEASE_BEFORE_RECALL
                  
            FROM mhc AS a LEFT JOIN recalls AS b
            
            ON  (
                    (a.NOMS_ID = b.NOMS_ID) OR
                    (a.PRISON_NUMBER = b.PRISON_NUMBER)
                )
            """ 

matched = duckdb.sql(query).df()
len(matched) # 366

sum(~matched['LICENCE_REVOKE_DATE'].isna())

"""
matched.to_excel('matched_cases.xlsx',index=False)
"""