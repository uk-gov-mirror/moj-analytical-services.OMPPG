""" 
GOAL: PRODUCE DISCHARGES AND DISPOSALS STATISTICS FOR RESTRICTED PATIENT PUBLICATION
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

#--------------- Import the population dataset based on date of authorisation

disch_and_disp = pd.read_excel(f"s3://alpha-omppg/Mental-Health/{year}/raw-data/Disposals_and_Discharges_up_to_{year}.xls")

disch_and_disp = disch_and_disp.replace("–","-", regex = True) # replace long dashes

disch_and_disp = disch_and_disp[disch_and_disp['AUTHORISATION_DATE'].dt.year == 2024]
len(disch_and_disp) # 1777

disch_and_disp = disch_and_disp.replace("–","-", regex = True) # replace long dashes

    # check datetime types
    
disch_and_disp.info() # 1603, all good

    # rearrange columns
# disch_and_disp.columns

retain_order = ['FILE_REFERENCE', 'FAMILY_NAME', 'ACTUAL_DATE','AUTHORISATION_DATE', 'AUTHORITY_FOR_DETENTION_DESCRIPTION', 'MOVE_TYPE_DESCRIPTION','MOVE_SUB_TYPE_DESCRIPTION',
                'MOVE_SUB_SUB_TYPE_DESCRIPTION','FROM_ESTABLISHMENT_DESCRIPTION','TO_ESTABLISHMENT_DESCRIPTION']

disch_and_disp = disch_and_disp[retain_order + [col for col in disch_and_disp.columns if col not in retain_order]]

disch_and_disp.head()

#---------------Remove duplicates on both authorization date and Actual date

disch_and_disp[disch_and_disp.duplicated(subset=['FILE_REFERENCE','AUTHORISATION_DATE'],keep = False)].sort_values(['FILE_REFERENCE','AUTHORISATION_DATE'])# none

disch_and_disp = disch_and_disp.drop(index=[121,127,124,119,136,46682])

len(disch_and_disp) # 1771, 1602

disch_and_disp[disch_and_disp.duplicated(subset=['FILE_REFERENCE','ACTUAL_DATE'],keep = False)].sort_values(['FILE_REFERENCE','ACTUAL_DATE']) # 6 rows

disch_and_disp = disch_and_disp.drop(index=[46946]) # some duplicates and incorrect entries

len(disch_and_disp) # 1770

#---------------Remove Test cases
   
disch_and_disp[disch_and_disp['FAMILY_NAME'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] #0

disch_and_disp[disch_and_disp['FIRST_NAMES'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

Test_Case_Mask =  (   (disch_and_disp['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (disch_and_disp['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (disch_and_disp['FILE_REFERENCE'] != 'T18122')

disch_and_disp = disch_and_disp[~Test_Case_Mask]

len(disch_and_disp) # 1600

    # Check 'case' cases and remove
disch_and_disp[disch_and_disp['FAMILY_NAME'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

disch_and_disp[disch_and_disp['FIRST_NAMES'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

    # Check 'digit' cases - these are normally good and shoulbe untouched
disch_and_disp[disch_and_disp['FAMILY_NAME'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none

disch_and_disp[disch_and_disp['FIRST_NAMES'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none

#--------------- Bring in movement reference file

ref_DispDischType_A = pd.read_excel("s3://alpha-omppg/Mental Health/Reference/Reference.xls", sheet_name = "DispDischType_A")
ref_DispDischType_B = pd.read_excel("s3://alpha-omppg/Mental Health/Reference/Reference.xls", sheet_name = "DispDischType_B")

ref_DispDischType_A.columns = ref_DispDischType_A.columns.str.upper()
ref_DispDischType_B.columns = ref_DispDischType_B.columns.str.upper()

ref_DispDischType_A = ref_DispDischType_A.replace("–","-", regex = True)
ref_DispDischType_B = ref_DispDischType_B.replace("–","-", regex = True)

# ref_DispDischType_A.info()
# ref_DispDischType_B.info()

#--------------- Determine movement type, first with refererence A

    # creates a dictionary of the reference to match without resorting to sql
    # make MOVE_SUB_TYPE_DESCRIPTION the key and DISPDISCH_TYPE the value.
    
ref_DispDischType_A_dict = dict(zip(ref_DispDischType_A['MOVE_SUB_TYPE_DESCRIPTION'],ref_DispDischType_A['DISPDISCH_TYPE'])) 

    # match discharge and disposal to the reference dictionary to obtain the DISPDISCH_TYPE column

disch_and_disp['DISPDISCH_TYPE'] = disch_and_disp['MOVE_SUB_TYPE_DESCRIPTION'].map(ref_DispDischType_A_dict).fillna('check') 

    # check any non-matches - those with 'check'
    
disch_and_disp[disch_and_disp['DISPDISCH_TYPE'] == 'check'].groupby(['MOVE_SUB_TYPE_DESCRIPTION','MOVE_SUB_SUB_TYPE_DESCRIPTION','DISPDISCH_TYPE']). \
                                                            size().reset_index(name='count') # sort it out later below

#--------------- Second, we obtain values of DISPDISCH_TYPE from refererence B where it's specified in reference A to do so.

    # create a dictionary with a tuple of MOVE_SUB_TYPE_DESCRIPTION and MOVE_SUB_SUB_TYPE_DESCRIPTION as keys with  DISPDISCH_TYPE as the value
    # The approach creates a multindex dataframe with one column, and converts the dataframe to a dictionary to match the dictionary for reference B
    
ref_DispDischType_B_dict = ref_DispDischType_B.set_index(['MOVE_SUB_TYPE_DESCRIPTION','MOVE_SUB_SUB_TYPE_DESCRIPTION'])['DISPDISCH_TYPE'].to_dict() 

    # Now match the two to obtain DISPDISCH_TYPE from reference B where reference A says "Use MOVE_SUB_SUB_TYPE_DESCRIPTION to match"
    
disch_and_disp.loc[disch_and_disp['DISPDISCH_TYPE'] =='Use MOVE_SUB_SUB_TYPE_DESCRIPTION to match','DISPDISCH_TYPE']= \
        disch_and_disp[disch_and_disp['DISPDISCH_TYPE'] =='Use MOVE_SUB_SUB_TYPE_DESCRIPTION to match'].\
        set_index(['MOVE_SUB_TYPE_DESCRIPTION','MOVE_SUB_SUB_TYPE_DESCRIPTION']).index.map(ref_DispDischType_B_dict.get).fillna('check') 

     # check any non-matches- those with check
    
disch_and_disp[disch_and_disp['DISPDISCH_TYPE'] == 'check'].groupby(['MOVE_SUB_TYPE_DESCRIPTION','MOVE_SUB_SUB_TYPE_DESCRIPTION','DISPDISCH_TYPE']).size().reset_index(name='count') # check any non-matches

# --------------- Sort out unmatchedata for Emma to check
    
# disch_and_disp[disch_and_disp['DISPDISCH_TYPE']=='check'].to_excel("to_check.xlsx", index=False) # 

# disch_and_disp[(disch_and_disp['ACTUAL_DATE'].isna()) | (disch_and_disp['ACTUAL_DATE'].dt.year < 2023)].to_excel("Emma_to_check_dates.xlsx", index=False) # 

# -------------------------- Fix unknown move sub sub

    # Fix Remissions

disch_and_disp[disch_and_disp['MOVE_SUB_TYPE_DESCRIPTION'] =='Remitted To Prison'].groupby(['AUTHORITY_FOR_DETENTION_DESCRIPTION','MOVE_SUB_TYPE_DESCRIPTION','MOVE_SUB_SUB_TYPE_DESCRIPTION','DISPDISCH_TYPE']).size().reset_index(name='count') 

unknown_remission =( (disch_and_disp['MOVE_SUB_TYPE_DESCRIPTION'] == 'Remitted To Prison') &
                     (disch_and_disp['MOVE_SUB_SUB_TYPE_DESCRIPTION'].isin(['Not Specified','Not Applicable']))
                   )

resume_sentence = disch_and_disp['AUTHORITY_FOR_DETENTION_DESCRIPTION'].isin(['S45A - MHA 1983 - Hospital & Limitation Direction','S47/49 - MHA 1983 - Transfer from Prison'])

resume_unsentenced = disch_and_disp['AUTHORITY_FOR_DETENTION_DESCRIPTION'].isin(['S48/49 - MHA 1983 - Immigration Detainee',
                                                                                 'S48/49 - MHA 1983 - Remanded',
                                                                                 'S48/49 - MHA 1983 - committed for Trial to CC'])

disch_and_disp.loc[unknown_remission & resume_sentence,'DISPDISCH_TYPE'] = 'gReturned to custody to resume sentence'

disch_and_disp.loc[unknown_remission & resume_unsentenced,'DISPDISCH_TYPE'] = 'hRemission of untried/unsentenced prisoners'

     # Fix Expiration

disch_and_disp['TO_SIMPLE']  = 'Hospital'
disch_and_disp['FROM_SIMPLE'] = 'Hospital'

disch_and_disp.loc[disch_and_disp['TO_ESTABLISHMENT_DESCRIPTION'].str.contains('HMP',regex =True),'TO_SIMPLE'] = 'Prison'
disch_and_disp.loc[disch_and_disp['FROM_ESTABLISHMENT_DESCRIPTION'].str.contains('HMP',regex =True),'FROM_SIMPLE'] = 'Prison'

disch_and_disp.loc[disch_and_disp['TO_ESTABLISHMENT_DESCRIPTION'].isin(['Community - England','Community - Wales']),'TO_SIMPLE'] = 'Community'
disch_and_disp.loc[disch_and_disp['FROM_ESTABLISHMENT_DESCRIPTION'].isin(['Community - England','Community - Wales']),'FROM_SIMPLE'] = 'Community'

disch_and_disp.loc[disch_and_disp['TO_ESTABLISHMENT_DESCRIPTION'].isin(['Not Specified','Not Applicable']),'TO_SIMPLE'] = 'Unknown'
disch_and_disp.loc[disch_and_disp['FROM_ESTABLISHMENT_DESCRIPTION'].isin(['Not Specified','Not Applicable']),'FROM_SIMPLE'] = 'Unknown'

#disch_and_disp[disch_and_disp['TO_SIMPLE'] =='Prison'].groupby('TO_ESTABLISHMENT_DESCRIPTION').size().reset_index(name='count')
#disch_and_disp[disch_and_disp['TO_SIMPLE'] =='Community'].groupby('TO_ESTABLISHMENT_DESCRIPTION').size().reset_index(name='count')
#disch_and_disp[disch_and_disp['TO_SIMPLE'] =='Unknown'].groupby('TO_ESTABLISHMENT_DESCRIPTION').size().reset_index(name='count')

disch_and_disp[disch_and_disp['MOVE_SUB_TYPE_DESCRIPTION'] =='Expired Restrictions'].groupby(['AUTHORITY_FOR_DETENTION_DESCRIPTION','MOVE_SUB_TYPE_DESCRIPTION','MOVE_SUB_SUB_TYPE_DESCRIPTION','FROM_SIMPLE','TO_SIMPLE','DISPDISCH_TYPE']).size().reset_index(name='count') 

unknown_expiration =( (disch_and_disp['MOVE_SUB_TYPE_DESCRIPTION'] == 'Expired Restrictions') &
                     (disch_and_disp['MOVE_SUB_SUB_TYPE_DESCRIPTION'].isin(['Not Specified','Not Applicable']))
                   )

disch_and_disp.loc[unknown_expiration,'DISPDISCH_TYPE'] = 'fRemained in Hospital'

disch_and_disp[disch_and_disp['DISPDISCH_TYPE'] =='check'].groupby(['MOVE_SUB_TYPE_DESCRIPTION','MOVE_SUB_SUB_TYPE_DESCRIPTION','DISPDISCH_TYPE']).size().reset_index(name='count') # check any non-matches

 # Fix Disposal
    
# disch_and_disp[disch_and_disp['DISPDISCH_TYPE'] =='check']

disch_and_disp[disch_and_disp['MOVE_SUB_TYPE_DESCRIPTION'].isin(['Disposal By Court','Disposal - Migrated'])].groupby(['AUTHORITY_FOR_DETENTION_DESCRIPTION','MOVE_SUB_TYPE_DESCRIPTION','MOVE_SUB_SUB_TYPE_DESCRIPTION','FROM_SIMPLE','TO_SIMPLE','DISPDISCH_TYPE']).size().reset_index(name='count') 

unknown_disposal =( (disch_and_disp['MOVE_SUB_TYPE_DESCRIPTION'].isin(['Disposal By Court','Disposal - Migrated'])) &
                     (disch_and_disp['MOVE_SUB_SUB_TYPE_DESCRIPTION'].isin(['Not Specified','Not Applicable']))
                   )

s48_49_37_41_dvcv = disch_and_disp['AUTHORITY_FOR_DETENTION_DESCRIPTION'].isin(['S48/49 - MHA 1983 - committed for Trial to CC',
                                                                                'S48/49 - MHA 1983 - Civil Prisoner',
                                                                                'S37/41 - MHA 1983 - Hospital Order',
                                                                                'DVCV - Unfit to Plead'])

disch_and_disp.loc[unknown_disposal & s48_49_37_41_dvcv,'DISPDISCH_TYPE'] = 'iDisposal at court (S48(2)) not into the community'

disch_and_disp[disch_and_disp['DISPDISCH_TYPE'] =='check'].groupby(['MOVE_SUB_TYPE_DESCRIPTION','MOVE_SUB_SUB_TYPE_DESCRIPTION','DISPDISCH_TYPE']).size().reset_index(name='count') # none

disch_and_disp[disch_and_disp['DISPDISCH_TYPE'] =='check']

disch_and_disp.loc[(disch_and_disp['DISPDISCH_TYPE'] =='check') &(disch_and_disp['MOVE_SUB_SUB_TYPE_DESCRIPTION'] =='Dual Detention'),
                  'DISPDISCH_TYPE'] = 'fRemained in Hospital'

disch_and_disp.loc[(disch_and_disp['DISPDISCH_TYPE'] =='check') &(disch_and_disp['MOVE_SUB_TYPE_DESCRIPTION'] =='Disposal By Court'),
                  'DISPDISCH_TYPE'] = 'iDisposal at court (S48(2)) not into the community'

disch_and_disp.loc[(disch_and_disp['DISPDISCH_TYPE'] =='check') &(disch_and_disp['MOVE_SUB_TYPE_DESCRIPTION'] =='Terminated Restrictions'),
                  'DISPDISCH_TYPE'] = 'fRemained in Hospital'

disch_and_disp.loc[(disch_and_disp['DISPDISCH_TYPE'] =='check') &(disch_and_disp['MOVE_SUB_TYPE_DESCRIPTION'] =='AD By Tribunal'),
                  'DISPDISCH_TYPE'] = 'zAD of Conditional Discharged Patient'

#--------------- Gender

disch_and_disp['GENDER'].value_counts(dropna=False)

# disch_and_disp.loc[disch_and_disp['GENDER'].isna(),'GENDER'] = 'M'

disch_and_disp.loc[disch_and_disp['GENDER'] == 'M ( Was F )','GENDER'] = 'M'

disch_and_disp.loc[disch_and_disp['GENDER'] == 'F ( Was M )','GENDER'] = 'F'

    # Work on copy
    
disch_and_disp_2 = disch_and_disp.copy()

# Check strange disposals

disch_and_disp_2[(disch_and_disp_2['FROM_SIMPLE'] != 'Hospital') & 
                (disch_and_disp_2['MOVE_SUB_TYPE_DESCRIPTION'].isin(['Disposal By Court','Expired Restrictions','Remitted To Prison']))] # Checks show all good.

#--------------- Populate Tables 1, 8, 

disch_and_disp_2[disch_and_disp_2['DISPDISCH_TYPE']=='iDisposal at court (S47) not into the community']

disch_and_disp_2.loc[47010,'DISPDISCH_TYPE'] = 'iDisposal at court (S48(2)) not into the community'

    # Table 8
disch_and_disp.groupby(['DISPDISCH_TYPE','MOVE_SUB_SUB_TYPE_DESCRIPTION','MOVE_SUB_TYPE_DESCRIPTION']).size().reset_index(name='count').to_excel("Tables/Table 8_temp_actual.xlsx", index=False) 

disch_and_disp_2.groupby(['DISPDISCH_TYPE']).size().reset_index(name='count').to_excel("Tables/Table 8 simple.xlsx", index=False)

#--------------- Export As Parquet
    
    # Conversions to satisfy parquet
    
disch_and_disp_2['FILE_REFERENCE'] = disch_and_disp_2['FILE_REFERENCE'].astype(str)
disch_and_disp_2['NOMS_ID'] = disch_and_disp_2['NOMS_ID'].astype(str)
disch_and_disp_2['PRISON_NUMBER'] = disch_and_disp_2['PRISON_NUMBER'].astype(str)

disch_and_disp_2.to_parquet(f"s3://alpha-omppg/Mental Health/2023/Parquet Data/dispdisch__prepared_actual_date{year}.parquet")

disch_and_disp_2.to_excel("Disch_and_Disp.xlsx")
