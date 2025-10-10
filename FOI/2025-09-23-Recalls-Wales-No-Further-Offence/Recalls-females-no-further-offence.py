""" 
1. Can you please provide me with the number of women in Wales recalled to custody (not involving a further offence) in 2023. 
 
2. In relation to (1) can you please tell me how many recalls relate to an original (custodial) sentence of: (a) over 12 months (b) 12 months or less. 
 
3. Can you please provide me with the number of women in England recalled to custody (not involving a further offence) in 2023. 
 
4. In relation to (3) can you please tell me how many recalls relate to an original (custodial) sentence of: (a) over 12 months (b) 12 months or less.’

"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib
import os

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
#importlib.reload(Out_of_bounds_dates)
#import prepareMatch
#importlib.reload(prepareMatch)
#import openMatch
#importlib.reload(openMatch)
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


# ------------------ Import data
rec1 = pd.read_sas('s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2023q1.sas7bdat',encoding='latin1')
rec2 = pd.read_sas('s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2023q2.sas7bdat',encoding='latin1')
rec3 = pd.read_sas('s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2023q3.sas7bdat',encoding='latin1')
rec4 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2023q4.parquet')

for data in [rec1,rec2,rec3,rec4]:
    data.columns = data.columns.str.upper()

recalls = pd.concat([rec1,rec2,rec3,rec4], ignore_index=True)

"""
len(recalls) # 27820
recalls.info()
recalls.head()

del rec1,rec2,rec3,rec4
"""

further_offence_mask_1 = recalls['RECALL_REASON_DESCRIPTIONS'].str.contains('Offence|further', case=False,na=False)
further_offence_mask_2 = (recalls['FURTHER_CHARGE'] == 100)

"""
recalls[further_offence_mask_1]['RECALL_REASON_DESCRIPTIONS'].value_counts(dropna=False).reset_index()
recalls[further_offence_mask_1]['RECALL_REASON_DESCRIPTIONS'].size # 7510
recalls[further_offence_mask_2]['RECALL_REASON_DESCRIPTIONS'].size # 7510
"""

noFurtherOffence = recalls[~further_offence_mask_1].copy()

"""
len(noFurtherOffence) # 20310

someCols = ['NOMS_REGION_DESCRIPTION','NPS_DIVISION','NPS_CRC_NAME','PROBATION_AREA_DESCRIPTION','PROB_AREA']

for i in someCols:
    print('\n' + i)
    print(noFurtherOffence[i].value_counts(dropna=False))

recalls.pivot_table(index=someCols,aggfunc='size').reset_index()

walesMask = noFurtherOffence['NOMS_REGION_DESCRIPTION'].str.contains('wales',case=False,na=False) # NOMS region is wrong
walesNoOffence = noFurtherOffence[walesMask]

for i in someCols:
    print('\n' + i)
    print(walesNoOffence[i].value_counts(dropna=False))
"""
noFurtherOffence['COUNTRY'] = 'England'
noFurtherOffence.loc[noFurtherOffence['NPS_DIVISION'] == 'Wales','COUNTRY'] = 'Wales'

noFurtherOffence['COUNTRY'].value_counts(dropna=False) # 

noFurtherOffence['CUSTODYTYPE'].value_counts(dropna=False) #

# Keep only females

noFurtherOffence['GENDER'].value_counts(dropna=False) # females = 2461
femalesNoFurtherOffence = noFurtherOffence[noFurtherOffence['GENDER'] == 'F'].copy()
len(femalesNoFurtherOffence) # 1688

# ORA and non-ORA
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
    
sentence(femalesNoFurtherOffence)

femalesNoFurtherOffence['SENTENCE'].unique()
femalesNoFurtherOffence['SENTENCE'].value_counts(dropna=False) #
# Custody types according to recall_type_description
femalesNoFurtherOffence['RECALL_TYPE_CUSTODY'] = 'Determinates over 12m'
femalesNoFurtherOffence.loc[femalesNoFurtherOffence['RECALL_TYPE_DESCRIPTION'].str.contains('14|UNDER 12', case=False),'RECALL_TYPE_CUSTODY'] = 'ORA'
femalesNoFurtherOffence.loc[femalesNoFurtherOffence['RECALL_TYPE_DESCRIPTION'] == 'Indeterminate Recall','RECALL_TYPE_CUSTODY'] = 'ISP'

femalesNoFurtherOffence['RECALL_TYPE_CUSTODY'].unique()
femalesNoFurtherOffence['RECALL_TYPE_CUSTODY'].value_counts(dropna=False)

# ORA non-ORA by sentence type
femalesNoFurtherOffence['ORA'] = 'Non-ORA'
femalesNoFurtherOffence.loc[femalesNoFurtherOffence['SENTENCE'] == 'Determinate less than 12 months','ORA'] = 'ORA'
femalesNoFurtherOffence['ORA'].unique()

femalesNoFurtherOffence['ORA'].value_counts(dropna=False)

# Wales probation areas
walesMask = femalesNoFurtherOffence['COUNTRY'] == 'Wales'

for i in someCols:
    print('\n' + i)
    print(femalesNoFurtherOffence[walesMask][i].value_counts(dropna=False))

# Country breakdown
femalesNoFurtherOffence['COUNTRY'].value_counts(dropna=False) # 1542,146

pd.pivot_table(femalesNoFurtherOffence,index = 'COUNTRY',columns = 'ORA',aggfunc='size').reset_index()
