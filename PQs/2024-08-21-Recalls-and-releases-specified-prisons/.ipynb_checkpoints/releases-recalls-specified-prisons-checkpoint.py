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


# Import NOMIS release data

releases = pd.read_excel("s3://alpha-omppg/PQs/2024-08-21-Recalls-and-releases-specified-prisons/PQs_2231_2232.xlsx")
len(releases) # 63825


# recalls = pd.read_excel("s3://alpha-omppg/Data Central/PPUD Recalls/Recalls_2023.xls")

# Bring in recalls - start with 2024Q1 and add 2023 q2-q4 
quarters =['q2','q3','q4']

recalls = pd.read_parquet("s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2024q1.parquet") 

for quarter in quarters:
    # import the file if it's a SAS file and name it pop_year
    try:
        quart_recs = pd.read_sas(f"s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2023{quarter}.sas7bdat", encoding='latin1')
        quart_recs.columns = quart_recs.columns.str.upper()
        print(f"Loaded SAS file for {quarter}")
    except Exception as e:
        print(f"Failed to load SAS file for {quarter}, error: {e}")
        # else if the file is not SAS, import it if it's a parquet file
        try:
            quart_recs = pd.read_parquet(f"s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2023{quarter}.parquet")
            quart_recs.columns = quart_recs.columns.str.upper()
            print(f"Loaded Parquet file for {quarter}")
        except Exception as e:
            print(f"Failed to load Excel file for {quarter}, error: {e}")
  
    recalls = pd.concat([recalls,quart_recs],axis=0)

len(recalls) # 28411, check length against published totals

recalls.head()
releases.columns = releases.columns.str.upper() # make uppder case the columns of releases

# Keep only last 12 MONTHs of recall data
recalls['LICENCE_REVOKE_DATE'].dt.month.value_counts(dropna=False)
last_12_MONTHS_cond = (recalls['LICENCE_REVOKE_DATE'].dt.month > 12)
last_12_MONTHS_cond.sum()
recalls = recalls[last_12_MONTHS_cond]
recalls.shape # 14179

# Check missing NOMIS ID
recalls[recalls['NOMS_ID'].isna()].shape[0] # 2

recalls[recalls['NOMS_ID'].isna()]

# There should be no duplicate recall date for the same offender
recalls[recalls.duplicated(['PRISON_NUMBER','LICENCE_REVOKE_DATE'],keep=False)] # 0

# Normalize licence revoke date and movement date
releases.info()
recalls['LRD'] = recalls['LICENCE_REVOKE_DATE'].dt.normalize()
# releases['MOVEMENT_DATE'] = pd.to_datetime(releases['MOVEMENT_DATE'],dayfirst=True).dt.normalize()

# There should be no duplicate movement date for the same offender
releases = releases.sort_values(['NOMS_NO','MOVEMENT_DATE'])
releases[releases.duplicated(['NOMS_NO','MOVEMENT_DATE'],keep=False)].head() # 0

releases_unique = releases.drop_duplicates(['NOMS_NO','MOVEMENT_DATE'],keep='first')
len(releases_unique) # 50536, matches OMSQ

# Identify next release dates to capture recalls appropriately
releases_unique = releases_unique.sort_values(by=['NOMS_NO', 'MOVEMENT_DATE'])
releases_unique['NEXT_RELEASE'] = releases_unique.groupby('NOMS_NO')['MOVEMENT_DATE'].shift(periods = -1)
releases_unique[releases_unique['NOMS_NO']=='A1189EX']

    # if no next release, then set next release data to 1 April 2024 to capture releases up to and on 31 Dec
releases_unique.loc[releases_unique['NEXT_RELEASE'].isna(),'NEXT_RELEASE'] = pd.Timestamp(2024,4,1)
releases_unique.head(10)

# check duplicate case to see how next release data worked
releases_unique[releases_unique.duplicated('NOMS_NO',keep=False)][['NOMS_NO','MOVEMENT_DATE','NEXT_RELEASE']].head()

#Keep relevant prisons
releases_relevant = releases_unique[releases_unique['FROM_PRISON_NAME'].str.contains('Peterborough|Lincoln', case=False)]
releases_relevant['FROM_PRISON_NAME'].value_counts()
len(releases_relevant) # 2315

releases_relevant
# Match
recalls = prepareMatch.prepareMatch(recalls)
recalls.head()

query = """SELECT a.*, 
                  b.NOMS_NO,
                  b.MOVEMENT_DATE,
                  b.FROM_PRISON_NAME,
                  b.NEXT_RELEASE
                  
            FROM recalls AS a INNER JOIN releases_relevant AS b
            
            ON  
                (b.NOMS_NO = a.NOMS_ID OR
                 b.NOMS_NO = a.NOMS_TRIM OR
                 b.NOMS_NO = a.NOMS_START OR
                 b.NOMS_NO = a.NOMS_END OR
                 b.NOMS_NO = a.PRISON_NUMBER OR
                 b.NOMS_NO = a.PN_TRIM OR
                 b.NOMS_NO = a.PN_START OR
                 b.NOMS_NO = a.PN_END) AND
            a.LRD >= b.MOVEMENT_DATE AND
            a.LRD < b.NEXT_RELEASE""" # next release is from a new sentence

matched = duckdb.sql(query).df()
len(matched) #964
matched.head()

# Number of recalls per person
matched['RECALL_NUM'] = matched.groupby(['NOMS_NO','MOVEMENT_DATE']).transform('size')
len(matched)
matched.head()
matched[matched['NOMS_NO'] =='A1189EX']

# identify multiple recaos
matched['MULT_RECALL']= 'once'
matched.loc[matched['RECALL_NUM'] > 1,'MULT_RECALL'] = 'mult'

# Deduplicated by Noms, MOVE AND RECALL
matched = matched.sort_values(['NOMS_NO','MOVEMENT_DATE'])
matched[matched.duplicated(['NOMS_NO','MOVEMENT_DATE'],keep=False)][['NOMS_NO','FAMILY_NAME','MOVEMENT_DATE','LRD','NEXT_RELEASE','RECALL_NUM']].head(10) # 0

matched[matched.duplicated(['NOMS_NO','MOVEMENT_DATE','LRD'],keep=False)][['NOMS_NO','FAMILY_NAME','MOVEMENT_DATE','LRD','NEXT_RELEASE','RECALL_NUM']].head(10) # 0
len(matched) # 964


matched = matched.sort_values(['NOMS_NO','MOVEMENT_DATE'])
matched2 = matched.drop_duplicates(['NOMS_NO','MOVEMENT_DATE'],keep='first')

matched2.head(100)
len(matched2) # 804

# Tabulate
pd.pivot_table(matched2,
               index='FROM_PRISON_NAME',
               columns='MULT_RECALL',
               dropna=False,
               aggfunc='size',  # Counting the number of occurrences
               fill_value=0).reset_index()

matched2.to_excel('final_unique.xlsx',index=False)
matched.to_excel('final_not_unique.xlsx',index=False)
