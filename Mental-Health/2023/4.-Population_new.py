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

import re

from dateutil.relativedelta import relativedelta

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

#--------------- Import the population dataset and replace long dash with normal dash

pop = pd.read_excel(f"s3://alpha-omppg/Mental Health/{year}/Raw Data/population_{year}.xlsx")

pop = pop.replace("–","-",regex=True) # replace long dashes with normal dashes

    # check datetime types
pop.info() # 7840

    # rearrange columns
retain_order = ['FILE_REFERENCE', 'FAMILY_NAME', 'DATE_OF_HOSPITAL_ORDER', 'DATE_RECEIVED_IN_MHU','AUTHORITY_FOR_DETENTION_DESCRIPTION','DA_STATUS_DESCRIPTION', 'END_DATE']

pop = pop[retain_order + [col for col in pop.columns if col not in retain_order]]

pop.head()
#---------------Year of hospital order should be up to 31 Dec of snapshot year

pop[pop['DATE_OF_HOSPITAL_ORDER'].isna()].head()

pop.loc[[7812],'DATE_OF_HOSPITAL_ORDER'] = pd.Timestamp(2023,10,12)
pop.loc[[6620],'DATE_OF_HOSPITAL_ORDER'] = pd.Timestamp(2024,1,2)
pop.loc[[7608],'DATE_OF_HOSPITAL_ORDER'] = pd.Timestamp(2024,1,8)

# pop[pop['DATE_RECEIVED_IN_MHU'].isna()].head() # not too important

pop['DATE_OF_HOSPITAL_ORDER'].dt.year.value_counts(dropna=False).sort_index() # 4 in 2024

pop[pop['DATE_OF_HOSPITAL_ORDER'].dt.year > year]

pop.loc[[7816],'DATE_OF_HOSPITAL_ORDER']=pd.Timestamp(2023,12,15)

pop = pop.drop(index=[6620,7607,7608]) # 3 wrong entries

# pop['DATE_RECEIVED_IN_MHU'].dt.year.value_counts(dropna=False).sort_index() # not important

# pop[pop['DATE_RECEIVED_IN_MHU'].dt.year > year].head()  # not important

len(pop) # 7837


#---------------------------------- Remove Test cases
    # Check 'test' cases and remove
