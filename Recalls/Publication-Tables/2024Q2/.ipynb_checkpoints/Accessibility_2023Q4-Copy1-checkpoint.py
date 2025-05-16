""" 
GOAL: PRODUCE RECALL TABLES FOR OMSQ.
By Eric Nyame, 17/04/2024
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

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>


        # Period variables
quarter = 4 # 1:Jan-Mar, 2:Apr-Jun, 3:Jul-Sep, 4:Oct-Dec
year = 2023 # Enter the year being run in 4 digit format

# Bring in final datasets
recalls = pd.read_parquet(f's3://alpha-omppg/Recalls/final_data/recalls/recalls_final_{year}q{quarter}.parquet')
reasons = pd.read_parquet(f's3://alpha-omppg/Recalls/Final Data/Parquet/recall_reasons_{year}q{quarter}.parquet')
ual = pd.read_parquet(f's3://alpha-omppg/UAL/Final Data/Parquet/ual_final_{year}q{quarter}.parquet')
releases = pd.read_sas(f's3://alpha-omppg/ISP Releases/Final Data/isp_releases_2023q4.sas7bdat', encoding='latin1')
# releases = pd.read_parquet(f's3://alpha-omppg/ISP Releases/Final Data/isp_releases_{year}q{quarter}.parquet') # for next quarter

releases.columns = releases.columns.str.upper()
releases = releases[releases['RELEASE_TYPE'] == 'Recall Re-release']
releases['MONTHS_RECALLED'] = releases.apply(lambda x: TimeDiffs.month_diff(x['LAST_RTC_DATE'],x['RELEASE_DATE']),axis=1)

# specify output table

output_work_book = f'Tables_{year}Q{quarter}.xlsx'

# ------------------------------------------ Table 5.2

recalls['Sent'] = np.nan

# Conditions for the 'Sent' column
conditions = [
    (recalls['CUSTODYTYPE'] == 'Determinate') & (recalls['SENTENCETYPE'].isna()),
    (recalls['CUSTODYTYPE'] == 'Determinate') & (recalls['SENTENCETYPE'] == 'Other'),
    (recalls['CUSTODYTYPE'] == 'Determinate') & (recalls['SENTENCETYPE'] == 'Under 12 months'),
    (recalls['CUSTODYTYPE'] == 'IPP') & (recalls['SENTENCETYPE'].isna()),
    (recalls['CUSTODYTYPE'] == 'IPP') & (recalls['SENTENCETYPE'] == 'Other'),
    (recalls['CUSTODYTYPE'] == 'IPP') & (recalls['SENTENCETYPE'] == 'Under 12 months'),
    (recalls['CUSTODYTYPE'] == 'Life') & (recalls['SENTENCETYPE'].isna()),
    (recalls['CUSTODYTYPE'] == 'Life') & (recalls['SENTENCETYPE'] == 'Other'),
    (recalls['CUSTODYTYPE'] == 'Life') & (recalls['SENTENCETYPE'] == 'Under 12 months')
]

# Corresponding values for each condition
choices = [
    'Missing',
    '12 months or more',
    'Less than 12 months',
    'Missing',
    'IPP',
    'IPP',
    'Missing',
    'Life sentence',
    'Life sentence'
]

# Apply the conditions and choices to 'Sent'
recalls['Sent'] = np.select(conditions, choices, default=recalls['Sent'])

# Condition for the 'HDC' column based on case-insensitive string finding
recalls['HDC'] = 'Non-HDC'
recalls.loc[recalls['RECALL_TYPE_DESCRIPTION'].str.contains('HDC', case=False),'HDC'] = 'HDC'


# Convert LICENCE_REVOKE_DATE to datetime and format as year-quarter
recalls['YYQ'] = recalls['LICENCE_REVOKE_DATE'].dt.to_period('Q')

# Creating the pivot table

with pd.ExcelWriter(output_work_book) as writer:  
    pd.pivot_table(
                        recalls,
                        index=['GENDER','SUP_BODY', 'Sent'],
                        columns=['YYQ', 'HDC'],
                        dropna=False,
                        aggfunc='size',  # Counting the number of occurrences
                        fill_value=0     # Replace NaN with 0
                    ).reset_index().to_excel(writer,sheet_name='Table 5_2')

# workbook closes by itself so no need use writer.close()


# ------------------------------------------ Table 5.3

# Creating the pivot table

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a') as writer:  
    pd.pivot_table(
    recalls,
    index=['SUP_BODY', 'NPS_CRC_NAME'],
    columns=['YYQ', 'HDC'],
    dropna=False,
    aggfunc='size',
    fill_value='0'
).reset_index().to_excel(writer,sheet_name='Table 5_3')

# ---------------Table 5.4: Number of returns to custody after licence recall, by sex, supervising body, and sentence length

table_4_condtion = ( (recalls['UAL_FLAG'] == False) |
                     (
                        (recalls['LICENCE_REVOKE_DATE'].dt.year < 2015) & 
                        (recalls['RTC_DATE'] <= recalls['RETURN_BY']) & 
                        (recalls['RTC_DATE'].notna())
                     )
                   )

# Creating the pivot table

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a') as writer:  
    pd.pivot_table(
    recalls[table_4_condtion],
    index=['GENDER','SUP_BODY', 'Sent'],
    columns=['YYQ'],
    dropna=False,
    aggfunc='size',
    fill_value='0'
).reset_index().to_excel(writer,sheet_name='Table 5_4')

# ---------------Table 5.5: Number of offenders not returned to custody after licence recall, by sex, supervising body, and sentence length

table_5_condtion = ( (recalls['UAL_FLAG'] == True) |
                     (
                        (recalls['LICENCE_REVOKE_DATE'].dt.year < 2015) & 
                        (
                            (recalls['RTC_DATE'] > recalls['RETURN_BY']) | 
                            (recalls['RTC_DATE'].isna())
                        )
                     )
                   )

# Creating the pivot table

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a') as writer:  
    pd.pivot_table(
    recalls[table_5_condtion],
    index=['GENDER','SUP_BODY', 'Sent'],
    columns=['YYQ'],
    dropna=False,
    aggfunc='size',
    fill_value='0'
).reset_index().to_excel(writer,sheet_name='Table 5_5')
    
# ---------------Table 5.6: Number of recalls from licence by sentence type, and process time

# correct recall process and recall target

recalls['RECALL_PROCESS'].value_counts(dropna=False)
recalls['RECALL_TARGET'].value_counts(dropna=False)

recalls.loc[recalls['CUSTODYTYPE'].isin(['IPP','Life']),'RECALL_PROCESS'] = 'Indeterminate sentences (1)'
recalls.loc[recalls['RECALL_TARGET'] == 'd. Resolved','RECALL_TARGET'] = 'b. Returned outside target'


# Creating the pivot table

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a') as writer:  
    pd.pivot_table(
    recalls,
    index=['RECALL_TARGET','RECALL_PROCESS'],
    columns=['YYQ'],
    dropna=False,
    aggfunc='size',
    fill_value='0'
).reset_index().to_excel(writer,sheet_name='Table 5_6')
    
# ---------------Table 5.7: Total number of offenders not returned to custody after licence recall, by sex, supervising body, and sentence length

ual['Sent'] = np.nan

# Applying multiple conditions to set the 'Sent' column
ual_conditions = [
    (ual['CUSTODYTYPE'] == 'Determinate') & (ual['SENTENCETYPE'].isna()),
    (ual['CUSTODYTYPE'] == 'Determinate') & (ual['SENTENCETYPE'] == 'Other'),
    (ual['CUSTODYTYPE'] == 'Determinate') & (ual['SENTENCETYPE'] == 'Under 12 months'),
    (ual['CUSTODYTYPE'] == 'IPP') & (ual['SENTENCETYPE'].isna()),
    (ual['CUSTODYTYPE'] == 'IPP') & (ual['SENTENCETYPE'] == 'Other'),
    (ual['CUSTODYTYPE'] == 'IPP') & (ual['SENTENCETYPE'] == 'Under 12 months'),
    (ual['CUSTODYTYPE'] == 'Life') & (ual['SENTENCETYPE'].isna()),
    (ual['CUSTODYTYPE'] == 'Life') & (ual['SENTENCETYPE'] == 'Other'),
    (ual['CUSTODYTYPE'] == 'Life') & (ual['SENTENCETYPE'] == 'Under 12 months')
]

choices = [
    'Missing',  # for determinate and missing sentence type
    '12 months or more',  # for determinate and 'Other'
    'Less than 12 months',  # for determinate and 'Under 12 months'
    'Missing',  # for IPP and missing sentence type
    'IPP',  # for IPP and 'Other'
    'IPP',  # for IPP and 'Under 12 months'
    'Missing',  # for Life and missing sentence type
    'Life sentence',  # for Life and 'Other'
    'Life sentence'  # for Life and 'Under 12 months'
]

# Apply the conditions and choices to 'Sent'
ual['Sent'] = np.select(ual_conditions, choices, default= np.nan)

ual.head()

# Couple of corrections
ual['SUP_BODY'].value_counts(dropna=False)

((ual['SUP_BODY'] == 'a. Probation Trust') & (ual['Sent'] == 'Less than 12 months')).sum() # 0

ual.loc[(ual['SUP_BODY'] == 'a. Probation Trust') & (ual['Sent'] == 'Less than 12 months'),'SUP_BODY'] = 'c. CRC'

ual.loc[ual['SUP_BODY'] == 'b. PS','SUP_BODY']= 'b. NPS'

# Creating the pivot table

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='replace') as writer:  
    ual.groupby(['GENDER','SUP_BODY', 'Sent'],dropna=False).size().reset_index(name='Count').to_excel(writer,sheet_name='Table 5_7')
    
# ---------------Table 5.8: Total number of offenders not returned to custody after licence recall, by supervising body, and length of time since recall


# Define the dictionary to map HOWLONG values
howlong_mapping = {
    "a Up to and including 6 months": "Up to and including 6 months",
    "b More than 6 months - 1 year": "From 6 months up to and including 12 months",
    "c More than 1 year - 2 years": "From 12 months up to and including 2 years",
    "d More than 2 years - 5 years": "From 2 years up to and including 5 years",
    "e More than 5 years - 10 years": "More than 5 years",
    "f More than 10 years": "More than 5 years",
    "other": "Unknown"
}

ual['HOWLONG'] = ual['HOWLONG'].map(howlong_mapping).fillna('Unknown')
ual['HOWLONG'].value_counts()

# Creating the pivot table

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a') as writer:  
    ual.groupby(['SUP_BODY', 'HOWLONG'],dropna=False).size().reset_index(name='Count'). \
    reset_index().to_excel(writer,sheet_name='Table 5_8')

# ---------------Table 5.9: Total number of offenders not returned to custody after licence recall, by offence

# Creating the pivot table
ual['OFFENCEGRP_NEW'].value_counts(dropna=False)
with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='replace') as writer:  
    ual.groupby(['OFFENCEGRP_NEW','OFFENCESUBGROUP_NEW'],dropna=False).size().reset_index(name='Count'). \
    reset_index().to_excel(writer,sheet_name='Table 5_9')

# ---------------Table 5.10: Number of recalls, by sex, sentence and reason for recall

# Some corrections
reasons['SENTENCETYPE'].value_counts()

reasons.loc[reasons['CUSTODYTYPE'] == 'IPP','SENTENCETYPE'] = 'IPP'
reasons.loc[reasons['CUSTODYTYPE'] == 'Life','SENTENCETYPE'] = 'Life'

# Creating the pivot table

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:  
    reasons.groupby(['SENTENCETYPE','REASON_DESC'],dropna=False).size().reset_index(name='Count'). \
    reset_index().to_excel(writer,sheet_name='Table 5_10')
    
    reasons.groupby(['GENDER','REASON_DESC'],dropna=False).size().reset_index(name='Count'). \
    reset_index().to_excel(writer,sheet_name='Table 5_10',startcol=6)

# ---------------Table 5.11: Number of recalls, by sex, sentence and reason for recall

# Some formatting
#releases['CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

releases.loc[releases['CUSTODY_TYPE_DESCRIPTION'] == 'DPP','CUSTODY_TYPE_DESCRIPTION'] = 'IPP'
releases.loc[releases['CUSTODY_TYPE_DESCRIPTION'] != 'IPP','CUSTODY_TYPE_DESCRIPTION'] = 'Life'
releases['YYQ'] = releases['RELEASE_DATE'].dt.to_period('Q')
cut_off = releases['RELEASE_DATE'].dt.year >= 2023

# Creating the pivot table

aggregated = releases[cut_off].groupby(['CUSTODY_TYPE_DESCRIPTION','YYQ'],dropna=False)['MONTHS_RECALLED'].agg(['size','mean','count']).reset_index()
df_melted = pd.melt(aggregated, id_vars=['CUSTODY_TYPE_DESCRIPTION', 'YYQ'], var_name='Statistic', value_name='Value')

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a') as writer:  
    df_melted.pivot_table(index=['CUSTODY_TYPE_DESCRIPTION', 'Statistic'], columns='YYQ', values='Value', fill_value=0).round().to_excel(writer,sheet_name='Table 5_11')
    
# ---------------Table 5.12: Number of recalls, by sex, sentence, supervising body and ethnicity 

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

# Creating the pivot table

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:  
    recalls.groupby(['GENDER','ETHNICITY'],dropna=False).size().reset_index(name = 'count').to_excel(writer,sheet_name='Table 5_12')
    recalls.groupby(['Sent','ETHNICITY'],dropna=False).size().reset_index(name = 'count').to_excel(writer,startcol=5,sheet_name='Table 5_12')
    recalls.groupby(['SUP_BODY','ETHNICITY'],dropna=False).size().reset_index(name = 'count').to_excel(writer,startcol=10,sheet_name='Table 5_12')