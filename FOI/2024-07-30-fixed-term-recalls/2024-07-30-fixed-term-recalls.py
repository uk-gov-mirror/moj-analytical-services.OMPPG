""" 
I would like to know:
• How many Fixed Term Recalls to custody there were in Q1 2024
• For the total number of FTRs in 2023, the breakdown of top 3 reasons for recall? (i.e. 2023: X FTRs in total, Y% for reoffending, Z% for failure to reside, P% for failure to attend probation meeting.) 
• In 2023 the breakdown, by probation region, of Fixed Term Recalls to custody


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

# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x) #


# (1) How many Fixed Term Recalls to custody there were in Q1 2024

ft_recalls_2024q1 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/Parquet/recalls_final_2024q1.parquet')

ft_recalls_2024q1.columns = ft_recalls_2024q1.columns.str.upper()

ft_recalls_2024q1['QUARTER'] = ft_recalls_2024q1['LICENCE_REVOKE_DATE'].dt.to_period('Q') # convert in the form 2022Q2

# Fixed terms

ft_recalls_2024q1['FIXED'] = 'No'
ft_recalls_2024q1.loc[ft_recalls_2024q1['RECALL_TYPE_DESCRIPTION'].str.contains('fix|ftr', case=False),'FIXED'] = 'Yes'
ft_recalls_2024q1['FIXED'].value_counts(dropna=False)

pd.pivot_table(ft_recalls_2024q1,
               index = 'RECALL_TYPE_DESCRIPTION',
               columns = 'FIXED',
               values = 'LICENCE_REVOKE_DATE',
               aggfunc='count',
               fill_value=0)

ft_recalls_2024q1['FIXED'].value_counts(dropna=False)
# 2208

# (2) For the total number of FTRs in 2023, the breakdown of top 3 reasons for recall? (i.e. 2023: X FTRs in total, Y% for reoffending, Z% for failure to reside, P% for failure to attend probation meeting.) 


# RecallReasons-------------------------------------------

reas1 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2023q1.parquet')
reas2 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2023q2.parquet')
reas3 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2023q3.parquet')
reas4 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_2023q4.parquet')

# uppercase the headers
for df in [reas1,reas2,reas3,reas4]:
    df.columns = df.columns.str.upper()

# Concatenate all DataFrames into one------------------------------------------------------------------

ft_reasons = pd.concat([reas1,reas2,reas3,reas4], ignore_index=True)

ft_reasons['FIXED'] = 'No'
ft_reasons.loc[ft_reasons['RECALL_TYPE_DESCRIPTION'].str.contains('fix|ftr', case=False),'FIXED'] = 'Yes'
ft_reasons = ft_reasons[ft_reasons['FIXED']=='Yes']

ft_reasons['FIXED'].value_counts(dropna=False)

len(ft_reasons) # 13205

ft_reasons.head()
ft_reasons.info()

ft_reasons['REASON_DESC'].value_counts(dropna=False).reset_index()

# (3) In 2023 the breakdown, by probation region, of Fixed Term Recalls to custody

rec1 = pd.read_sas('s3://alpha-omppg/Recalls/final_data/recalls/recalls_final_2023q1.sas7bdat',encoding='latin1')
rec2 = pd.read_sas('s3://alpha-omppg/Recalls/final_data/recalls/recalls_final_2023q2.sas7bdat',encoding='latin1')
rec3 = pd.read_sas('s3://alpha-omppg/Recalls/final_data/recalls/recalls_final_2023q3.sas7bdat',encoding='latin1')
rec4 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/Parquet/recalls_final_2023q4.parquet')

# uppercase the headers
for df in [rec1,rec2,rec3,rec4]:
    df.columns = df.columns.str.upper()

ft_recalls_2023 = pd.concat([rec1,rec2,rec3,rec4], ignore_index=True)

ft_recalls_2023['FIXED'] = 'No'
ft_recalls_2023.loc[ft_recalls_2023['RECALL_TYPE_DESCRIPTION'].str.contains('fix|ftr', case=False),'FIXED'] = 'Yes'
ft_recalls_2023 = ft_recalls_2023[ft_recalls_2023['FIXED']=='Yes']

len(ft_recalls_2023) # 6668

ft_recalls_2023['NPS_CRC_NAME'].value_counts(dropna=False).reset_index()

recalls_2023q1 = pd.read_sas('s3://alpha-omppg/Recalls/final_data/recalls/recalls_final_2023q1.sas7bdat',encoding='latin1')

recalls_2023q1.columns = recalls_2023q1.columns.str.upper()

recalls_2023q1.index = recalls_2023q1['LICENCE_REVOKE_DATE']

monthly_sum = recalls_2023q1.resample('M').size()
monthly_sum

recalls_2023q1.index = pd.
recalls_2023q1.head()


