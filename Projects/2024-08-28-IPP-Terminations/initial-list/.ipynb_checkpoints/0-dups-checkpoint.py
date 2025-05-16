""" 
GOAL: ATTEMPT PRODUCE ALL IPPs/DPPs BY PPUD AS AT 16 AUGUST 2024

By Eric Nyame, 28/08/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
# import importlib

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
# import Out_of_bounds_dates
import prepareMatch
#importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
import TimeDiffs
# import tariff_groups

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

# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #

# IMPORT RELEASES AND RECALLS DATA
data1 = pd.read_excel("raw-data/All-IPP-DPP-Cases 09-10-2024.xlsx")
data2 = pd.read_excel("raw-data/All-IPP-DPP-Cases 16-10-2024.xls")
len(data2) # 8125
[col for col in data1.columns if col not in data2.columns ] #'IPP_TERMINATED_FLAG', 

retain = ['OFFENDER_ID',
 'IS FIRST RELEASE BEFORE DOS?',
 'ON IPP DASHBOARD? 21/08/2024',
 'ACTIVE TERMINATION REVIEW? (AS AT 19/08/24)',
 'Active Termination Review Type (as of 04/10/24)',
 'LICENCE TERMINATED? (AS AT 21/08/24)',
 'CANCELLED QUASHED REVIEW?',
 'DECEASED REVIEW STATUS',
 'Inactive Termination Review Status as of 04/10/24',
 'NOTES','STATUS_DESCRIPTION']

data2['FILE_REFERENCE'].isna().sum()
data1['FILE_REFERENCE'].isna().sum()

data1_simp = data1[['FILE_REFERENCE'] + retain]
data1_simp.head()
data1_simp = data1_simp.rename(columns ={'STATUS_DESCRIPTION':'OLD_STATUS'})

data2['ID'] = list(range(len(data2)))
data2.head()

data2 = pd.merge(data2,data1_simp,how='left',left_on='FILE_REFERENCE',right_on='FILE_REFERENCE')
len(data2)
data2[data2.duplicated('ID',keep=False)][['FILE_REFERENCE','FAMILY_NAME','STATUS_DESCRIPTION','OLD_STATUS']]

data2[data2['OLD_STATUS'].isna()][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES','STATUS_DESCRIPTION','OLD_STATUS']]
    # import sentence data
all_ipp_dpp = data2.copy()
all_ipp_dpp = all_ipp_dpp.drop_duplicates('ID',keep='first').copy()

# all_ipp_dpp = pd.read_excel("raw-data/All-IPP-DPP-Cases 16-10-2024.xls")
all_ipp_dpp.columns = all_ipp_dpp.columns.str.upper()
strip_blanks(all_ipp_dpp)

###-----------------------
  # Check 'test' cases and remove
all_ipp_dpp[all_ipp_dpp['FAMILY_NAME'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

all_ipp_dpp[all_ipp_dpp['FIRST_NAMES'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

all_ipp_dpp[all_ipp_dpp['PRISON_NUMBER'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES','PRISON_NUMBER']]


Test_Case_Mask =  (   (all_ipp_dpp['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (all_ipp_dpp['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (all_ipp_dpp['FILE_REFERENCE'] != 'T18122')

# all_ipp_dpp[Test_Case_Mask][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 3 cases

all_ipp_dpp = all_ipp_dpp[~Test_Case_Mask]
all_ipp_dpp.shape # 8114

    # Check 'case' cases and remove
all_ipp_dpp[all_ipp_dpp['FAMILY_NAME'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

all_ipp_dpp[all_ipp_dpp['FIRST_NAMES'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

    # Check 'digit' cases - these are normally good and shoulbe untouched
all_ipp_dpp[all_ipp_dpp['FAMILY_NAME'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 
all_ipp_dpp[all_ipp_dpp['FIRST_NAMES'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 
###-------------

# len(all_ipp_dpp) # 8114

all_ipp_dpp['FAMILY_NAME_ORIGINAL'] = all_ipp_dpp['FAMILY_NAME']
all_ipp_dpp =prepareMatch.prepareMatch(all_ipp_dpp)
all_ipp_dpp['FAMILY_NAME'] = all_ipp_dpp['FAMILY_NAME_ORIGINAL']
del all_ipp_dpp['FAMILY_NAME_ORIGINAL']
# all_ipp_dpp.head()

# all_ipp_dpp['NOMS_ID'].isna().sum() #232
# all_ipp_dpp['NOMS_START'].isna().sum() #232

# CREATE NEW UNIVERSAL IDENTIFIER - COMMON_NOMIS
all_ipp_dpp['COMMON_ID'] =all_ipp_dpp['NOMS_START']

# IDENTIFY THOSE WITH MISSING NOMS ID

all_ipp_dpp['MISSING_NOMS'] = False
all_ipp_dpp.loc[all_ipp_dpp['COMMON_ID'].isna(),'MISSING_NOMS'] = True 
# all_ipp_dpp['MISSING_NOMS'].value_counts() # 232 missing NOMS ID

# all_ipp_dpp[(~all_ipp_dpp['NOMS_ID'].isna()) &(all_ipp_dpp['NOMS_ID'] != all_ipp_dpp['NOMS_START'])] # only 11 cases
#all_ipp_dpp[all_ipp_dpp['NOMS_ID'].str.contains('A2206AY|A5216AA',case=False,na=False)]
#all_ipp_dpp[all_ipp_dpp['COMMON_ID']=='A3533AP']

#all_ipp_dpp[(~all_ipp_dpp['PRISON_NUMBER'].isna()) &(all_ipp_dpp['PRISON_NUMBER'] != all_ipp_dpp['PN_START'])] # only 11 cases
#all_ipp_dpp[all_ipp_dpp['NOMS_ID'].str.contains('A2206AY|A5216AA'

retain = ['CRO_PNC','FAMILY_NAME','FIRST_NAMES','FILE_REFERENCE','NOMS_ID','COMMON_ID','PRISON_NUMBER', 'CUSTODY_TYPE_DESCRIPTION','DOB','DOS','MISSING_NOMS','STATUS_DESCRIPTION']

# DUPLICATED FILE REFERENCE - AIM TO PULL NOMIS ID WHERE MISSING FROM THE OTHER RECORD

#all_ipp_dpp['TEMP_FILE_REF'] = all_ipp_dpp['FILE_REFERENCE'].astype(str).str.upper()
#dups = all_ipp_dpp[(~all_ipp_dpp['FILE_REFERENCE'].isna()) &
                   #(all_ipp_dpp.duplicated('TEMP_FILE_REF',keep=False))
                  #].copy() # not missing file reference to check duplicated cases
#dups = dups.sort_values('TEMP_FILE_REF')
#len(dups) # 100

#dups[retain +['TEMP_FILE_REF']]
#dups[dups['MISSING_NOMS'] == True][retain +['TEMP_FILE_REF']] # no duplicated file reference case has a missing nomis_id

#del all_ipp_dpp['TEMP_FILE_REF']

# DUPLICATED CRO_PNC - AIM TO PULL NOMIS ID WHERE MISSING FROM THE OTHER RECORD

all_ipp_dpp['TEMP_CRO'] = all_ipp_dpp['CRO_PNC'].astype(str).str.upper()
dups = all_ipp_dpp.loc[(~all_ipp_dpp['CRO_PNC'].isna()) & 
                       (all_ipp_dpp.duplicated('TEMP_CRO',keep=False))                      
                      ].copy() # not missing CRO_PNC reference to check duplicated cases
dups = dups.sort_values('TEMP_CRO')
# len(dups) # 119
# dups[dups['MISSING_NOMS'] == True][retain + ['TEMP_CRO']]# 10 cases

dups['COMMON_ID'] = dups.groupby('TEMP_CRO')['COMMON_ID'].transform(lambda x: x.ffill().bfill())
dups[(dups.duplicated('TEMP_CRO',keep=False)) & (dups['NOMS_ID'].isna())][retain +['TEMP_CRO']]
del dups['TEMP_CRO']

all_ipp_dpp = all_ipp_dpp[(all_ipp_dpp['CRO_PNC'].isna()) | 
                       (~all_ipp_dpp.duplicated('TEMP_CRO',keep=False))].copy()

all_ipp_dpp = pd.concat([all_ipp_dpp,dups])
# len(all_ipp_dpp) # 8114
all_ipp_dpp['MISSING_NOMS'] = False
all_ipp_dpp.loc[all_ipp_dpp['COMMON_ID'].isna(),'MISSING_NOMS'] = True 
# all_ipp_dpp['MISSING_NOMS'].value_counts() # 231 missing NOMS ID

# DUPLICATED PN_START - AIM TO PULL NOMIS ID WHERE MISSING FROM THE OTHER RECORD

#dups = all_ipp_dpp.loc[(~all_ipp_dpp['PN_START'].isna()) & 
                       #(all_ipp_dpp.duplicated('PN_START',keep=False))                      
                      #].copy() # not missing CRO_PNC reference to check duplicated cases
#dups = dups.sort_values('PN_START')
len(dups) # 123
#dups[dups['MISSING_NOMS'] == True][retain + ['PN_START']]# 9 cases

                                                
# DUPLICATED PRISON_NUMBER - AIM TO PULL NOMIS ID WHERE MISSING FROM THE OTHER RECORD

#all_ipp_dpp['TEMP_PN'] = all_ipp_dpp['PRISON_NUMBER'].astype(str).str.upper()
#dups = all_ipp_dpp.loc[(~all_ipp_dpp['PRISON_NUMBER'].isna()) & 
                       #(all_ipp_dpp.duplicated('TEMP_PN',keep=False))                      
                      #].copy() # not missing CRO_PNC reference to check duplicated cases
#dups = dups.sort_values('TEMP_PN')
#len(dups) # 104
#dups[dups['MISSING_NOMS'] == True][retain + ['TEMP_PN']]# 7 cases no NOMIS ID, so proceed

#del all_ipp_dpp['TEMP_PN']

# DUPLICATED FAMILY NAME AND DOB, - AIM TO PULL NOMIS ID WHERE MISSING FROM THE OTHER RECORD

#all_ipp_dpp['TEMP_FN'] = all_ipp_dpp['FAMILY_NAME'].astype(str).str.upper()
#all_ipp_dpp['TEMP_DOB'] = all_ipp_dpp['DOB'].astype(str).str.upper()
#dups = all_ipp_dpp.loc[(~all_ipp_dpp['FAMILY_NAME'].isna()) & 
                       #(all_ipp_dpp.duplicated(['TEMP_FN','TEMP_DOB'],keep=False))                      
                      #].copy() # not missing CRO_PNC reference to check duplicated cases
#dups = dups.sort_values(['TEMP_FN','TEMP_DOB'])
#len(dups) # 149

#dups[dups['MISSING_NOMS'] == True][retain + ['TEMP_FN','TEMP_DOB']]# 9 cases

#del all_ipp_dpp['TEMP_FN']
#del all_ipp_dpp['TEMP_DOB']
#len(all_ipp_dpp)

# SAME CRO BUT MISSING NOMS BOTH BOTH

all_ipp_dpp['TEMP_CRO'] = all_ipp_dpp['CRO_PNC'].astype(str).str.upper()
dups = all_ipp_dpp.loc[(~all_ipp_dpp['CRO_PNC'].isna()) &
                       (all_ipp_dpp.duplicated('TEMP_CRO',keep=False)) &
                       (all_ipp_dpp['MISSING_NOMS'] == True)
                      ].copy() # not missing CRO_PNC reference to check duplicated cases

dups = dups.sort_values('TEMP_CRO')
# len(dups) # 6
# dups[dups['MISSING_NOMS'] == True][retain + ['TEMP_CRO']] # 9 cases
dups['COMMON_ID'] = dups['TEMP_CRO']
# dups[dups['NOMS_ID'].isna()][retain + ['TEMP_CRO']]

all_ipp_dpp = all_ipp_dpp.loc[(all_ipp_dpp['CRO_PNC'].isna()) |
                       (~all_ipp_dpp.duplicated('TEMP_CRO',keep=False)) |
                       (~all_ipp_dpp['MISSING_NOMS'] == True)
                      ].copy()

all_ipp_dpp= pd.concat([all_ipp_dpp,dups])
del all_ipp_dpp['TEMP_CRO']
# len(all_ipp_dpp) # 8114

all_ipp_dpp['MISSING_NOMS'] = False
all_ipp_dpp.loc[all_ipp_dpp['COMMON_ID'].isna(),'MISSING_NOMS'] = True 
# all_ipp_dpp['MISSING_NOMS'].value_counts() # 225

# NOW STREAlINE NAMES, FILE REFERENCE AND PRISON NUMBER
# all_ipp_dpp[all_ipp_dpp['COMMON_ID'].isna()][retain + [col for col in all_ipp_dpp.columns if col not in retain]]

pattern = r'(?i)\(| AKA| DUPLICATE| FORMERLY'
all_ipp_dpp['FAMILY_NAME_2'] = all_ipp_dpp['FAMILY_NAME'].str.split(pattern).str[0].str.upper().str.strip()
all_ipp_dpp['PRISON_NUMBER_2'] = all_ipp_dpp['PRISON_NUMBER'].str.split(pattern).str[0].str.upper().str.strip()
all_ipp_dpp['FILE_REFERENCE_2'] = all_ipp_dpp['FILE_REFERENCE'].str.split(pattern).str[0].str.upper().str.strip()

# DUPLICATED FILE REFERENCE - AIM TO PULL NOMIS ID WHERE MISSING FROM THE OTHER RECORD

dups = all_ipp_dpp[(~all_ipp_dpp['FILE_REFERENCE_2'].isna()) &
                   (all_ipp_dpp.duplicated('FILE_REFERENCE_2',keep=False))
                  ].copy() # not missing file reference to check duplicated cases
dups = dups.sort_values('FILE_REFERENCE_2')
# len(dups) # 99

# dups[retain +['FILE_REFERENCE_2']]
# dups[dups['MISSING_NOMS'] == True][retain +['FILE_REFERENCE_2']] # 1 CASE
# dups[dups['PRISON_NUMBER']=='X30642']
all_ipp_dpp.loc[1950,'COMMON_ID'] = 'A0781AM'

# DUPLICATED PRISON_NUMBER

dups = all_ipp_dpp[(~all_ipp_dpp['PRISON_NUMBER_2'].isna()) &
                   (all_ipp_dpp.duplicated('PRISON_NUMBER_2',keep=False))
                  ].copy() # not missing file reference to check duplicated cases
dups = dups.sort_values('PRISON_NUMBER_2')
# len(dups) # 117

# dups[retain +['PRISON_NUMBER_2']]
# dups[dups['MISSING_NOMS'] == True][retain +['PRISON_NUMBER_2']] # 2 CASEs
dups[dups['PRISON_NUMBER']=='VK7808']
all_ipp_dpp.loc[all_ipp_dpp['PRISON_NUMBER'] =='VR4900','COMMON_ID'] = 'VR4900'
all_ipp_dpp.loc[210,'COMMON_ID'] = 'A5693AG'
all_ipp_dpp.loc[all_ipp_dpp['PRISON_NUMBER'] =='VK7808 DUPLICATE'] 
# DUPLICATED FAMILY NAMES AND DOB

all_ipp_dpp['TEMP_FN'] = all_ipp_dpp['FAMILY_NAME_2'].astype(str).str.upper()
dups = all_ipp_dpp.loc[(~all_ipp_dpp['FAMILY_NAME'].isna()) & 
                       (all_ipp_dpp.duplicated(['TEMP_FN','DOB'],keep=False))                      
                      ].copy() # not missing CRO_PNC reference to check duplicated cases
dups = dups.sort_values(['TEMP_FN','DOB'])
# len(dups) # 164

#dups[retain + ['TEMP_FN','DOB']]#
#dups[dups['MISSING_NOMS'] == True][retain + ['TEMP_FN','DOB']]# 5 cases
#dups[dups['COMMON_ID'].isna()][retain + ['TEMP_FN','DOB']]# 5 cases

#all_ipp_dpp.loc[all_ipp_dpp['FILE_REFERENCE'] =='W36442'][retain + ['TEMP_FN','DOB']]
all_ipp_dpp.loc[all_ipp_dpp['FAMILY_NAME'] =='Ward (Duplicate Of W36442)','COMMON_ID'] = 'A5366AE'
#all_ipp_dpp.loc[all_ipp_dpp['FILE_REFERENCE'] =='B46528']
all_ipp_dpp.loc[all_ipp_dpp['FILE_REFERENCE'] =='B46528','COMMON_ID'] = 'PV4333'

#all_ipp_dpp.loc[all_ipp_dpp['PRISON_NUMBER'] =='ML6276']
all_ipp_dpp.loc[all_ipp_dpp['FILE_REFERENCE'] =='76245','COMMON_ID'] = 'A7601AE'

#all_ipp_dpp[all_ipp_dpp['COMMON_ID'].isna()][retain + [] + [col for col in all_ipp_dpp.columns if col not in retain]]

#len(all_ipp_dpp[all_ipp_dpp['COMMON_ID'].isna()]) # 219

all_ipp_dpp.loc[all_ipp_dpp['COMMON_ID'].isna(),'COMMON_ID'] = all_ipp_dpp['PRISON_NUMBER']

len(all_ipp_dpp) # 8114

all_ipp_dpp_save =all_ipp_dpp.copy()

all_ipp_dpp.to_excel('all_ipp_dpp.xlsx',index=False)
