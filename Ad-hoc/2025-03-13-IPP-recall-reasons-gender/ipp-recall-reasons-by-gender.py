""" 
GOAL: BREAD DOWN RECALL IPP RECALL REASONS BY SEX
"""

import pandas as pd
from pandas.api.types import CategoricalDtype
import numpy as np
from itables import show

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Get last final recall data for the last 5 quarters----------------------------------------------------------------------

reas4 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2023q3.parquet')
reas5 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2023q4.parquet')
reas1 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2024q1.parquet')
reas2 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2024q2.parquet')
reas3 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2024q3.parquet')

# uppercase the headers
for df in [reas1,reas2,reas3,reas4,reas5]:
    df.columns = df.columns.str.upper()

# Concatenate all DataFrames into one------------------------------------------------------------------

reasons = pd.concat([reas4,reas5,reas1,reas2,reas3], ignore_index=True)
len(reasons) # 80,236,74661,68905
reasons.head()
reasons.info()

del reas1,reas2,reas3,reas4,reas5

# Some corrections
reasons['SENTENCETYPE'].value_counts()
reasons['CUSTODYTYPE'].value_counts()

reasons.loc[reasons['CUSTODYTYPE'] == 'IPP','SENTENCETYPE'] = 'IPP'
reasons.loc[reasons['CUSTODYTYPE'] == 'Life','SENTENCETYPE'] = 'Life sentence'
reasons.loc[reasons['SENTENCETYPE'] == 'Other','SENTENCETYPE'] = 'Determinate 12 months or more'
reasons.loc[reasons['SENTENCETYPE'] == 'Under 12 months','SENTENCETYPE'] = 'Determinate less than 12 months'

reasons['SENTENCE'] = reasons['SENTENCETYPE']

# Add a recall 'QUARTER' column in the form 'Month to Month year'-------------------------------------------
# this uses a function in Shared.py

quarter_mapping = {
    'Q1': 'Jan to Mar',
    'Q2': 'Apr to June',
    'Q3': 'July to Sept',
    'Q4': 'Oct to Dec'
}
def format_quarter(period):
    year = period.year
    quarter_str = str(period).split('Q')[1] # splits at Q and takes the number at the end
    return f"{quarter_mapping[f'Q{quarter_str}']} {year}"

reasons['QUARTER'] = reasons['LICENCE_REVOKE_DATE'].dt.to_period('Q') # convert in the form 2022Q2
reasons['QUARTER'] = reasons['QUARTER'].apply(format_quarter) # then apply the function to it to change to 'Month to Month year'
reasons['QUARTER'].unique()
reasons.head() # have a look

# Change gender values - uses a mapping from Shared.py-----------------------------------------------------------
gender_mapping = {'F': 'Female', 'M': 'Male'}
reasons['GENDER'].unique()
reasons['GENDER'] = reasons['GENDER'].replace(gender_mapping) # change 'F' to 'Female', 'M' to 'Male'

# reasons[reasons['REASON_DESC'] == 'Other']['RECALL_REASON_DESCRIPTIONS'].value_counts(dropna=False)

# create a list of the unique recall['QUARTER'] values ---------------

quarters = list(reasons['QUARTER'].unique()) # values like 'Month to Month Year'
quarters

# Calculate summaries for table 2 - function table_2_func() is in Shared.py

# Pivot the final summary DataFrame to get the desired format

ipp_recalls = reasons[reasons['SENTENCE']=='IPP']
ipp_recalls['SENTENCE'].value_counts(dropna=False)

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

ipp_recalls['REASON_DESC'] = ipp_recalls['REASON_DESC'].astype(CategoricalDtype(categories=reason_desc_vals, ordered=True))

table_10_df = ipp_recalls.pivot_table(
    index=['GENDER', 'REASON_DESC'],
    columns='QUARTER',
    aggfunc='size',observed=False
).reset_index()

show( table_10_df, buttons=["excelHtml5"])
