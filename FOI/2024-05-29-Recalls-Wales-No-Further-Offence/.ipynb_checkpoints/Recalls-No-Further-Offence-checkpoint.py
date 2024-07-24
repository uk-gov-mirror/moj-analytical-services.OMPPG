""" 
2 The number of women recalled into custody for breach of post-release licence during 2023 ,
excluding those returned to custody for the commission of a further offence in Wales 
broken down into regional Probation Districts.

3 The number of women recalled into custody for breach of post-release  licence conditions,
excluding those returned to custody for the commission of a further offence,during 2023 for 
(a) England and (b) Wales and for England and Wales together.

By Eric Nyame, 29/05/2024
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


# ------------------ Import data

    # Interprets last 5 years as 2018 to 2022
# years = [2018, 2019, 2020, 2021, 2022] #2013,2014,2015,2016,2017, 
quarters =['q1','q2','q3','q4']

# loop through folders and try to import files with different file types but same name

recalls = pd.DataFrame()

for quarter in quarters:
    # import the file if it's a SAS file and name it pop_year
    try:
        quart_recs = pd.read_sas(f"s3://alpha-omppg/Recalls/final_data/recalls/recalls_final_2023{quarter}.sas7bdat", encoding='latin1')
        quart_recs.columns = quart_recs.columns.str.upper()
        print(f"Loaded SAS file for {quarter}")
    except Exception as e:
        print(f"Failed to load SAS file for {quarter}, error: {e}")
        # else if the file is not SAS, import it if it's a parquet file
        try:
            quart_recs = pd.read_parquet(f"s3://alpha-omppg/Recalls/final_data/recalls/recalls_final_2023{quarter}.parquet")
            quart_recs.columns = quart_recs.columns.str.upper()
            print(f"Loaded Parquet file for {quarter}")
        except Exception as e:
            print(f"Failed to load Excel file for {quarter}, error: {e}")
  
    recalls = pd.concat([recalls,quart_recs],axis=0)

    # upper case columns
len(recalls) # 27820

further_offence_mask_1 = recalls['RECALL_REASON_DESCRIPTIONS'].str.contains('Offence|further', case=False,na=False)
further_offence_mask_2 = (recalls['FURTHER_CHARGE'] == 100)

recalls[further_offence_mask_1]['RECALL_REASON_DESCRIPTIONS'].value_counts(dropna=False).reset_index()
recalls[further_offence_mask_1]['RECALL_REASON_DESCRIPTIONS'].size # 7510
recalls[further_offence_mask_2]['RECALL_REASON_DESCRIPTIONS'].size # 7510

noFurtherOffence = recalls[~further_offence_mask_1].copy()

len(noFurtherOffence) # 20310

someCols = ['NPS_DIVISION','NPS_CRC_NAME','PROBATION_AREA_DESCRIPTION','PROB_AREA','NOMS_REGION_DESCRIPTION']

for i in someCols:
    print('\n' + i)
    print(noFurtherOffence[i].value_counts(dropna=False))

walesMask = noFurtherOffence['NOMS_REGION_DESCRIPTION'].str.contains('wales',case=False,na=False)
walesNoOffence = noFurtherOffence[walesMask]

for i in someCols:
    print('\n' + i)
    print(walesNoOffence[i].value_counts(dropna=False))

walesMask = noFurtherOffence['NOMS_REGION_DESCRIPTION'].str.contains('wales',case=False,na=False)

noFurtherOffence['COUNTRY'] = 'England'
noFurtherOffence.loc[noFurtherOffence['NPS_DIVISION'].str.contains('wales',case=False,na=False),'COUNTRY'] = 'Wales'

noFurtherOffence['COUNTRY'].value_counts(dropna=False) # 1814,1496

femalesNoFurtherOffence = noFurtherOffence[noFurtherOffence['GENDER'] == 'F'].copy()
len(femalesNoFurtherOffence) #1688

# Wales probation areas
walesMask = femalesNoFurtherOffence['COUNTRY'] == 'Wales'

for i in someCols:
    print('\n' + i)
    print(femalesNoFurtherOffence[walesMask][i].value_counts(dropna=False))

# Country breakdown
femalesNoFurtherOffence['COUNTRY'].value_counts(dropna=False) # 1542,146




    # Check lengths match published population figures
for year in years:
    print(year,len(globals()[f'pop_{year}']))
    
# count IPPs
for year in years:
    x = globals()[f'pop_{year}']
    ipp_mask = x['DA_CUSTODY_TYPE_DESCRIPTION'].str.contains('IPP|DPP',case=False,na=False)
    count = len(x[ipp_mask])
    print(year,count)
    
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
