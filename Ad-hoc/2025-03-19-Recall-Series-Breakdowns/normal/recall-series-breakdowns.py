""" 
As discussed – Dame Anne is interested in breakdowns of the recall flow into prisons by month (or week if possible), up to September 2024:
- By gender
- By standard/fixed term recall
- By sentence length (which I understand, due to data quality issues, is available only by an under/over 12-month breakdown)
- By IPP, life, and EDS
- By reason for recall


By Eric Nyame, 09/10/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib
from itables import show

# import re

# from dateutil.relativedelta import relativedelta

#---------------------------------- Import own predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
# import prepareMatch
# importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
import TimeDiffs

#----------------------------------Set display options

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.set_option('display.max_colwidth', None)

# function to remove trailing and leading blanks

def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>


# Function to identify where bad datetime value is. Pass in the 

def dateOutOfBoundsColumn(dataset,value): # pass in the out-of-bounds date
    for col in dataset.columns:
        # Convert the column to string and check if any value contains the problematic date substring
        if dataset[col].astype(str).str.contains(value).any():
            hmm = dataset[col].astype(str).str.contains(value)
            cols_to_keep = ['FILE_REFERENCE','FAMILY_NAME','LICENCE_REVOKE_DATE',col]
            display(dataset[hmm][cols_to_keep])
            break

dateOutOfBoundsColumn(recalls,'3017-03-30')

# Function to show table in my preferred way
def show_data(data):
    show(data,
         scrollY="200px", 
         scrollCollapse=True, 
         paging=False,
         buttons=["excelHtml5"])

#----------------------------------Set Global Parameters
years = list(range(2015,2025))
quarters =[f"q{i}" for i in range(1,5)]

#---------------------------------- Import data

# some of the files are SAS and others are Parquet, so try to import each

def conCatRecallDatasets(years,quarters):
    
    recalls = pd.DataFrame() # start with an empty dataframe

    for year in years:
        
        for quarter in quarters:

            quart_recs = pd.DataFrame() # Reset appending file

            try: # Try to import SAS file first
                quart_recs = pd.read_sas(f"s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_{year}{quarter}.sas7bdat", encoding='latin1')
                quart_recs.columns = quart_recs.columns.str.upper()
                print(f"Loaded SAS file for {year}{quarter}")

            except Exception as e:# If no SAS file, import parquet version

                print(f"Failed to load SAS file for {year}{quarter}, error: {e}")

                try:
                    quart_recs = pd.read_parquet(f"s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_{year}{quarter}.parquet")
                    quart_recs.columns = quart_recs.columns.str.upper()
                    print(f"Loaded Parquet file for {year}{quarter}")

                except Exception as e:
                    print(f"Failed to load parquet file for {year}{quarter}, error: {e}")

            recalls = pd.concat([recalls,quart_recs],axis=0)

    return recalls

recalls = conCatRecallDatasets(years,quarters)
len(recalls) # 240817

recalls['LICENCE_REVOKE_DATE'].dt.year.value_counts(dropna=False).sort_index()

# Year and month of licence revocation date
recalls['YEAR'] = recalls['LICENCE_REVOKE_DATE'].dt.year
recalls['MONTH_NUM'] = recalls['LICENCE_REVOKE_DATE'].dt.month # for sorting
recalls['MONTH'] = recalls['LICENCE_REVOKE_DATE'].dt.strftime('%b')

# Customize month abbreviations
custom_months = {'Jun':'June','Jul':'July','Sep': 'Sept'}
recalls['MONTH'] = recalls['MONTH'].replace(custom_months)

recalls.MONTH.value_counts()

recalls.head()
recalls.tail()

# Gender SUmmary

recalls['GENDER'].value_counts(dropna=False).sort_index()

summary_table = recalls.pivot_table(
    index = ['YEAR','MONTH_NUM','MONTH'],
    columns =[ 'GENDER'],
    aggfunc = 'size',
    fill_value = 0
).reset_index()

summary_table.columns.names = ['']
summary_table.head()

show_data(summary_table)

# Fixed-Standard term summary

recalls['RECALL_TYPE_DESCRIPTION'].value_counts(dropna=False)

ftrMask = recalls['RECALL_TYPE_DESCRIPTION'].str.contains('FTR|Fixed', case=False)

recalls['FIXED_OR_STANDARD'] = 'Standard'
recalls.loc[ftrMask,'FIXED_OR_STANDARD']='Fixed'

recalls['FIXED_OR_STANDARD'].value_counts(dropna=False).sort_index()

summary_table = recalls.pivot_table(
    index = ['YEAR','MONTH_NUM','MONTH'],
    columns =[ 'FIXED_OR_STANDARD'],
    aggfunc = 'size',
    fill_value = 0
).reset_index()

summary_table.columns.names = ['']
summary_table.head()

show_data(summary_table)

# Sentence

recalls['CUSTODYTYPE'].value_counts(dropna=False)
recalls['SENTENCETYPE'].value_counts(dropna=False)

def sentence(df):
    
    conditions = [
        (df['CUSTODYTYPE'] == 'Determinate') & (df['SENTENCETYPE'].isna()),
        (df['CUSTODYTYPE'] == 'Determinate') & (df['SENTENCETYPE'] == 'Other'),
        (df['CUSTODYTYPE'] == 'Determinate') & (df['SENTENCETYPE'] == 'Under 12 months'),
        (df['CUSTODYTYPE'] == 'IPP') & (df['SENTENCETYPE'].isna()),
        (df['CUSTODYTYPE'] == 'IPP') & (df['SENTENCETYPE'] == 'Other'),
        (df['CUSTODYTYPE'] == 'IPP') & (df['SENTENCETYPE'] == 'Under 12 months'),
        (df['CUSTODYTYPE'] == 'Life') & (df['SENTENCETYPE'].isna()),
        (df['CUSTODYTYPE'] == 'Life') & (df['SENTENCETYPE'] == 'Other'),
        (df['CUSTODYTYPE'] == 'Life') & (df['SENTENCETYPE'] == 'Under 12 months')
    ]

    choices = [
        'Missing',
        'Determinate 12 months or more',
        'Determinate less than 12 months',
        'Missing',
        'IPP',
        'IPP',
        'Missing',
        'Life sentence',
        'Life sentence'
    ]
    
    df['SENTENCE'] = np.nan # set initially to nans
    df['SENTENCE'] = np.select(conditions, choices, default=df['SENTENCE'])

sentence(recalls)
recalls['SENTENCE'].value_counts(dropna=False)

recalls['CUSTODY_TYPE_AT_RECALL'].value_counts(dropna=False)

summary_table = recalls.pivot_table(
    index = ['YEAR','MONTH_NUM','MONTH'],
    columns =[ 'SENTENCE'],
    aggfunc = 'size',
    fill_value = 0
).reset_index()

summary_table.columns.names = ['']
summary_table.head()

show_data(summary_table)

# Recall Reasons


