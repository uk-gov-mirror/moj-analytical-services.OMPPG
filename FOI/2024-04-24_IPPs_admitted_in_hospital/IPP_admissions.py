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

ipp_admissions = pd.read_excel("s3://alpha-omppg/FOI/2024-04-24_IPPs_admitted_in_hospital/IPP_Admissions_To_Hospital_as_at_24-04-24.xls")
ipp_admissions.shape #1064

ipp_admissions = ipp_admissions.replace("–","-", regex = True)

    # check datetime types
ipp_admissions.info() # 

ipp_admissions = ipp_admissions[~ipp_admissions['ACTUAL_DATE'].isna()]
ipp_admissions.shape #1056

ipp_admissions.head()

    # rearrange columns
# ipp_admissions.columns

retain_order = ['FILE_REFERENCE', 'FAMILY_NAME', 'ACTUAL_DATE',  'MOVE_TYPE_DESCRIPTION','MOVE_SUB_TYPE_DESCRIPTION',
                'MOVE_SUB_SUB_TYPE_DESCRIPTION','FROM_ESTABLISHMENT_DESCRIPTION','TO_ESTABLISHMENT_DESCRIPTION']

ipp_admissions = ipp_admissions[retain_order + [col for col in ipp_admissions.columns if col not in retain_order]]

ipp_admissions.head()

#---------------Remove duplicates

ipp_admissions[ipp_admissions.duplicated(subset=['FILE_REFERENCE','ACTUAL_DATE'],keep = False)].sort_values(['FILE_REFERENCE','ACTUAL_DATE']).head(10) #0 


ipp_admissions['CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

#---------------Remove Test cases
    # Check 'test' cases and remove
ipp_admissions[ipp_admissions['FAMILY_NAME'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

ipp_admissions[ipp_admissions['FIRST_NAMES'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

Test_Case_Mask =  (   (ipp_admissions['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (ipp_admissions['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (ipp_admissions['FILE_REFERENCE'] != 'T18122')

ipp_admissions = ipp_admissions[~Test_Case_Mask]

len(ipp_admissions) # 1747

    # Check 'case' cases and remove
ipp_admissions[ipp_admissions['FAMILY_NAME'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

ipp_admissions[ipp_admissions['FIRST_NAMES'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

    # Check 'digit' cases - these are normally good and shoulbe untouched
ipp_admissions[ipp_admissions['FAMILY_NAME'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none

ipp_admissions[ipp_admissions['FIRST_NAMES'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none


#--------------- Count instances of admissions
ipp_admissions['YEAR_ACTUAL'] =ipp_admissions['ACTUAL_DATE'].dt.to_period('Y')
ipp_admissions['YEAR_ACTUAL'].value_counts(dropna=False).reset_index(name='count')
ipp_admissions.groupby('YEAR_ACTUAL').size()

# Unique individuals
unique_cond = (ipp_admissions['ACTUAL_DATE'].dt.year >= 2012) & (ipp_admissions['ACTUAL_DATE'].dt.year <=2023)
dedups = ipp_admissions[unique_cond].drop_duplicates('FILE_REFERENCE')

dedups.shape
ipp_admissions.groupby(['AUTHORITY_FOR_DETENTION_DESCRIPTION','ADMISSION_CATEGORY']).size().reset_index(name='count') # check any non-matches

    # Remove non applicables and not specifieds
(ipp_admissions['AUTHORITY_FOR_DETENTION_DESCRIPTION'] == 'Not Applicable').sum() # 0

# In custody
pop2023 = pd.read_parquet(f"s3://alpha-omppg/Mental Health/2023/Parquet Data/population_prepared_2023.parquet")

pop2023.head()
pop2023.info()
pop2023[pop2023['STATUS']=='aHospital']['DA_CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)
pop2023['STATUS'].value_counts()
