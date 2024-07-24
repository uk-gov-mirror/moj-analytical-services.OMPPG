""" 
GOAL: the number of offenders that were recalled on a Fixed-Term Recall twice or more times on the same sentence, across the last 10 years.
By Eric Nyame, 18/03/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib

import re

from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
# from my_log import my_log
import Out_of_bounds_dates
importlib.reload(Out_of_bounds_dates)
import prepareMatch
importlib.reload(prepareMatch)
import openMatch
importlib.reload(openMatch)
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


# ***********************************A USE PUBLICATION DATASETS

years = [2013,2014,2015,2016,2017, 2018, 2019, 2020, 2021, 2022, 2023]
quarters =['q1','q2','q3','q4']

# concatenate all datasets over the required period

pub_fixed = pd.DataFrame() # start with an empty dataframe

for i in years:
    for j in quarters:
        if (i == 2013) and (j != 'q4'): # start from q4 2013 
            continue
        if (i == 2023) and (j =='q4'): # end at q3 2023
            break
        rec = pd.read_sas(f"s3://alpha-omppg/Recalls/Final Data/SAS/recalls_final_{i}{j}.sas7bdat", encoding='latin1')
        rec.columns = rec.columns.str.upper() # capitalise all headers
        rec = rec[rec['RECALL_TYPE_DESCRIPTION'].str.contains('FTR|Fixed', case=False)] # keep only fixed-term recalls
        pub_fixed = pd.concat([pub_fixed,rec],axis = 0, ignore_index= True) # concatenate 

# Check range of year-quarters to be sure you've covered relevant period
pub_fixed['Year_Quarter'] = pub_fixed['LICENCE_REVOKE_DATE'].dt.to_period('Q')
pub_fixed['Year'] = pub_fixed['LICENCE_REVOKE_DATE'].dt.to_period('Y')

pub_fixed['Year_Quarter'].value_counts(dropna=False).sort_index() # should start from 2013 Q4 to 2023 Q3.

# check missing nomis ids and dos
pub_fixed.shape[0] # 79022 rows
pub_fixed['NOMS_ID'].isna().sum()  # 192 missing NOMIS IDs
pub_fixed['DOS'].isna().sum()  # 2597 missing DOS

# count appearances of NOMIS and Date of sentence
group_counts = pub_fixed.groupby(['NOMS_ID', 'DOS']).size()
group_counts.value_counts(dropna=False).sort_index() # apperances of Nomis id-Dos combos
len(group_counts[group_counts > 1].index.get_level_values('NOMS_ID').unique()) # 9923


# *********************************** B USE FRESH EXTRACT

fixed1 = pd.read_excel("s3://alpha-omppg/Data Central/PPUD Recalls/Fixed Term Recalls up to 2016.xls")
fixed2 = pd.read_excel("s3://alpha-omppg/Data Central/PPUD Recalls/Fixed Term Recalls up to 2017 to Sep2023.xls")

fixed = pd.concat([fixed1,fixed2], axis =0, ignore_index= True) # concatenate

# keep data for relevant period
fixed2 = fixed[(fixed['LICENCE_REVOKE_DATE'].dt.normalize() > pd.Timestamp(2012,12,31)) & 
               (fixed['LICENCE_REVOKE_DATE'].dt.normalize() <= pd.Timestamp(2022,12,31))].copy()

# Check range of year-quarters to be sure you've covered relevant period
fixed2['Year_Quarter'] = fixed2['LICENCE_REVOKE_DATE'].dt.to_period('Q')
fixed2['Year'] = fixed2['LICENCE_REVOKE_DATE'].dt.to_period('Y')

fixed2['Year_Quarter'].value_counts(dropna=False).sort_index()

# check missing nomis ids and dos
fixed2.shape[0] # 78812 rows
fixed2['NOMS_ID'].isna().sum()  # 114 missing NOMIS IDs
fixed2['DOS'].isna().sum()  # 0 missing DOS

# count appearances of NOMIS and Date of sentence
group_counts = fixed2.groupby(['NOMS_ID', 'DOS']).size()
group_counts.value_counts(dropna=False).sort_index() # apperances of Nomis id-Dos combos
len(group_counts[group_counts > 1].index.get_level_values('NOMS_ID').unique()) # 9923


