""" 
GOAL: PRODUCE RESTRICTED PATIENTS STATISTICS FOR PUBLICATION
By Eric Nyame, 29/02/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib

from itables import show

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
# import prepareMatch
# importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
import TimeDiffs

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

#--------------- Import the population dataset and replace long dash with normal dash

pop = pd.read_excel("rp_population.xls")

len(pop)
pop = pop.drop_duplicates()
pop.head()

pop = pop.replace("–","-",regex=True) # replace long dashes with normal dashes
len(pop) # 8064

pop = pop[~pop['AUTHORITY_FOR_DETENTION_DESCRIPTION'].str.contains('Xfer from',case=False,na=False)]

pop['AUTHORITY_FOR_DETENTION_DESCRIPTION'].value_counts(dropna=False)



not_hospital_orders = ['S47/49 - MHA 1983 - Transfer from Prison','S48/49 - MHA 1983 - committed for Trial to CC',
                      'S48/49 - MHA 1983 - Remanded','S48/49 - MHA 1983 - Immigration Detainee','Not Applicable']

pop = pop[~pop['AUTHORITY_FOR_DETENTION_DESCRIPTION'].isin(not_hospital_orders)]

    # check datetime types
pop.info() # 6691

    # rearrange columns
retain_order = ['FILE_REFERENCE', 'FAMILY_NAME', 'DATE_OF_HOSPITAL_ORDER', 'DATE_RECEIVED_IN_MHU','AUTHORITY_FOR_DETENTION_DESCRIPTION','DA_STATUS_DESCRIPTION', 'END_DATE']

pop = pop[retain_order + [col for col in pop.columns if col not in retain_order]]

pop.head()
#---------------Year of hospital order should be up to 31 Dec of snapshot year

pop[pop['DATE_OF_HOSPITAL_ORDER'].isna()].head() #0

# pop[pop['DATE_RECEIVED_IN_MHU'].isna()].head() # not too important

pop['DATE_OF_HOSPITAL_ORDER'].dt.year.value_counts(dropna=False).sort_index().tail() # 10 in 2025

#---------------------------------- Remove Test cases
    # Check 'test' cases and remove
pop[pop['FAMILY_NAME'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none

pop[pop['FIRST_NAMES'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] #none

Test_Case_Mask =  (   (pop['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (pop['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (pop['FILE_REFERENCE'] != 'T18122')

# pop[Test_Case_Mask][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none
pop = pop[~Test_Case_Mask]

pop.shape  # 6688

    # Check 'case' cases and remove
pop[pop['FAMILY_NAME'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 4 all good

pop[pop['FIRST_NAMES'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0 good

    # Check 'digit' cases - these are normally good and shoulbe untouched
pop[pop['FAMILY_NAME'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none
pop[pop['FIRST_NAMES'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none

 # End dates before 31 should be removed - these are ended cases without their status set to closed
# pop[~pop['END_DATE'].isna()].head()

#--------------- Check active DAs

pop = pop.sort_values(by = ['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER'],ascending=[True,False])

pop[pop.duplicated(['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER','AUTHORITY_FOR_DETENTION_DESCRIPTION'], keep = False)] # 0

pop[pop.duplicated(['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER'], keep = False)] # 3 cases, but authority for dentention differs

# dups_pop = pop[pop.duplicated(['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER'], keep = False)] #
#len(dups_pop) # 120 cases
# dups_pop.head()

#--------------- Remove Non applicables and in foreign prisons

# pop[pop['AUTHORITY_FOR_DETENTION_DESCRIPTION'].isin(['Not Applicable', 'Not Specified'])]

pop = pop[~pop['AUTHORITY_FOR_DETENTION_DESCRIPTION'].isin(['Not Applicable', 'Not Specified'])]
len(pop) # 6685

# pop[pop['CURRENT_ESTABLISHMENT_DESCRIPTION'].str.contains('Foreign', case=False)]

pop = pop[~pop['CURRENT_ESTABLISHMENT_DESCRIPTION'].str.contains('Foreign', case=False)]
len(pop) # 7834

#---------------  Remove unrestricted patients

# pop['DA_CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

pop['DA_CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

pop = pop[pop['DA_CUSTODY_TYPE_DESCRIPTION'] != 'Unrestricted Patient']
len(pop) # 6685

#--------------- Gender

# pop.GENDER.value_counts(dropna=False)

pop.loc[pop['GENDER'] == 'M ( Was F )', 'GENDER'] = 'M'
pop.loc[pop['GENDER'] == 'F ( Was M )', 'GENDER'] = 'F'

#--------------- Status/Location
    
# pop['STATUS_DESCRIPTION'].value_counts(dropna=False)

# pop[pop['STATUS_DESCRIPTION']=='In Custody [*]'].head() # good

pop['STATUS'] = np.where(pop['STATUS_DESCRIPTION'] == 'Conditionally Discharged','bCD','aHospital')

# pd.crosstab(pop['STATUS_DESCRIPTION'],pop['STATUS'], margins = True, margins_name = 'Total')


#--------------- Export population before offence as Parquet
    
    # Conversions to satisfy parquet
    
pop['FILE_REFERENCE'] = pop['FILE_REFERENCE'].astype(str)
pop['NOMS_ID'] = pop['NOMS_ID'].astype(str)
pop['PRISON_NUMBER'] = pop['PRISON_NUMBER'].astype(str)

pop.to_parquet("output/pop.parquet")


""" 
GOAL: PRODUCE RESTRICTED PATIENTS STATISTICS FOR PUBLICATION
By Eric Nyame, 29/02/2024
"""

offences = pd.read_excel("rp_offences.xls")

offences = offences.replace("–","-",regex=True)

offences.info() # 13431

# We will deduplicate the offences after the match 

    # offences = offences.sort_values(by=['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER'])

    # offences[offences.duplicated(['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER','OFFENCE_DESCRIPTION'],keep=False)] # don't worry about these yet

offences['FILE_REFERENCE'] = offences['FILE_REFERENCE'].astype(str)
offences['PRISON_NUMBER'] = offences['PRISON_NUMBER'].astype(str)


query = """SELECT a.*, 
                  b.OFFENCE_DESCRIPTION, 
                  b.OFFENCE_GROUP_DESCRIPTION,
                  b.COURT_OFFENCE_TEXT
                  
            FROM pop AS a LEFT JOIN offences AS b
            
            ON  (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) 
            AND
                (a.DATE_OF_HOSPITAL_ORDER = b.DATE_OF_HOSPITAL_ORDER AND a.DATE_OF_HOSPITAL_ORDER IS NOT NULL) AND
                (a.AUTHORITY_FOR_DETENTION_DESCRIPTION = b.AUTHORITY_FOR_DETENTION_DESCRIPTION AND a.AUTHORITY_FOR_DETENTION_DESCRIPTION IS NOT NULL) """

pop_off = duckdb.sql(query).df()
len(pop_off) # 10654

pop_off.head()

# ----------------- Put together sorted missing offences

 retain_order = ['FILE_REFERENCE', 'FAMILY_NAME', 'DATE_OF_HOSPITAL_ORDER','AUTHORITY_FOR_DETENTION_DESCRIPTION','OFFENCE_DESCRIPTION','OFFENCE_GROUP_DESCRIPTION','COURT_OFFENCE_TEXT']

pop_off = pop_off[retain_order + [col for col in pop.columns if col not in retain_order]]

specified_offences = ["Harassment","Harass","Stalking","Stalk","Breach","Breaching","Injunction","Fear ","Restraining","Restrain","Racially","Race","Religiously","Religion","Controlling","Control","Coercive","Coerce"]

pattern = '|'.join(specified_offences)

pop_off[pop_off['OFFENCE_DESCRIPTION'].str.contains(pattern, case=False, na=False)]['OFFENCE_DESCRIPTION'].value_counts(dropna=False)

pop_off[pop_off['COURT_OFFENCE_TEXT'].str.contains(pattern, case=False, na=False)]['COURT_OFFENCE_TEXT'].value_counts(dropna=False)

show(pop_off[pop_off['COURT_OFFENCE_TEXT'].str.contains(pattern, case=False, na=False)]['COURT_OFFENCE_TEXT'].value_counts(dropna=False),buttons='excel5')

# Keep only susptected cases
pop_off = pop_off[pop_off['COURT_OFFENCE_TEXT'].str.contains(pattern, case=False, na=False)]
len(pop_off) # 463

pop_off['COURT_OFFENCE_TEXT'].value_counts()

pop_off[pop_off['COURT_OFFENCE_TEXT'].str.contains('drug|theft|suspended|prevent', case=False, na=False)]['COURT_OFFENCE_TEXT'].value_counts(dropna=False)

pop_off = pop_off[~pop_off['COURT_OFFENCE_TEXT'].str.contains('drug|theft|suspended|prevent', case=False, na=False)]
len(pop_off) # 389

pop_off.head()

pop_off.to_excel("output/pop.xlsx")
