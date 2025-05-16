""" 
GOAL: PRODUCE QUARTERLY RECALL DATA FOR OMSQ.
By Eric Nyame, 15/04/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
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

# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x) #

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

recalls_final = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2024q4.parquet')

recalls_final['NUMBER_OF_RECALL_REASONS'].isna().sum() # 0

    # Check total number of recall reasons while ignoring NA values
recalls_final['NUMBER_OF_RECALL_REASONS'].sum() # 18840, 19051, 14626


# Expand dataset to include one row for every reason

    # Split comma-separated reasons into a list, expand these into rows, and clean spaces
reasons = recalls_final.copy()
reasons['REASON_DESC'] = reasons['RECALL_REASON_DESCRIPTIONS'].str.split(',')
reasons.head()

reasons = reasons.explode('REASON_DESC')
reasons.head()

reasons['REASON_DESC'] = reasons['REASON_DESC'].str.strip()


# Select and rearrange columns if necessary (not shown here as it mirrors the R code)
# e.g., expanded_reasons = expanded_reasons[['other_columns', 'REASON_DESC']] if needed

# Bring cases with no reason recorded
missing_reasons = recalls_final[recalls_final['NUMBER_OF_RECALL_REASONS'].isna()]

# Concatenate the 'expanded_reasons' and 'missing_reasons' datasets
reasons = pd.concat([reasons, missing_reasons], ignore_index=True)
reasons.shape # # 18840, 19051, 14626

# Count occurrences of each 'REASON_DESC', and sort
reason_counts = reasons['REASON_DESC'].value_counts(dropna=False).reset_index()
reason_counts.columns = ['REASON_DESC', 'n']
reason_counts = reason_counts.sort_values('n', ascending=False)
reason_counts

# Calculate percentages and cumulative frequencies
reason_counts['PERCENT'] = (reason_counts['n'] / reason_counts['n'].sum()) * 100
reason_counts['CUM_FREQ'] = reason_counts['n'].cumsum()
reason_counts['CUM_PERCENT'] = reason_counts['PERCENT'].cumsum()
reason_counts

# Round the percentages
reason_counts['PERCENT'] = reason_counts['PERCENT'].round(2)
reason_counts['CUM_PERCENT'] = reason_counts['CUM_PERCENT'].round(2)
reason_counts

# Group reasons together - any with less than 5% of dataset group into 'other'*/

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
    'Missing': 'Unknown'
}

# Apply the mapping to 'REASON_DESC'
reasons['REASON_DESC'] = reasons['REASON_DESC'].map(recallReason_format).fillna('Other')
reasons.head()


# Check grouping has worked (compare with totals above)*/
reasons['REASON_DESC'].value_counts(dropna=False).reset_index()

#/Compress into one row for each recall/reason combination

# duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")
query ="""SELECT DISTINCT * FROM reasons"""
reasons_final = duckdb.sql(query).df()
reasons_final.shape # 18781, 18977, 14579


# final table of reasons by quarter

# Extract year and quarter from 'LICENCE_REVOKE_DATE'
reasons_final['YYQ'] = reasons_final['LICENCE_REVOKE_DATE'].dt.to_period('Q').astype(str)

reasons_final.head()
reasons_final.info()

# Create a pivot table
pd.pivot_table(reasons_final, 
               index=['GENDER', 'REASON_DESC'], 
               columns=['YYQ'], aggfunc='size', fill_value=0)

pd.crosstab([reasons_final['GENDER'], reasons_final['REASON_DESC']],reasons_final['YYQ'])
# Print the pivot table

# Save on Amazon to continue

reasons_final = reasons_final.drop(columns=['YYQ'])

reasons_final.to_parquet("s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2024q4.parquet",index=False)
