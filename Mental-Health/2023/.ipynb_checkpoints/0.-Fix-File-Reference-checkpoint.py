""" 
GOAL: ADD FILEREFERENCE FROM OFFENCE DATA TO THE POULATION DATA EMMA SENT ME.

BACKGROUND: WHEN EMMA SENT ME THE POPULATION DATASET, FILEREFERENCES HAD BEEN CORRUPTED IN EXCEL WITH SOMETHING LIKE 03/2667 
BECOMING SOMETHING LIKE MARCH.. IN EXCEL.RODUCE OFFENCE BREAKDOWNSRESTRICTED PATIENTS STATISTICS FOR PUBLICATION

By Eric Nyame, 29/02/2024
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

sys.path.append('/home/jovyan/OMPPG/Macro Library')
# from my_log import my_log
import Out_of_bounds_dates
importlib.reload(Out_of_bounds_dates)
import prepareMatch
importlib.reload(prepareMatch)
import openMatch
importlib.reload(openMatch)
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
snapshotDate = pd.Timestamp(2023,12,31)

#--------------- Import offence and Emma's population dataset.

offences = pd.read_excel("s3://alpha-omppg/Mental Health/2023/Raw Data/Offence_all.xls")
offences = offences.replace("–","-")

    # keep one unique file reference-prison number prison combo
offences = offences.drop_duplicates(subset=['FILE_REFERENCE','PRISON_NUMBER'])
#len(offences) # 30856

pop = pd.read_excel(f"s3://alpha-omppg/Mental Health/{year}/Raw Data/population.xlsx")
pop = pop.replace("–","-")
# len(pop) # 7842

#---------------------------------- Remove Test cases
    # Check 'test' cases and remove
# pop[pop['FAMILY_NAME'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

# pop[pop['FIRST_NAMES'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

Test_Case_Mask =  (   (pop['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (pop['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (pop['FILE_REFERENCE'] != 'T18122')

# pop[Test_Case_Mask][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 2 cases

pop = pop[~Test_Case_Mask]

pop.shape  #7840
pop['row'] = list(range(len(pop))) # similar to SAS _n_ for tracking entries

    # Check 'case' cases and remove
#pop[pop['FAMILY_NAME'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0
#pop[pop['FIRST_NAMES'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

    # Check 'digit' cases - these are normally good and shoulbe untouched
#pop[pop['FAMILY_NAME'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 
#pop[pop['FIRST_NAMES'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 

#---------------------------------- Ensure File Reference and Prison numbers are proper to avoid wrong matching

    # Check prison numbers without digits - should be set to missing unless it's unique
# pop[~pop['PRISON_NUMBER'].astype(str).str.contains(r'\d',na=False)][['FILE_REFERENCE','PRISON_NUMBER','FAMILY_NAME','FIRST_NAMES']]

# pop.loc[pop['PRISON_NUMBER'].isin(['Not Applicable']),'PRISON_NUMBER'] = np.nan # potential problem with only 'Not Applicable'

    # Check File reference without digits - should be set to missing
# pop[~pop['FILE_REFERENCE'].astype(str).str.contains(r'\d',na=False)][['FILE_REFERENCE','PRISON_NUMBER','FAMILY_NAME','FIRST_NAMES']] # none

len(pop) #7840

#---------------------------------- Bring in file reference from offence data
query = """SELECT a.*, 
                  b.FILE_REFERENCE AS FR2,
                  b.PRISON_NUMBER  AS PN2
                  
            FROM pop AS a LEFT JOIN offences AS b
            
            ON  (
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) OR
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)
                ) 
                """

pop2 = duckdb.sql(query).df()

# len(pop2) # 7840 -> 7843

# rearrange columsn for better viewing
retain = ['row','FILE_REFERENCE','FR2','PRISON_NUMBER','PN2','FAMILY_NAME','DATE_OF_HOSPITAL_ORDER','DATE_RECEIVED_IN_MHU',
          'AUTHORITY_FOR_DETENTION_DESCRIPTION','DA_STATUS_DESCRIPTION','END_DATE','CURRENT_ESTABLISHMENT_DESCRIPTION']

# If file references are different but prison numbers are the same, then repalce pop's file reference with offences' file reference

diff_flr_eq_pn = ((pop2['FILE_REFERENCE'] != pop2['FR2']) & (pop2['PRISON_NUMBER'] == pop2['PN2']))

# pop2[diff_flr_eq_pn][retain].head(20)

pop2.loc[diff_flr_eq_pn,'FILE_REFERENCE'] = pop2['FR2']

# pop2[pop2['FILE_REFERENCE'] != pop2['FR2']][retain].head(20) # 0

# pop2[pop2['PRISON_NUMBER'] != pop2['PN2']][retain].head(20)
# pop2[(pop2['PRISON_NUMBER'] != pop2['PN2']) & (~pop2['PN2'].isna())][retain].head(20) # 8
# pop2[(pop2['PRISON_NUMBER'] != pop2['PN2']) & (~pop2['PN2'].isin([None,'Not Applicable']))][retain].head(20)

pn_cond = ((pop2['PRISON_NUMBER'] != pop2['PN2']) & (~pop2['PN2'].isin([None,'Not Applicable'])))
pop2.loc[pn_cond,'PRISON_NUMBER'] = pop2['PN2']

# pop2[pop2.duplicated('FILE_REFERENCE',keep=False)][retain]

pop2 = pop2.drop(index=[1454,1650])
# pop2[pop2.duplicated('row',keep=False)][retain]
pop2 = pop2.drop(index=[6846])

pop2 = pop2.drop(['row','FR2','PN2'],axis=1)
pop2.head()
pop2 = pop2.drop_duplicates(subset=['FILE_REFERENCE','PRISON_NUMBER'])
# len(pop2)
pop = pop.drop(['row'],axis=1)
pop2 = pop2[pop.columns]

# Save to Amazon
# pop2.to_excel("s3://alpha-omppg/Mental Health/2023/Raw Data/population_2023.xlsx", index=False)

