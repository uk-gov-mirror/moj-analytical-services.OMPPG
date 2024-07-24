""" 
PQ: 21522 – (ordinary) To ask the Secretary of State for Justice, how many 
(a) male prisoners, 
(b) women prisoners and 
(c) young offenders 
were transferred to hospital under the Mental Health Act 1983 in each year since 2010

By Eric Nyame, 17/04/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys

# import importlib

sys.path.append('/home/jovyan/OMPPG/Macro Library')
import Out_of_bounds_dates
# importlib.reload(Out_of_bounds_dates)
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

#--------------- Import admissions data

admissions = pd.read_excel(f"s3://alpha-omppg/PQs/2024 04 17 Transfers from prison to secure hospital/Transfers_from_prison_2013_to_2022.xls")

    # check date columns have datetime type
    
admissions.info() # all good

admissions.head()

    # rearrange columns for nicer viewing
# admissions.columns

retain_order = ['FILE_REFERENCE', 'FAMILY_NAME', 'ACTUAL_DATE',  'GENDER','DOB','MOVE_TYPE_DESCRIPTION','MOVE_SUB_TYPE_DESCRIPTION',
                'MOVE_SUB_SUB_TYPE_DESCRIPTION','FROM_ESTABLISHMENT_DESCRIPTION','TO_ESTABLISHMENT_DESCRIPTION']

admissions = admissions[retain_order + [col for col in admissions.columns if col not in retain_order]]

admissions.head()

#---------------Remove duplicates
admissions['AUTHORITY_FOR_DETENTION_DESCRIPTION'].value_counts(dropna=False)

admissions = admissions[admissions['AUTHORITY_FOR_DETENTION_DESCRIPTION'].str.contains('47/49|48/49|Xfer')]
    
    # save duplicates for George to check
dups = admissions[admissions.duplicated(subset=['FILE_REFERENCE','ACTUAL_DATE'],keep = False)].sort_values(['FILE_REFERENCE','ACTUAL_DATE']).head(10)
dups.to_excel('dups.xlsx',index = False)
    
    # remove duplicates
admissions = admissions.drop_duplicates(subset=['FILE_REFERENCE','ACTUAL_DATE'], keep ='first')
len(admissions) # 10295

#---------------Remove Test cases
    # Check 'test' cases and remove
admissions[admissions['FAMILY_NAME'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]
admissions[admissions['FIRST_NAMES'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

Test_Case_Mask =  (   (admissions['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (admissions['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (admissions['FILE_REFERENCE'] != 'T18122')

admissions = admissions[~Test_Case_Mask]

len(admissions) # 

    # Check 'case' cases and remove
admissions[admissions['FAMILY_NAME'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0
admissions[admissions['FIRST_NAMES'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

    # Check 'digit' cases - these are normally good and shoulbe untouched
admissions[admissions['FAMILY_NAME'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none
admissions[admissions['FIRST_NAMES'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none

#--------------- Gender
admissions['GENDER'].value_counts(dropna=False)

    # check missing gender and save for PPUD checks
missing_gender = admissions[admissions['GENDER'].isna()]
missing_gender.to_excel('missing_gender.xlsx',index=False)

admissions.loc[admissions['GENDER'] == 'M ( Was F )','GENDER'] = 'M'

admissions.loc[admissions['GENDER'] == 'F ( Was M )','GENDER'] = 'F'
admissions.loc[admissions['GENDER'] == 'F( Was M )','GENDER'] = 'F'

#-------------- Age

admissions['DOB'].isna().sum() # 0
admissions['DOB'].dt.year.min(), admissions['DOB'].dt.year.max() # question DOB 1900

incorrect_age = admissions[(admissions['ACTUAL_DATE'] <= admissions['DOB'])]
incorrect_age.to_excel('incorrect_age.xlsx',index=False)

admissions = admissions.copy()
admissions['AGE'] = np.nan
admissions['AGE'] = admissions.apply(lambda x: TimeDiffs.year_diff(x['DOB'],x['ACTUAL_DATE']),axis=1) # TimeDiffs is my own module

# admissions['AGE'].value_counts().sort_index()
# admissions[['DOB','AGE']].head()

    # Classify young offenders
admissions.loc[admissions['AGE'] < 18,'AGEBAND'] = 'under 18'
admissions.loc[admissions['AGE'] >= 18,'AGEBAND'] = '18 and over'

# Tabulate
admissions['ACTUAL_YEAR'] = admissions['ACTUAL_DATE'].dt.year
admissions.head()

pd.crosstab(admissions['GENDER'],admissions['ACTUAL_YEAR'], margins = True, margins_name = 'Total')

pd.crosstab(admissions['AGEBAND'],admissions['ACTUAL_YEAR'], margins = True, margins_name = 'Total')

pd.crosstab(admissions['AGE'],admissions['AGEBAND'], margins = True, margins_name = 'Total')