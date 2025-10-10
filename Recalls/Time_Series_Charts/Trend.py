""" 
GOAL: PRODUCE RECALL TRENDS FOR COMMENTARY IN OMSQ.
By Eric Nyame, 17/04/2024
"""

import pandas as pd
from pandas.api.types import CategoricalDtype
import numpy as np
import sys
import duckdb
import importlib

from itables import show
# openpyxl
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
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

# Get last final recall data for the last 5 quarters----------------------------------------------------------------------

rec1 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2024q4.parquet')
rec2 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2025q1.parquet')

# uppercase the headers
for df in [rec1,rec2]:
    df.columns = df.columns.str.upper()

# Concatenate all DataFrames into one------------------------------------------------------------------

recalls = pd.concat([rec1,rec2], ignore_index=True)
len(recalls) # 20376, 19757,17197
recalls.head()
recalls.info()

del rec1,rec2

# Add a recall 'QUARTER' column in the form 'Month to Month year'-------------------------------------------
# this uses a function in Shared.py

recalls['QUARTER'] = recalls['LICENCE_REVOKE_DATE'].dt.to_period('Q') # convert in the form 2022Q2
recalls['QUARTER'].unique()

# Change gender values - uses a mapping from Shared.py-----------------------------------------------------------

recalls['GENDER'].unique()

gender_mapping = {'F': 'Female', 'M': 'Male'}

recalls['GENDER'] = recalls['GENDER'].replace(gender_mapping) # change 'F' to 'Female', 'M' to 'Male'

# Create a SENTENCE column (under 12, over 12, IPP, life)--------------------------------------------------------
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

sentence_order = ['Life sentence','Determinate less than 12 months','IPP','Determinate 12 months or more']
recalls['SENTENCE'] = recalls['SENTENCE'].astype(CategoricalDtype(categories=sentence_order, ordered=True))
recalls['SENTENCE'].unique()

# Create a HDC indentification ------------------------------------------------------------------

recalls['HDC'] = 'Non-HDC'
recalls.loc[recalls['RECALL_TYPE_DESCRIPTION'].str.contains('HDC', case=False),'HDC'] = 'HDC'

# Fixed terms

recalls['FIXED'] = 'No'
recalls.loc[recalls['RECALL_TYPE_DESCRIPTION'].str.contains('fix|ftr', case=False),'FIXED'] = 'Yes'
recalls['FIXED'].value_counts(dropna=False)

# Custody types according to recall_type_description
recalls['RECALL_TYPE_CUSTODY'] = 'Determinates over 12m'
recalls.loc[recalls['RECALL_TYPE_DESCRIPTION'].str.contains('14|UNDER 12', case=False),'RECALL_TYPE_CUSTODY'] = 'ORA'
recalls.loc[recalls['RECALL_TYPE_DESCRIPTION'] == 'Indeterminate Recall','RECALL_TYPE_CUSTODY'] = 'ISP'

recalls['RECALL_TYPE_CUSTODY'].unique()

# ORA non-ORA by sentence type
recalls['ORA'] = 'Non-ORA'
recalls.loc[recalls['SENTENCE'] == 'Determinate less than 12 months','ORA'] = 'ORA'
recalls['ORA'].unique()

# Tabulate - Sentence Types

sentence_summary = recalls.groupby(['SENTENCE', recalls['LICENCE_REVOKE_DATE'].dt.to_period('Q')]).size().reset_index(name='Total')


show(sentence_summary.pivot_table(index ='SENTENCE',columns = 'LICENCE_REVOKE_DATE',values = 'Total').reset_index(),
     buttons=["excelHtml5"])

# Tabulate - ORA

recalls['ORA'] = recalls['ORA'].astype(CategoricalDtype(categories=['ORA','Non-ORA'], ordered=True))

ora_summary = recalls.groupby(['ORA', recalls['LICENCE_REVOKE_DATE'].dt.to_period('Q')]).size().reset_index(name='Total')

show(ora_summary.pivot_table(index ='ORA',columns = 'LICENCE_REVOKE_DATE',values = 'Total').reset_index(),
     buttons=["excelHtml5"])

# Tabulate - HDC

recalls['HDC'] = recalls['HDC'].astype(CategoricalDtype(categories=['Non-HDC','HDC'], ordered=True))

hdc_summary = recalls.groupby(['HDC', recalls['LICENCE_REVOKE_DATE'].dt.to_period('Q')]).size().reset_index(name='Total')

show(hdc_summary.pivot_table(index ='HDC',columns = 'LICENCE_REVOKE_DATE',values = 'Total').reset_index(),
     buttons=["excelHtml5"])

# Tabulate - Standard fixed including ISPs

std_1_summary = recalls.groupby(['FIXED', recalls['LICENCE_REVOKE_DATE'].dt.to_period('Q')]).size().reset_index(name='Total')

show(std_1_summary.pivot_table(index ='FIXED',columns = 'LICENCE_REVOKE_DATE',values = 'Total').reset_index(),
     buttons=["excelHtml5"])

# Tabulate - Standard fixed not including ISPs

std_2_summary = recalls[~recalls['SENTENCE'].isin(['Life sentence', 'IPP'])].groupby(['FIXED', recalls['LICENCE_REVOKE_DATE'].dt.to_period('Q')]).size().reset_index(name='Total')

show(std_2_summary.pivot_table(index ='FIXED',columns = 'LICENCE_REVOKE_DATE',values = 'Total').reset_index(),
     buttons=["excelHtml5"])