pop[pop['FAMILY_NAME'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none

pop[pop['FIRST_NAMES'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] #none

Test_Case_Mask =  (   (pop['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (pop['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (pop['FILE_REFERENCE'] != 'T18122')

# pop[Test_Case_Mask][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none
pop = pop[~Test_Case_Mask]

pop.shape  # 7837

    # Check 'case' cases and remove
pop[pop['FAMILY_NAME'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 6 all good

pop[pop['FIRST_NAMES'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 1 good

    # Check 'digit' cases - these are normally good and shoulbe untouched
pop[pop['FAMILY_NAME'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none
pop[pop['FIRST_NAMES'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none

 # End dates before 31 should be removed - these are ended cases without their status set to closed
# pop[~pop['END_DATE'].isna()].head()

#--------------- Keep the most recent DAs (agreed to be the way to to deduplicate dual detentions)

pop = pop.sort_values(by = ['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER'],ascending=[True,False])

dups_pop = pop[pop.duplicated('FILE_REFERENCE', keep = False)] # 0

len(dups_pop) # 0, good

pop = pop.drop_duplicates(subset = ['FILE_REFERENCE'],  keep='first').copy()

len(pop) # 7837

#--------------- Remove Non applicables and in foreign prisons

# pop[pop['AUTHORITY_FOR_DETENTION_DESCRIPTION'].isin(['Not Applicable', 'Not Specified'])]

pop = pop[~pop['AUTHORITY_FOR_DETENTION_DESCRIPTION'].isin(['Not Applicable', 'Not Specified'])]
len(pop) # 7835

# pop[pop['CURRENT_ESTABLISHMENT_DESCRIPTION'].str.contains('Foreign', case=False)]

pop = pop[~pop['CURRENT_ESTABLISHMENT_DESCRIPTION'].str.contains('Foreign', case=False)]
len(pop) # 7834

#---------------  Remove unrestricted patients

# pop['DA_CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

pop = pop[pop['DA_CUSTODY_TYPE_DESCRIPTION'] != 'Unrestricted Patient']
len(pop) # 7833

#--------------- Gender

# pop.GENDER.value_counts(dropna=False)

pop.loc[pop['GENDER'] == 'M ( Was F )', 'GENDER'] = 'M'
pop.loc[pop['GENDER'] == 'F ( Was M )', 'GENDER'] = 'F'

#--------------- Status/Location
    
# pop['STATUS_DESCRIPTION'].value_counts(dropna=False)

# pop[pop['STATUS_DESCRIPTION']=='In Custody [*]'].head() # good

pop['STATUS'] = np.where(pop['STATUS_DESCRIPTION'] == 'Conditionally Discharged','bCD','aHospital')

# pd.crosstab(pop['STATUS_DESCRIPTION'],pop['STATUS'], margins = True, margins_name = 'Total')

#-------------- Age

# pop['DOB'].isna().sum() # 0
# pop['DOB'].dt.year.min(), pop['DOB'].dt.year.max() # question DOB 1900

pop['AGE'] = pop.apply(lambda x: TimeDiffs.year_diff(x['DOB'],snapshotDate),axis=1)

# pop['AGE'].value_counts().sort_index()
# pop[['DOB','AGE']].head()

pop.loc[pop['AGE'] <= 20,'AGEBAND'] = '20 and under'
pop.loc[(pop['AGE'] > 20) & (pop['AGE'] <= 39),'AGEBAND'] = '21-39'
pop.loc[(pop['AGE'] > 39) & (pop['AGE'] <= 59),'AGEBAND'] = '40-59'
pop.loc[pop['AGE'] > 59 ,'AGEBAND'] = '60 or more' # formerly '60+'

# pd.crosstab(pop['AGE'],pop['AGEBAND'], margins = True, margins_name = 'Total')

#-------------- Ethnicity
pop['ETHNICITY_DESCRIPTION'].value_counts(dropna=False)

ref_Ethnicity = pd.read_excel("s3://alpha-omppg/Mental Health/Reference/Reference.xls", sheet_name = "Ethnicity")
ref_Ethnicity.head()

ref_Ethnicity = ref_Ethnicity.replace("–","-", regex = True)

# for i in zip(ref_Ethnicity['ETHNICITY_DESCRIPTION'],ref_Ethnicity['ETHNICITY_GROUP']):
    #print(i)
    
ref_Ethnicity_dict = dict(zip(ref_Ethnicity['ETHNICITY_DESCRIPTION'],ref_Ethnicity['ETHNICITY_GROUP'])) 

pop['ETHNICITY'] = pop['ETHNICITY_DESCRIPTION'].map(ref_Ethnicity_dict).fillna('check') 

    # check any non-matches
    
pop.groupby(['ETHNICITY_DESCRIPTION','ETHNICITY']).size().reset_index(name='count')

pop.groupby(['ETHNICITY']).size().reset_index(name='count').sort_values('count',ascending=False)

#--------------- Deduplicate

    # missing file reference repalcement with prison number
    
# pop[pop['FILE_REFERENCE'].isna()][['FILE_REFERENCE','PRISON_NUMBER']] # None
# pop.loc[pop['FILE_REFERENCE'].isna(),'FILE_REFERENCE'] = pop['PRISON_NUMBER']

    # check repeated file_reference
# pop[pop.duplicated(subset =['FILE_REFERENCE'], keep=False)] # 0

# pop[pop.duplicated(subset =['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER'], keep=False)] # 0

len(pop) # 7833

#--------------- Detention Authority reference file

ref_detAuth = pd.read_excel("s3://alpha-omppg/Mental Health/Reference/Reference.xls", sheet_name = "DetAuth")
ref_detAuth_dict = dict(zip(ref_detAuth['AUTHORITY_FOR_DETENTION_DESCRIPT'],ref_detAuth['DETAUTH']))

pop['DETAUTH'] = pop['AUTHORITY_FOR_DETENTION_DESCRIPTION'].map(ref_detAuth_dict).fillna('check')

 # check any non-matches
    
pop.groupby(['AUTHORITY_FOR_DETENTION_DESCRIPTION','DETAUTH']).size().reset_index(name='count')

pop.groupby(['DETAUTH']).size().reset_index(name='count').sort_values('count',ascending=False)

# pd.crosstab(pop['AUTHORITY_FOR_DETENTION_DESCRIPTION'],pop['DETAUTH'], margins = True, margins_name = 'Total')
# pop['DETAUTH'].isna().sum() #0

#--------------- Export population before offence as Parquet
    
    # Conversions to satisfy parquet
    
pop['FILE_REFERENCE'] = pop['FILE_REFERENCE'].astype(str)
pop['NOMS_ID'] = pop['NOMS_ID'].astype(str)
pop['PRISON_NUMBER'] = pop['PRISON_NUMBER'].astype(str)

pop.to_parquet(f"s3://alpha-omppg/Mental Health/2023/Parquet Data/population_prepared_{year}.parquet")

#--------------  breakdown all offences

    # Table 5
pd.crosstab([pop['GENDER'],pop['DETAUTH']],most_ser['STATUS'], margins = True, margins_name = 'Total').to_excel("Tables/Table_5.xlsx")

    # Table 9
pd.crosstab([pop['STATUS'],pop['ETHNICITY']],pop['STATUS'], margins = True, margins_name = 'Total').to_excel("Tables/Table_9.xlsx")

    # Table 2
pop.groupby(['STATUS','GENDER','AGEBAND']).size().reset_index(name='count').to_excel("Tables/Table_2.xlsx")
