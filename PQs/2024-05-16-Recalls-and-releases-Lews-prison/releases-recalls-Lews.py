""" 
26110| Ordinary
To ask the Secretary of State for Justice, how many prisoners in HMP Lewes were (a) released as street homeless and (b) released and recalled (i) once and (ii) multiple times in each of the last six MONTHs.

By Eric Nyame, 16/05/2024
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


# ------------------ Import data

releases = pd.read_csv("s3://alpha-omppg/PQs/2024-05-16-Recalls-and-releases-Lews-prison/PQ-26-110-for-Eric.csv")
recalls = pd.read_excel("s3://alpha-omppg/Data Central/PPUD Recalls/Recalls_2023.xls")

# make uppder case the columns of releases
releases.columns = releases.columns.str.upper()

# Keep only last 6 MONTHs of recall data
last_6_MONTH_cond = (recalls['LICENCE_REVOKE_DATE'].dt.month > 6)
last_6_MONTH_cond.sum()
recalls = recalls[last_6_MONTH_cond]
recalls.shape # 14179

# There should be no duplicated recall date for the same offender
recalls[recalls.duplicated(['PRISON_NUMBER','LICENCE_REVOKE_DATE'],keep=False)] # 0

# Normalize licence revoke date and movement date
releases.info()
recalls['LRD'] = recalls['LICENCE_REVOKE_DATE'].dt.normalize()
releases['MOVEMENT_DATE'] = pd.to_datetime(releases['MOVEMENT_DATE'],dayfirst=True).dt.normalize()

# There should be no duplicated movement date for the same offender
releases[releases.duplicated(['NOMS_NO','MOVEMENT_DATE'],keep=False)] # 0

# Identify next release dates to capture recalls appropriately
releases = releases.sort_values(by=['NOMS_NO', 'MOVEMENT_DATE'])
releases['NEXT_RELEASE'] = releases.groupby('NOMS_NO')['MOVEMENT_DATE'].shift(-1)

    # if no next release, then set next release data to 1 Jan 2024 to capture releases up to and on 31 Dec
releases.loc[releases['NEXT_RELEASE'].isna(),'NEXT_RELEASE'] = pd.Timestamp(2024,1,1)

# check duplicate case to see how next review data worked
releases[releases.duplicated('NOMS_NO',keep=False)][['NOMS_NO','MOVEMENT_DATE','NEXT_RELEASE']]

# Match
query = """SELECT a.*, 
                  b.NOMS_NO,
                  b.MOVEMENT_DATE
                  
            FROM recalls AS a INNER JOIN releases AS b
            
            ON  a.NOMS_ID = b.NOMS_NO AND
            a.LRD >= b.MOVEMENT_DATE AND
            a.LRD < b.NEXT_RELEASE"""

matched = duckdb.sql(query).df()
len(matched) #112

matched.head()

# identify MONTH of recall
matched['MONTH'] = matched['MOVEMENT_DATE'].dt.month
matched.head()

# Number of recalls per person per month
matched['RECALL_NUM'] = matched.groupby(['NOMS_NO', 'MONTH']).transform('size')
len(matched)

# identify multiple recaos
matched['MULT_RECALL']= 'once'
matched.loc[matched['RECALL_NUM'] > 1,'MULT_RECALL'] = 'mult'

matched[matched.duplicated(['NOMS_NO','MONTH'],keep=False)]

# Deduplicated by Noms and MONTH
matched = matched.sort_values(['NOMS_NO','MONTH'])

matched = matched.drop_duplicates(['NOMS_NO','MONTH'])   # remove duplicate prison number and licence revoke date
len(matched2) # 97

# Deduplicated by Noms and MONTH
matched = matched.sort_values(['NOMS_NO','MOVEMENT_DATE'])

matched = matched.drop_duplicates(['NOMS_NO','MONTH'])   # remove duplicate prison number and licence revoke date
len(matched2) # 97
# Tabulate
pd.pivot_table(matched,
               index='MONTH',
               columns='MULT_RECALL',
               dropna=False,
               aggfunc='size',  # Counting the number of occurrences
               fill_value=0).reset_index()

