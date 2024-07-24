""" 
GOAL: PRODUCE ADMISSION AND RECALL STATISTICS FOR RESTRICTED PATIENT PUBLICATION
By Eric Nyame, 29/02/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
# import duckdb
# import importlib

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
# from my_log import my_log
import Out_of_bounds_dates
# importlib.reload(Out_of_bounds_dates)
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


#----------------------------------Set globals

year = 2023
# snapshotDate = pd.Timestamp(2023,12,31)

#--------------- Import the population dataset and replace long dash with normal dash

admis_and_recs = pd.read_excel(f"s3://alpha-omppg/Mental Health/{year}/Raw Data/Admissions_and_Recalls_{year}.xls")

admis_and_recs = admis_and_recs.replace("–","-", regex = True)

    # check datetime types
admis_and_recs.info() # all good

admis_and_recs.head()

    # rearrange columns
# admis_and_recs.columns

retain_order = ['FILE_REFERENCE', 'FAMILY_NAME', 'ACTUAL_DATE',  'MOVE_TYPE_DESCRIPTION','MOVE_SUB_TYPE_DESCRIPTION',
                'MOVE_SUB_SUB_TYPE_DESCRIPTION','FROM_ESTABLISHMENT_DESCRIPTION','TO_ESTABLISHMENT_DESCRIPTION']

admis_and_recs = admis_and_recs[retain_order + [col for col in admis_and_recs.columns if col not in retain_order]]

admis_and_recs.head()

#---------------Remove duplicates

admis_and_recs[admis_and_recs.duplicated(subset=['FILE_REFERENCE','ACTUAL_DATE'],keep = False)].sort_values(['FILE_REFERENCE','ACTUAL_DATE']).head(10)

admis_and_recs = admis_and_recs.drop(index=[931,124])

len(admis_and_recs) # 1748

#---------------Remove Test cases
    # Check 'test' cases and remove
admis_and_recs[admis_and_recs['FAMILY_NAME'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

admis_and_recs[admis_and_recs['FIRST_NAMES'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

Test_Case_Mask =  (   (admis_and_recs['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (admis_and_recs['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (admis_and_recs['FILE_REFERENCE'] != 'T18122')

admis_and_recs = admis_and_recs[~Test_Case_Mask]

len(admis_and_recs) # 1747

    # Check 'case' cases and remove
admis_and_recs[admis_and_recs['FAMILY_NAME'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

admis_and_recs[admis_and_recs['FIRST_NAMES'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

    # Check 'digit' cases - these are normally good and shoulbe untouched
admis_and_recs[admis_and_recs['FAMILY_NAME'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none

admis_and_recs[admis_and_recs['FIRST_NAMES'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none

#--------------- Bring in DetAuth reference file
detAuth = pd.read_excel("s3://alpha-omppg/Mental Health/Reference/Reference.xls", sheet_name = "DetAuth")

detAuth = detAuth.replace("–","-", regex = True)

detAuth_dict = dict(zip(detAuth['AUTHORITY_FOR_DETENTION_DESCRIPT'],detAuth['DETAUTH_PUB'])) # creates a dictionary of DAs and their pub values

admis_and_recs['ADMISSION_CATEGORY'] =admis_and_recs['AUTHORITY_FOR_DETENTION_DESCRIPTION'].map(detAuth_dict).fillna('check') # Create Admissions Cat column matching reference

admis_and_recs.groupby(['AUTHORITY_FOR_DETENTION_DESCRIPTION','ADMISSION_CATEGORY']).size().reset_index(name='count') # check any non-matches

    # Remove non applicables and not specifieds
admis_and_recs = admis_and_recs[~(admis_and_recs['AUTHORITY_FOR_DETENTION_DESCRIPTION'] == 'Not Applicable')]

len(admis_and_recs) # 1746

#--------------- Check movement types
admis_and_recs['MOVE_TYPE_DESCRIPTION'].value_counts(dropna=False)

admis_and_recs.groupby(['MOVE_TYPE_DESCRIPTION','ADMISSION_CATEGORY']).size().reset_index(name='count')

    # Put all recalls under the Admission of 'Recalled after conditional discharge'
admis_and_recs.loc[admis_and_recs['MOVE_TYPE_DESCRIPTION'] == 'Recall','ADMISSION_CATEGORY'] = 'Recalled after conditional discharge'

#--------------- Gender
admis_and_recs['GENDER'].value_counts(dropna=False)

admis_and_recs[admis_and_recs['GENDER'].isna()]

admis_and_recs.loc[admis_and_recs['GENDER'].isna(),'GENDER'] = 'M'

admis_and_recs.loc[admis_and_recs['GENDER'] == 'M ( Was F )','GENDER'] = 'M'

admis_and_recs.loc[admis_and_recs['GENDER'] == 'F ( Was M )','GENDER'] = 'F'

#--------------- High Secure vs Secure Hospitals destinations

admis_and_recs['HOSP_TYPE'] = 'Secure Hospital'

high_secure_hospitals =['Ashworth Hospital', 'Broadmoor Hospital','Rampton Hospital','Rampton Hospital DSPD Unit']

admis_and_recs.loc[admis_and_recs['TO_ESTABLISHMENT_DESCRIPTION'].isin(high_secure_hospitals),'HOSP_TYPE'] = 'High Secure Hospital'

admis_and_recs[admis_and_recs['HOSP_TYPE'] == 'High Secure Hospital']['TO_ESTABLISHMENT_DESCRIPTION'].value_counts(dropna=False)

    # Work on copy
admis_and_recs_2 = admis_and_recs.copy()

#--------------- Populate Tables 1, 6, 7, 

    # Table 6
admis_and_recs_2.groupby(['HOSP_TYPE','GENDER']).size().reset_index(name='count').to_excel("Tables/Table 6.xlsx", index=False)

 # Table 7
order = ['Transferred from Prison Service establishment while unsentenced or untried',
       'Transferred from Prison Service establishment after sentence',
       'Hospital order with restriction order',
       'Recalled after conditional discharge',
       'Transferred from Scotland, Northern Ireland etc.',
       'Unfit to plead',
       'Not guilty by reason of insanity',
       'Hospital and limitation direction']

admis_and_recs_2['ADMISSION_CATEGORY'] = pd.Categorical(admis_and_recs_2['ADMISSION_CATEGORY'], ordered= True, categories=order)

admis_and_recs_2.groupby(['ADMISSION_CATEGORY']).size().reset_index(name='count').to_excel("Tables/Table 7.xlsx", index=False)

#--------------- Export As Parquet
    
    # Conversions to satisfy parquet
    
admis_and_recs_2['FILE_REFERENCE'] = admis_and_recs_2['FILE_REFERENCE'].astype(str)
admis_and_recs_2['NOMS_ID'] = admis_and_recs_2['NOMS_ID'].astype(str)
admis_and_recs_2['PRISON_NUMBER'] = admis_and_recs_2['PRISON_NUMBER'].astype(str)

admis_and_recs_2.to_parquet(f"s3://alpha-omppg/Mental Health/2023/Parquet Data/admrec_prepared_{year}.parquet")


