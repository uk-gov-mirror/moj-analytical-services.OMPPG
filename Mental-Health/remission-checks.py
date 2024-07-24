""" 
GOAL: PRODUCE ADMISSION AaND RECALL STATISTICS FOR RESTRICTED PATIENT PUBLICATION
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

#************* MAIN ADMISSION CATEGORIES**********************************
"""
s45A/s45B = HOSPTAL DIRECTIONS. Court convicts but directs to hospital. 
       Prison sentence to be served after successful treatment in hospital.
    
s37/s41 = HOSPITAL ORDER with RESTRICTIONS added. 
          Issued by the court. Patient could be unfit or not guilty by insanity.
          Not guilty by isanity does not mean they didn't commit the offence?


s47/s49 =  TRANSFER OF CONVICTED PRISONERS with RESTRICTIONS added
           Secretary of State transfers a CONVICTED prisoner from prison to hospital. 

s48/s49 = TRANSFER OF UNCONVICTED PRISONERS with RESTRICTIONS added.
          Secretary of State transfers an UNSENTENCED prisoner from prison to hospital. 
          This could include remand, immigration detainees, unsentenced prisoners, civil prisoners.
"""
#*********************************************************************

#----------------------------------Set globals

year = 2023
# snapshotDate = pd.Timestamp(2023,12,31)

#--------------- Import the population dataset and replace long dash with normal dash

dispdisch = pd.read_sas(f"s3://alpha-omppg/Mental Health/dispdisch__prepared.sas7bdat",encoding='latin1')
dispdisch.to_excel("discharges_disposals.xlsx",index=False)

dispdisch = dispdisch.replace("–","-", regex = True)

    # check datetime types
dispdisch.info() # all good

dispdisch.head()

    # rearrange columns
# dispdisch.columns

retain_order = ['FILE_REFERENCE', 'FAMILY_NAME', 'ACTUAL_DATE',  'MOVE_TYPE_DESCRIPTION','MOVE_SUB_TYPE_DESCRIPTION',
                'MOVE_SUB_SUB_TYPE_DESCRIPTION','FROM_ESTABLISHMENT_DESCRIPTION','TO_ESTABLISHMENT_DESCRIPTION']

dispdisch = dispdisch[retain_order + [col for col in dispdisch.columns if col not in retain_order]]

dispdisch.head()

#---------------Remove duplicates

dispdisch[dispdisch.duplicated(subset=['FILE_REFERENCE','ACTUAL_DATE'],keep = False)].sort_values(['FILE_REFERENCE','ACTUAL_DATE']).head(10)

dispdisch = dispdisch.drop(index=[931,124])

len(dispdisch) # 1748

#---------------Remove Test cases
    # Check 'test' cases and remove
dispdisch[dispdisch['FAMILY_NAME'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

dispdisch[dispdisch['FIRST_NAMES'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

Test_Case_Mask =  (   (dispdisch['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (dispdisch['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (dispdisch['FILE_REFERENCE'] != 'T18122')

dispdisch = dispdisch[~Test_Case_Mask]

len(dispdisch) # 1747

    # Check 'case' cases and remove
dispdisch[dispdisch['FAMILY_NAME'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

dispdisch[dispdisch['FIRST_NAMES'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

    # Check 'digit' cases - these are normally good and shoulbe untouched
dispdisch[dispdisch['FAMILY_NAME'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none

dispdisch[dispdisch['FIRST_NAMES'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none

#--------------- Bring in DetAuth reference file
detAuth = pd.read_excel("s3://alpha-omppg/Mental Health/Reference/Reference.xls", sheet_name = "DetAuth")

detAuth = detAuth.replace("–","-", regex = True)

detAuth_dict = dict(zip(detAuth['AUTHORITY_FOR_DETENTION_DESCRIPT'],detAuth['DETAUTH_PUB'])) # creates a dictionary of DAs and their pub values

dispdisch['ADMISSION_CATEGORY'] =dispdisch['AUTHORITY_FOR_DETENTION_DESCRIPTION'].map(detAuth_dict).fillna('check') # Create Admissions Cat column matching reference

dispdisch.groupby(['AUTHORITY_FOR_DETENTION_DESCRIPTION','ADMISSION_CATEGORY']).size().reset_index(name='count') # check any non-matches

    # Remove non applicables and not specifieds
dispdisch = dispdisch[~(dispdisch['AUTHORITY_FOR_DETENTION_DESCRIPTION'] == 'Not Applicable')]

len(dispdisch) # 1746

#--------------- Check movement types
dispdisch['MOVE_TYPE_DESCRIPTION'].value_counts(dropna=False)

dispdisch.groupby(['MOVE_TYPE_DESCRIPTION','ADMISSION_CATEGORY']).size().reset_index(name='count')

    # Put all recalls under the Admission of 'Recalled after conditional discharge'
dispdisch.loc[dispdisch['MOVE_TYPE_DESCRIPTION'] == 'Recall','ADMISSION_CATEGORY'] = 'Recalled after conditional discharge'

#--------------- Gender
dispdisch['GENDER'].value_counts(dropna=False)

dispdisch[dispdisch['GENDER'].isna()]

dispdisch.loc[dispdisch['GENDER'].isna(),'GENDER'] = 'M'

dispdisch.loc[dispdisch['GENDER'] == 'M ( Was F )','GENDER'] = 'M'

dispdisch.loc[dispdisch['GENDER'] == 'F ( Was M )','GENDER'] = 'F'

#--------------- High Secure vs Secure Hospitals destinations

dispdisch['HOSP_TYPE'] = 'Secure Hospital'

high_secure_hospitals =['Ashworth Hospital', 'Broadmoor Hospital','Rampton Hospital','Rampton Hospital DSPD Unit']

dispdisch.loc[dispdisch['TO_ESTABLISHMENT_DESCRIPTION'].isin(high_secure_hospitals),'HOSP_TYPE'] = 'High Secure Hospital'

dispdisch[dispdisch['HOSP_TYPE'] == 'High Secure Hospital']['TO_ESTABLISHMENT_DESCRIPTION'].value_counts(dropna=False)

    # Work on copy
dispdisch_2 = dispdisch.copy()

#--------------- Populate Tables 1, 6, 7, 

    # Table 6
dispdisch_2.groupby(['HOSP_TYPE','GENDER']).size().reset_index(name='count').to_excel("Tables/Table 6.xlsx", index=False)

 # Table 7
order = ['Transferred from Prison Service establishment while unsentenced or untried',
       'Transferred from Prison Service establishment after sentence',
       'Hospital order with restriction order',
       'Recalled after conditional discharge',
       'Transferred from Scotland, Northern Ireland etc.',
       'Unfit to plead',
       'Not guilty by reason of insanity',
       'Hospital and limitation direction']

dispdisch_2['ADMISSION_CATEGORY'] = pd.Categorical(dispdisch_2['ADMISSION_CATEGORY'], ordered= True, categories=order)

dispdisch_2.groupby(['ADMISSION_CATEGORY']).size().reset_index(name='count').to_excel("Tables/Table 7.xlsx", index=False)

#--------------- Export As Parquet
    
    # Conversions to satisfy parquet
    
dispdisch_2['FILE_REFERENCE'] = dispdisch_2['FILE_REFERENCE'].astype(str)
dispdisch_2['NOMS_ID'] = dispdisch_2['NOMS_ID'].astype(str)
dispdisch_2['PRISON_NUMBER'] = dispdisch_2['PRISON_NUMBER'].astype(str)

dispdisch_2.to_parquet(f"s3://alpha-omppg/Mental Health/2023/Parquet Data/admrec_prepared_{year}.parquet")


