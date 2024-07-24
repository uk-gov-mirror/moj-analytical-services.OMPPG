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

recalls = pd.DataFrame() # start with an empty dataframe

for i in years:
    for j in quarters:
        if (i == 2013) and (j != 'q4'): # start from q4 2013 
            continue
        if (i == 2023) and (j =='q4'): # end at q3 2023
            break
        rec = pd.read_sas(f"s3://alpha-omppg/Recalls/Final Data/SAS/recalls_final_{i}{j}.sas7bdat", encoding='latin1')
        rec.columns = rec.columns.str.upper() # capitalise all headers
        ipp_condition = (rec['CUSTODYTYPE'] =='ipp') | (rec['CUSTODY_TYPE_DESCRIPTION'].str.contains('IPP|DPP', case=False, na = False))
        rec = rec[ipp_condition] # keep only fixed-term recalls
        recalls = pd.concat([recalls,rec],axis = 0, ignore_index= True) # concatenate 

# Check range of year-quarters to be sure you've covered relevant period
recalls['YEAR_QUARTER'] = recalls['LICENCE_REVOKE_DATE'].dt.to_period('Q')
recalls['YEAR'] = recalls['LICENCE_REVOKE_DATE'].dt.to_period('Y')

recalls['CUSTODYTYPE'].value_counts(dropna=False)
recalls['CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

recalls['GENDER'].value_counts(dropna=False)
recalls['ETHNICITY_DESCRIPTION'].value_counts(dropna=False)

recalls['DOB'].isna().sum() # 124

#------------------------ ETHNICITY
# Some formatting
# Define conditions
table_12_conditions = [
    recalls['ETHNICITY_DESCRIPTION'].str.contains('mixed', case=False, na=False),
    recalls['ETHNICITY_DESCRIPTION'].str.contains('black', case=False, na=False),
    recalls['ETHNICITY_DESCRIPTION'].str.contains('white', case=False, na=False),
    recalls['ETHNICITY_DESCRIPTION'].str.contains('Asian', case=False, na=False),
    recalls['ETHNICITY_DESCRIPTION'].str.contains('Refusal', case=False, na=False),
    recalls['ETHNICITY_DESCRIPTION'].str.contains('chinese', case=False, na=False),
    recalls['ETHNICITY_DESCRIPTION'].str.contains('Other Ethnic Group', case=False, na=False),
    recalls['ETHNICITY_DESCRIPTION'].str.contains('Other - Arab', case=False, na=False),
    recalls['ETHNICITY_DESCRIPTION'].str.contains('Other:', case=False, na=False),
    recalls['ETHNICITY_DESCRIPTION'].str.contains('Not Known', case=False, na=False),
    recalls['ETHNICITY_DESCRIPTION'].str.contains('Not Applicable', case=False, na=False),
    recalls['ETHNICITY_DESCRIPTION'].str.contains('Prefer not to say', case=False, na=False),
    recalls['ETHNICITY_DESCRIPTION'].str.contains('Any Other', case=False, na=False)
]

# Define outputs for each condition
choices = [
    'Mixed',
    'Black or Black British',
    'White',
    'Asian or Asian British',
    'Not stated',
    'Asian or Asian British',  # Now classified as Asian
    'Other ethnic group',
    'Other ethnic group',
    'Other ethnic group',
    'Unknown',
    'Unknown',
    'Not stated',
    'Other ethnic group'
]

# Apply conditions and choices to create the new column
recalls['ETHNICITY'] = np.select(table_12_conditions, choices, default='Check')
recalls['ETHNICITY'].value_counts(dropna=False)

# ----------------- AGE
recalls['AGE_AT_RECALL'] = np.where(recalls['LICENCE_REVOKE_DATE'] > recalls['DOB'],
                                         recalls.apply(lambda x: TimeDiffs.year_diff(x['DOB'],x['LICENCE_REVOKE_DATE']),axis=1),
                                        np.nan)

recalls['AGE_AT_RECALL'].value_counts(dropna=False)

# recalls.loc[recalls['AGE_AT_RECALL'].isna(),'AGEBAND'] = np.nan # not necessary as the last condition doesn't include missing cases
recalls.loc[recalls['AGE_AT_RECALL'] <= 20,'AGEBAND'] = '20 and under'
recalls.loc[(recalls['AGE_AT_RECALL'] > 20) & (recalls['AGE_AT_RECALL'] <= 39),'AGEBAND'] = '21-39'
recalls.loc[(recalls['AGE_AT_RECALL'] > 39) & (recalls['AGE_AT_RECALL'] <= 59),'AGEBAND'] = '40-59'
recalls.loc[recalls['AGE_AT_RECALL'] > 59 ,'AGEBAND'] = '60 or more' # formerly '60+'

recalls['AGEBAND'].value_counts(dropna=False)

#----------- TABULATE

# TOTAL RECALLS
recalls['YEAR'].value_counts(dropna=False).sort_index().reset_index()

# SEX

pd.pivot_table(
    recalls,
    index=['GENDER'],
    columns=['YEAR'],
    dropna=False,
    aggfunc='size',
    fill_value='0'
).reset_index()

# AGEBAND
pd.pivot_table(
    recalls,
    index=['AGEBAND'],
    columns=['YEAR'],
    dropna=False,
    aggfunc='size',
    fill_value='0'
).reset_index()

#ETHNICITY
pd.pivot_table(
    recalls,
    index=['ETHNICITY'],
    columns=['YEAR'],
    dropna=False,
    aggfunc='size',
    fill_value='0'
).reset_index()