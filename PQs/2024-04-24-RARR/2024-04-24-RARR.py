""" 
GOAL: RARR (FORMERLY EXECUTIVE RERELEASES
By Eric Nyame, 24/04/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
# import duckdb
# import importlib

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
# from my_log import my_log
import Out_of_bounds_dates
# importlib.reload(Out_of_bounds_dates)
# import prepareMatch
# importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
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

# Import rarr and rescinds
rarr = pd.read_excel("s3://alpha-omppg/PQs/2024-04-24-RARR/2024-04-24-RARR.xls")
rescinds =  pd.read_excel("s3://alpha-omppg/PQs/2024-04-24-RARR/2024-04-25-Rescinded RARR.xls")

#check shapes
rarr.shape # 10664
rescinds.shape # 58

# check data types are as expected - datetimes inparticular
rarr.info()
rescinds.info()

# view few lines
rarr.head()

# rearrange columsn
retain = ['ACTUAL','PRISON_NUMBER','FAMILY_NAME','FILE_REFERENCE','REVIEW_ID','REVIEW_TYPE_DESCRIPTION']
rarr = rarr[retain + [col for col in rarr.columns if col not in retain]]

# deduplicate on all
rarr = rarr.drop_duplicates()
rarr.shape # same

# Deduplicate RARR keeping the latest Actual date, first on review id then on prison number + actual
rarr = rarr.sort_values(['REVIEW_ID','ACTUAL'], ascending=[True,False]) # descending on ACTUAL
rarr[rarr.duplicated(['REVIEW_ID'], keep = False)].head(20)

rarr = rarr.drop_duplicates(['REVIEW_ID'])
rarr.shape # 10596

 # Deduplicate on Prison number 
rarr = rarr.sort_values(['PRISON_NUMBER','ACTUAL'])
rarr[rarr.duplicated(['PRISON_NUMBER','ACTUAL'], keep = False)].head(50) # none

# Are all titles about release?
rarr['TITLE'].str.contains('release',case=False,na=False).all() # True

# Remove Test cases
    # Check 'test' cases and remove
rarr[rarr['FAMILY_NAME'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] #0

rarr[rarr['FIRST_NAMES'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

Test_Case_Mask =  (   (rarr['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (rarr['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (rarr['FILE_REFERENCE'] != 'T18122')

rarr = rarr[~Test_Case_Mask]

# Deduplicate Rescinds by keeping the latest ACTUAL on review id, then on prison number + actual

rescinds = rescinds.sort_values(['REVIEW_ID','ACTUAL'], ascending=[True,False])
rescinds[rescinds.duplicated(['REVIEW_ID'], keep = False)].head(20) # none

# convert review_id and actual in rescinds into a dictionary
zipper = zip(rescinds['REVIEW_ID'],rescinds['ACTUAL'])
dict_rescind = dict(zipper)

# add rescind actual by mapping rarr to the resinds dictionary
rarr['RESCIND_ACTUAL'] = rarr['REVIEW_ID'].map(dict_rescind)

# determine if an RARR is a rescind or not. If the rescind data come after the RARR date, then it is rescinded.
rarr['RESCINDED'] = False
condition_rescind = rarr['RESCIND_ACTUAL'] >= rarr['ACTUAL']
rarr.loc[condition_rescind,'RESCINDED'] = True

# check the rescinded cases
(rarr['RESCINDED']==True).sum() # 50 cases

rarr[rarr['RESCINDED']==True].head()

# create RARR year
rarr['YEAR_ACTUAL'] = rarr['ACTUAL'].dt.to_period('Y')

# save to send
rarr.to_excel("s3://alpha-omppg/PQs/2024-04-24-RARR/2024-04-25-RARR_final.xlsx",index = False)


#---------------Breakdown
    # The want to know cases from 7 September to 31 December.
    
sep_dec_cond = (rarr['ACTUAL'] >= pd.Timestamp(2023,9,7)) & (rarr['ACTUAL'] <= pd.Timestamp(2023,12,31))

may_end_cond = rarr['ACTUAL'] <= pd.Timestamp(2023,5,31)

sep_dec_cond.sum() # 94 cases

rarr['SEP_NOV'] = False
rarr.loc[sep_dec_cond,'SEP_NOV'] = True

# all RARRs decisions made incuding where later recinded
rarr.groupby('YEAR_ACTUAL').size()

# all RARRs decisions made excluding where later recinded
rarr[rarr['RESCINDED']==False].groupby('YEAR_ACTUAL').size()

# sep-Dec RARRs decisions made incuding where later recinded
rarr.groupby('SEP_NOV').size()

# sep-Dec RARRs decisions made incuding where later recinded
rarr[rarr['RESCINDED']==False].groupby('SEP_NOV').size()

# May cond
rarr[may_end_cond].groupby('YEAR_ACTUAL').size()
rarr[may_end_cond & (rarr['RESCINDED']==False)].groupby('YEAR_ACTUAL').size()
