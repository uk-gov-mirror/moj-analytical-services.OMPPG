""" 
As discussed – Dame Anne is interested in breakdowns of the recall flow into prisons by month (or week if possible), up to September 2024:

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

from pandas.api.types import CategoricalDtype
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

    # Problem columns with out-of-bounds dates to exclude
    
colsToDrop = ['DOS','DOB','RETURN_BY','RTC_DATE','REPORT_RECD_BY_UNIT_TARGET','PB_DECISION_AFTER_BREACH_ACTUAL']
            
def conCatRecallDatasets(years,quarters):
    
    recalls = pd.DataFrame() # start with an empty dataframe

    for year in years:
        
        for quarter in quarters:

            quart_recs = pd.DataFrame() # Reset appending file

            try: # Try to import SAS file first
                quart_recs = pd.read_sas(f"s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_{year}{quarter}.sas7bdat", encoding='latin1')
                quart_recs.columns = quart_recs.columns.str.upper()
                quart_recs = quart_recs.drop(columns=colsToDrop)
                print(f"Loaded SAS file for {year}{quarter}")

            except Exception as e:# If no SAS file, import parquet version

                print(f"Failed to load SAS file for {year}{quarter}, error: {e}")

                try:
                    quart_recs = pd.read_parquet(f"s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_{year}{quarter}.parquet")
                    quart_recs.columns = quart_recs.columns.str.upper()
                    quart_recs = quart_recs.drop(columns=colsToDrop)
                    print(f"Loaded Parquet file for {year}{quarter}")

                except Exception as e:
                    print(f"Failed to load parquet file for {year}{quarter}, error: {e}")

            recalls = pd.concat([recalls,quart_recs],axis=0)

    return recalls

recalls = conCatRecallDatasets(years,quarters)

len(recalls) # 240817

show_data(recalls['REASON_DESC'].value_counts(dropna=False).sort_index())

recalls['REASON_DESC'].unique()

# Define the mapping dictionary
recallReason_format = {
    'Poor Behaviour - non-compliance': 'Non-compliance',
    'Poor Behaviour - Further offence/charge': 'Facing further charge',
    'Further Charge': 'Facing further charge',
    'EM - Further offence/charge - detected by ELM': 'Facing further charge',
    'HDC Further Charge': 'Facing further charge',
    'Failed to keep in touch': 'Failed to keep in touch',
    'Out Of Touch': 'Failed to keep in touch',
    'Failed to reside': 'Failed to reside',
    'Fail To Reside': 'Failed to reside',
    'Poor Behaviour - Drugs': 'Drugs/alcohol',
    'Poor Behaviour - alcohol': 'Drugs/alcohol',
    'HDC - Time violation': 'HDC - Time violation',
    'Poor Behaviour - Relationships': 'Poor Behaviour - Relationships',
    'HDC - Inability to monitor': 'HDC - Inability to monitor',
    'Failed home visit': 'Failed home visit',
    'HDC - Failed installation': 'HDC - Failed installation',
    'HDC - Equipment Tamper': 'HDC - Equipment Tamper',
    'a. Further Charge[*]' : 'Facing further charge',
    'a. HDC - Time violation' : 'HDC - Time violation',
    'b. HDC - Inability to monitor' : 'HDC - Inability to monitor',
    'b. Poor Behaviour - non-compliance[*]' : 'Non-compliance',
    'c. Failed to keep in touch[*]' : 'Failed to keep in touch',
    'c. HDC - Failed installation' : 'HDC - Failed installation',
    'd. Failed to reside[*]' : 'Failed to reside',
    'd. HDC - Equipment Tamper' : 'HDC - Equipment Tamper',
    'e. Poor Behaviour - Drugs/alcohol[*]' : 'Drugs/alcohol',
    'f. Other[*]' : 'Other',
    'f. Poor Behaviour - Relationships' : 'Poor Behaviour - Relationships',
    'g. Other[*]' : 'Other',
    'g. Unknown[*]' : 'Unknown',
    'h. Unknown[*]' : 'Unknown',
    'Missing': 'Unknown'
}

# Apply the mapping to 'REASON_DESC'
recalls['REASON_DESC_2'] = recalls['REASON_DESC'].replace(recallReason_format)
recalls.head()
recalls['REASON_DESC_2'].value_counts(dropna=False).sort_index()

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

# Reason SUmmary

    # Order the values of recall reason
reason_desc_vals = ['Facing further charge',
                    'Non-compliance', 
                    'Failed to keep in touch',
                    'Failed to reside', 
                    'Drugs/alcohol',
                    'Poor Behaviour - Relationships',
                    'HDC - Time violation', 
                    'HDC - Inability to monitor', 
                    'Failed home visit',
                    'HDC - Failed installation', 
                    'HDC - Equipment Tamper',
                    'Other']

recalls['REASON_DESC_2'] = recalls['REASON_DESC_2'].astype(CategoricalDtype(categories=reason_desc_vals, ordered=True))

summary_table = recalls.pivot_table(
    index = ['YEAR','MONTH_NUM','MONTH'],
    columns =[ 'REASON_DESC_2'],
    aggfunc = 'size',
    observed=True,
    fill_value = 0
).reset_index()

summary_table.columns.names = ['']
summary_table.head(20)

show_data(summary_table)