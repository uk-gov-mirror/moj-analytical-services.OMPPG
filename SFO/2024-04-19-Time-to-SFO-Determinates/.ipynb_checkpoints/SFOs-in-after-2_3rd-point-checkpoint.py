""" 
I am looking for some data on Fixed Term Recalls (as opposed to standard recalls) to custody across the last 5 years (2018-2023).

1.Total number of Fixed Term Recalls each year since 2018
2.The annual breakdown, by probation region, of Fixed Term Recalls to custody across the last 5 years
3.For the annual totals of FTRs across each of the last 5 years, the breakdown of top 3 reasons for recall? (i.e. 2020: X FTRs in total, Y% for reoffending, Z% for failure to reside, P% for failure to attend probation meeting.) 
4.I am looking for the % of all issued FTRs that were secondary FTRs on the same sentence. I.e. if 1000 were given in total, how many of these were given to the same person on the same sentence. (I would like this for every year from 2018) If it helps, for context, I am trying to understand the extent to which FTRs "work" - i.e. do individuals typically only require a single FTR to enforce engagement/compliance with their licence conditions.
5.By year, the proportion of total FTRs that were given during the licence PERIOD and the proportion that were given during PSS
6.The number of annual FTR recalls per the population in prison serving a sentence of 12 months or less on, say, 30 June, each year.
7.The 30th of June each year since 2018, what proportion of the total prison population was there on a Fixed Term Recall?

By Eric Nyame, 18/03/2024
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


#---------------------- Import Recall Data

       # import fresh fixed-term recall extracts from PPUD
    
rec_file_names = ['Recalls_up_to_2009.xls','Recalls_2012_2013.xls','Recalls_2014_2016.xls','Recalls_2017_2018.xls',
                  'Recalls_2019_2020.xls','Recalls_2021_2022.xls','Recalls_2023.xls','Recalls_Jan2024_to_18Apr2024.xls'] # file names on amazon

recalls = pd.DataFrame() # start with an empty dataframe to capture all PPUD fixed term recalls up to Sep 2023

for filename in rec_file_names:
    rec = pd.read_excel(f"s3://alpha-omppg/Data Central/PPUD Recalls/{filename}")
    recalls = pd.concat([recalls,rec],axis = 0, ignore_index= True) # concatenate

recalls.shape # 330650
recalls2 = recalls.copy()
recalls.info()

# check why licence_end and start are not datetime types
dateColsToChange =['LICENCE_END','LICENCE_START']
    
check1 = pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(recalls2,col)],axis = 0)

check1= check1[dateColsToChange + [col for col in recalls2.columns if col not in dateColsToChange]]
check1.head()
check1.shape #47 cases, mostly bad dates over the datetime limit of pandas. Set these to missing
check1

    # set bad dates to missing
recalls2.loc[recalls2['LICENCE_END'] > pd.Timestamp.max,'LICENCE_END'] = np.nan
recalls2.loc[recalls2['LICENCE_START'] > pd.Timestamp.max,'LICENCE_START'] = np.nan
    
    # change certain columns to pandas datetime type
for column in dateColsToChange:
    recalls2[column] = pd.to_datetime(recalls2[column])

recalls2.info()


# ----------------------------- Import SFO data
sfos = pd.read_excel("s3://alpha-omppg/Data Central/SFO/SFOs.xlsx")
sfos.info()

#-------------------------Add recall details to SFO

recalls2[recalls2['FILE_REFERENCE']=='PPU_186881']
# Match Terminations and Releases
query =  """SELECT a.*, 
                   b.RELEASE_BEFORE_RECALL,
                   b.LICENCE_REVOKE_DATE,
                   b.LICENCE_START,
                   b.LICENCE_END,
                   b.TYPE_OF_LICENCE_DESCRIPTION,
                   b.RECALL_REASON_DESCRIPTIONS,
                   b.RECALL_TYPE_DESCRIPTION,
                   b.DOS,
                   b.CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION,
                   b.CUSTODY_TYPE_DESCRIPTION
                   
            FROM sfos AS a LEFT JOIN recalls2 b 
            ON  (
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) OR
                    (a.NOMS_ID = b.NOMS_ID AND a.NOMS_ID IS NOT NULL) 
                ) AND
                a.PRISON_SENTENCE_START_DATE <= b.LICENCE_REVOKE_DATE"""

matched1 = duckdb.sql(query).df()
matched1.shape # 1297

matched1 = matched1.sort_values(['SFO_ID','LICENCE_REVOKE_DATE'])

retain = ['FILE_REFERENCE', 'FAMILY_NAME', 'PRISON_SENTENCE_START_DATE', 'DOS','PROBATION_SUPERVISION_START_DATE',
          'LICENCE_START','RELEASE_BEFORE_RECALL','DATE_OF_SFO','LICENCE_REVOKE_DATE','LICENCE_END',
          'CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION','STAGE_12_DOCN_RECEIVED_ACTUAL']

retain = retain + [col for col in matched1.columns if col not in retain]
matched1 = matched1[retain]
matched1.head()

    # deduplicate matched1
matched1['SHORTEST'] = abs((matched1['DATE_OF_SFO'] - matched1['LICENCE_REVOKE_DATE']).dt.days) # to identify the recall after the SFO

matched1.sort_values(['SFO_ID','SHORTEST'], inplace=True) # keep the earliest recall after the SFO

matched1 = matched1.drop_duplicates(subset=['SFO_ID']) 
matched1.shape # 1115

#-------------------------- Determine the PERIOD in which SFO_DATE falls

    # Calculating the thirds points and determining the PERIOD
matched1['PERIOD'] = round((matched1['LICENCE_END'] - matched1['PROBATION_SUPERVISION_START_DATE']).dt.days / 3) # number of days in a third of the entire time on licence
matched1['FIRST_THIRD'] = matched1['PROBATION_SUPERVISION_START_DATE'] + pd.to_timedelta(matched1['PERIOD'], unit='D') # first third endpoint
matched1['SECOND_THIRD'] = matched1['PROBATION_SUPERVISION_START_DATE'] + pd.to_timedelta(matched1['PERIOD']*2, unit='D') # second third endpoint/also start of the third point

matched1[['PROBATION_SUPERVISION_START_DATE','LICENCE_END','PERIOD','FIRST_THIRD','SECOND_THIRD']].head()


def determine_PERIOD(row):
    if pd.isna(row['PERIOD']):
        return " "
    elif row['DATE_OF_SFO'] <= row['FIRST_THIRD']:
        return 'FIRST_THIRD'
    elif row['DATE_OF_SFO'] <= row['SECOND_THIRD']:
        return 'SECOND_THIRD'
    else:
        return 'LAST_THIRD'
    
matched1['SFO_POINT'] = matched1.apply(determine_PERIOD, axis=1)

# Drop the auxiliary columns if they are no longer needed
matched1.drop(['PERIOD'], axis=1, inplace=True)

# Determine SFO's after 6 months following start of third point
   # Calculating the thirds points and determining the PERIOD

matched1.head()
matched1['SIX_MTHS_INTO_LAST_THIRD'] = matched1['SECOND_THIRD'] + pd.DateOffset(months=6) # six months after start of last third

matched1['SIX_MTHS_b4_LICENCE_END'] = np.nan
matched1.loc[matched1['SIX_MTHS_INTO_LAST_THIRD'] <= matched1['LICENCE_END'], 'SIX_MTHS_b4_LICENCE_END'] = 'YES'

retain = ['FILE_REFERENCE', 'FAMILY_NAME', 'PRISON_SENTENCE_START_DATE', 'DOS','PROBATION_SUPERVISION_START_DATE',      'LICENCE_START','RELEASE_BEFORE_RECALL','DATE_OF_SFO','LICENCE_REVOKE_DATE','LICENCE_END','FIRST_THIRD','SECOND_THIRD','SFO_POINT',
          'SIX_MTHS_INTO_LAST_THIRD','SIX_MTHS_b4_LICENCE_END', 'CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION','STAGE_12_DOCN_RECEIVED_ACTUAL']

retain = retain + [col for col in matched1.columns if col not in retain]
matched1 = matched1[retain]

matched1['LICENCE_REVOKE_DATE'] = pd.to_datetime(matched1['LICENCE_REVOKE_DATE']).dt.normalize()
matched1.head()
# Save
matched1.to_excel("matched_SFO.xlsx")
# matched1.to_excel(""s3://alpha-omppg/Data Central/SFO/matched_SFO.xlsx")
