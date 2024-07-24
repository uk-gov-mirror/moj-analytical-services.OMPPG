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

sys.path.append('/home/jovyan/OMPPG/Macro Library')
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

    # Interprets last 5 years as 2018 to 2022
years = [2018, 2019, 2020, 2021, 2022] #2013,2014,2015,2016,2017, 
quarters =['q1','q2','q3','q4']

    # concatenate publication datasets and keep only fixed-term recalls

pub_fixed = pd.DataFrame() # start with an empty dataframe

for i in years:
    for j in quarters:
        if (i == 2013) and (j != 'q4'): # start from q4 2013 
            continue
        if (i == 2023) and (j =='q4'): # end at q3 2023
            break
        rec = pd.read_sas(f"s3://alpha-omppg/Recalls/Final Data/SAS/recalls_final_{i}{j}.sas7bdat", encoding='latin1')
        rec.columns = rec.columns.str.upper() # capitalise all headers
        rec = rec[rec['RECALL_TYPE_DESCRIPTION'].str.contains('FTR|Fixed', case=False)] # keep only fixed-term recalls
        pub_fixed = pd.concat([pub_fixed,rec],axis = 0, ignore_index= True) # concatenate 

       # import fresh fixed-term recall extracts from PPUD
    
rec_file_names = ['Recalls_up_to_2009.xls','Recalls_2012_2013.xls','Recalls_2014_2016.xls','Recalls_2017_2018.xls','Recalls_2019_2020.xls','Recalls_2021_2022.xls','Recalls_2023.xls'] # file names on amazon

extract_fixed = pd.DataFrame() # start with an empty dataframe to capture all PPUD fixed term recalls up to Sep 2023

for _,filename in enumerate(rec_file_names):
    rec = pd.read_excel(f"s3://alpha-omppg/Data Central/PPUD Recalls/{filename}")
    rec = rec[rec['RECALL_TYPE_DESCRIPTION'].str.contains('FTR|Fixed', case=False)] # keep only fixed-term recalls
    extract_fixed = pd.concat([extract_fixed,rec],axis = 0, ignore_index= True) # concatenate

extract_fixed_2 = extract_fixed.copy()
extract_fixed_2.shape # 96804.

extract_fixed_2['RECALL_TYPE_DESCRIPTION'].value_counts(dropna=False)

  
# Create year variables in both datasets

# pub_fixed['YEAR'] = pub_fixed['LICENCE_REVOKE_DATE'].dt.to_period('Y')
extract_fixed_2['YEAR'] = extract_fixed_2['LICENCE_REVOKE_DATE'].dt.to_period('Y')

# Determine recall number for each combination of date of sentence and licence revocation date

extract_fixed_2['DOS'].isna().sum() # 2 cases with missing date of sentece, good
extract_fixed_2['LICENCE_REVOKE_DATE'].isna().sum() # 0
extract_fixed_2['NOMS_ID'].isna().sum() # 2839
extract_fixed_2['FILE_REFERENCE'].isna().sum() # 36
extract_fixed_2['PRISON_NUMBER'].isna().sum() # 2

# check duplicates
extract_fixed_2.duplicated(['PRISON_NUMBER','DOS','LICENCE_REVOKE_DATE'],keep='first').sum() # 8
extract_fixed_2.duplicated(['PRISON_NUMBER','LICENCE_REVOKE_DATE'],keep='first').sum() # 13

    # remove duplicate prison number and licence revoke date
extract_fixed_2 = extract_fixed_2.sort_values(['PRISON_NUMBER','LICENCE_REVOKE_DATE'])

extract_fixed_2 = extract_fixed_2.drop_duplicates(['PRISON_NUMBER','LICENCE_REVOKE_DATE'])
extract_fixed_2.shape

    # Count fixed-term recalls per year
# pub_fixed['YEAR'].value_counts(dropna=False).sort_index() # should start from 2013 Q4 to 2023 Q3.
extract_fixed_2[extract_fixed_2['LICENCE_REVOKE_DATE'].dt.year >= 2018]['YEAR'].value_counts(dropna=False).sort_index()


    # count the recall number for each combination of prison number, dos and licence revoke date

extract_fixed_2 = extract_fixed_2.sort_values(['PRISON_NUMBER','DOS','LICENCE_REVOKE_DATE'])

extract_fixed_2['RECALL_NUMBER'] = extract_fixed_2.groupby(['PRISON_NUMBER','DOS']).cumcount() + 1

retain = ['FILE_REFERENCE','FAMILY_NAME','DOS','LICENCE_REVOKE_DATE','RECALL_NUMBER','RECALL_TYPE_DESCRIPTION']

extract_fixed_2 = extract_fixed_2[retain +[col for col in extract_fixed_2.columns if col not in retain]]

extract_fixed_2.head(50)

# Keep only the second fixed-term recalls
second_ft_recalls = extract_fixed_2[extract_fixed_2['RECALL_NUMBER'] == 2].copy()

second_ft_recalls.shape # 14073

# tabulate to answer
    # number of second recall per year
    second_ft_recalls['YEAR'].value_counts(dropna=False).sort_index()
    
    # number of recalls per year
    extract_fixed_2['YEAR'].value_counts(dropna=False).sort_index()

        #
extract_fixed_2['YEAR'].value_counts(dropna=False).sort_index().to_excel("FOI_DATA.xlsx")

with pd.ExcelWriter("FOI_DATA.xlsx",engine='openpyxl', mode='a',if_sheet_exists='overlay') as writer:  
    # pub_fixed['YEAR'].value_counts(dropna=False).sort_index().to_excel(writer,sheet_name='Sheet1',startcol=3)
    second_ft_recalls['YEAR'].value_counts(dropna=False).sort_index().to_excel(writer,sheet_name='Sheet1',startcol=6)

# Breakdown by NOMS region
extract_fixed_2.head()
extract_fixed_2['NOMS_REGION_DESCRIPTION'].value_counts()
pd.pivot_table(
    extract_fixed_2,
    index=['NOMS_REGION_DESCRIPTION'],
    columns=['YEAR'],
    dropna=False,
    aggfunc='size',
    fill_value='0'
).reset_index()


    # Split comma-separated reasons into a list, expand these into rows, and clean spaces
reasons =extract_fixed_2.copy()
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
