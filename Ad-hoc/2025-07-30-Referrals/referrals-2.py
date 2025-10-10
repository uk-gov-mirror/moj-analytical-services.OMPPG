""" 
GOAL: Sentence bands for determinate cases referred to the Parole Board. 
By Eric Nyame, 02/05/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
import Out_of_bounds_dates # from my_log import my_log
import prepareMatch
#importlib.reload(prepareMatch)
import openMatch
# importlib.reload(openMatch)
import TimeDiffs
import tariff_groups

# Set display options

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

#----------------------------------Referral data

referrals = pd.read_excel("s3://alpha-omppg/data-central/PR_referrals/Active_Referred.xlsx")

strip_blanks(referrals)

referrals['REVIEW_TYPE_DESCRIPTION'].unique()
referrals['REVIEW_REASON_DESCRIPTION'].unique()

wantedTypes = ['Standard 255c recall review','zzzOngoing Review Following Recall']

referrals = referrals[referrals['REVIEW_TYPE_DESCRIPTION'].isin(wantedTypes)]

len(referrals) # 4614

referrals['REVIEW_RESULT_DESCRIPTION'].unique()

wantedOutcomes = ['Not Applicable','Not Specified']

referrals = referrals[referrals['REVIEW_RESULT_DESCRIPTION'].isin(wantedOutcomes)]

len(referrals) # 4468

sum(referrals['PART_TOTAL_IN_DAYS'].isna()) # 0

referrals = referrals[referrals['PART_TOTAL_IN_DAYS'] <= 1460]

len(referrals) # 2711

referrals['ACTUAL'].min() # 2023-10-23
referrals['ACTUAL'].max() # 2025-07-30

referrals['CUSTODY_TYPE_DESCRIPTION'].unique()

referrals = referrals[referrals['CUSTODY_TYPE_DESCRIPTION'] == 'Determinate']

len(referrals) # 2707

referrals.head()

referrals['ORA'] = (referrals['PART_TOTAL_IN_DAYS'] < 365)

"""
len(referrals) # 5043
sum(referrals['REVIEW_ID'].isna()) # 0
sum(referrals.duplicated('REVIEW_ID',keep=False)) # 6 duplicate Review IDs
referrals[referrals.duplicated(['REVIEW_ID'],keep=False)]
sum(referrals.duplicated(['REVIEW_ID','ACTUAL'],keep=False)) # 0
referrals[referrals.duplicated(['REVIEW_ID','ACTUAL'],keep=False)]

sum(referrals.duplicated('PRISON_NUMBER',keep=False)) # 2

referrals[referrals.duplicated('PRISON_NUMBER',keep=False)].head(5)

"""

referrals = referrals[~referrals.index.isin([5865])]

len(referrals) # 2706

referrals['SED'].min() # 2025-07-13
pd.Timestamp(2025,7,30)

sum(referrals['SED'].isna()) # 0

referrals = referrals[referrals['SED'] > pd.Timestamp(2025,7,30)]

len(referrals) # 2699

sum(referrals['ORA']) # 66

referrals['ORA'].value_counts()
# --------------keep a copy

referrals.to_excel('active_referrals.xlsx',index=False)
