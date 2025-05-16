""" 
I am looking for some data on Fixed Term Recalls (as opposed to standard recalls) to custody across the last 5 years (2018-2023).

1.Total number of Fixed Term Recalls each year since 2018
2.The annual breakdown, by probation region, of Fixed Term Recalls to custody across the last 5 years
3.For the annual totals of FTRs across each of the last 5 years, the breakdown of top 3 reasons for recall? (i.e. 2020: X FTRs in total, Y% for reoffending, Z% for failure to reside, P% for failure to attend probation meeting.) 
4.I am looking for the % of all issued FTRs that were secondary FTRs on the same sentence. I.e. if 1000 were given in total, how many of these were given to the same person on the same sentence. (I would like this for every year from 2018) If it helps, for context, I am trying to understand the extent to which FTRs "work" - i.e. do individuals typically only require a single FTR to enforce engagement/compliance with their licence conditions.
5.By year, the proportion of total FTRs that were given during the licence period and the proportion that were given during PSS
6.The number of annual FTR recalls per the population in prison serving a sentence of 12 months or less on, say, 30 June, each year.
7.The 30th of June each year since 2018, what proportion of the total prison population was there on a Fixed Term Recall?

By Eric Nyame, 18/03/2024
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


# ------------------ Use publication and fresh extracts to determine number of fixed-term recalls each year


female_recalls = pd.read_excel('female_recalls_up_to_30Nov2024.xls')
female_recalls.shape # 96804.

female_recalls['RECALL_TYPE_DESCRIPTION'].value_counts(dropna=False)

  
# Create year variables in both datasets

# pub_fixed['YEAR'] = pub_fixed['LICENCE_REVOKE_DATE'].dt.to_period('Y')
female_recalls['YEAR'] = female_recalls['LICENCE_REVOKE_DATE'].dt.to_period('Y')

# Determine recall number for each combination of date of sentence and licence revocation date

female_recalls['DOS'].isna().sum() # 2 cases with missing date of sentece, good
female_recalls['LICENCE_REVOKE_DATE'].isna().sum() # 0
female_recalls['NOMS_ID'].isna().sum() # 2839
female_recalls['FILE_REFERENCE'].isna().sum() # 36
female_recalls['PRISON_NUMBER'].isna().sum() # 2

# check duplicates
female_recalls.duplicated(['PRISON_NUMBER','DOS','LICENCE_REVOKE_DATE'],keep='first').sum() # 8
female_recalls.duplicated(['PRISON_NUMBER','LICENCE_REVOKE_DATE'],keep='first').sum() # 13

    # remove duplicate prison number and licence revoke date
female_recalls = female_recalls.sort_values(['PRISON_NUMBER','LICENCE_REVOKE_DATE'])

female_recalls = female_recalls.drop_duplicates(['PRISON_NUMBER','LICENCE_REVOKE_DATE'])
female_recalls.shape

    # Count fixed-term recalls per year
# pub_fixed['YEAR'].value_counts(dropna=False).sort_index() # should start from 2013 Q4 to 2023 Q3.
female_recalls[female_recalls['LICENCE_REVOKE_DATE'].dt.year >= 2018]['YEAR'].value_counts(dropna=False).sort_index()


    # count the recall number for each combination of prison number, dos and licence revoke date

female_recalls = female_recalls.sort_values(['PRISON_NUMBER','DOS','LICENCE_REVOKE_DATE'])

female_recalls['RECALL_NUMBER'] = female_recalls.groupby(['PRISON_NUMBER','DOS']).cumcount() + 1

retain = ['FILE_REFERENCE','FAMILY_NAME','DOS','LICENCE_REVOKE_DATE','RECALL_NUMBER','RECALL_TYPE_DESCRIPTION']

female_recalls = female_recalls[retain +[col for col in female_recalls.columns if col not in retain]]

female_recalls.head(50)

# Keep only the second fixed-term recalls
second_ft_recalls = female_recalls[female_recalls['RECALL_NUMBER'] == 2].copy()

second_ft_recalls.shape # 14073

# tabulate to answer
    # number of second recall per year
    second_ft_recalls['YEAR'].value_counts(dropna=False).sort_index()
    
    # number of recalls per year
    female_recalls['YEAR'].value_counts(dropna=False).sort_index()

        #
female_recalls['YEAR'].value_counts(dropna=False).sort_index().to_excel("FOI_DATA.xlsx")

with pd.ExcelWriter("FOI_DATA.xlsx",engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:  
    # pub_fixed['YEAR'].value_counts(dropna=False).sort_index().to_excel(writer,sheet_name='Sheet1',startcol=3)
    second_ft_recalls['YEAR'].value_counts(dropna=False).sort_index().to_excel(writer,sheet_name='Sheet1',startcol=6)

# Breakdown by NOMS region
female_recalls.head()
female_recalls['NOMS_REGION_DESCRIPTION'].value_counts()
pd.pivot_table(
    female_recalls,
    index=['NOMS_REGION_DESCRIPTION'],
    columns=['YEAR'],
    dropna=False,
    aggfunc='size',
    fill_value='0'
).reset_index()


    # Split comma-separated reasons into a list, expand these into rows, and clean spaces
reasons =female_recalls.copy()
reasons['REASON_DESC'] = reasons['RECALL_REASON_DESCRIPTIONS'].str.split(',')
reasons.head()

reasons = reasons.explode('REASON_DESC')
reasons.head()

reasons['REASON_DESC'] = reasons['REASON_DESC'].str.strip()



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

#/Compress into one row for each recall/reason combination
reasons.shape # 160783
reasons = reasons.drop_duplicates()
reasons.shape # 160563

top3_each_year = reasons.groupby(['YEAR','REASON_DESC']).size().reset_index(name='Count').sort_values(['YEAR','Count'],ascending=[True,False]).groupby('YEAR').head(3)

top3_each_year.head()

top3_each_year = top3_each_year.sort_values(['YEAR','Count'],ascending=[True,False])

top3_each_year
