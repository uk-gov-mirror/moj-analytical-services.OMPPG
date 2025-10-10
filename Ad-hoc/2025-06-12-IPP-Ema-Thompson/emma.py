""" 
GOAL: PRODUCE ISP POP FOR OMSQ. 
By Eric Nyame, 05/02/2024
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

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
import prepareMatch
#importlib.reload(prepareMatch)
import openMatch
# importlib.reload(openMatch)
import TimeDiffs
import tariff_groups

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
        
#---------------------------------- globals are already set


#----------------------------------Import PPUD data
ippippRecalls =  pd.read_excel(f's3://alpha-omppg/Ad hoc/2025-06-12-IPP-Ema-Thompson/IPP_Recalls_Apr-May_2025.xls')
receptions = pd.read_excel(f's3://alpha-omppg/Ad hoc/2025-06-12-IPP-Ema-Thompson/MIS-National-Receptions-Apr-11June-2025.xlsx')

receptions.columns = receptions.columns.str.upper()
receptions.columns = receptions.columns.str.replace(" ","_")
ippRecalls =  ippRecalls.replace("–","-",regex=True) # replace long dashes with normal dashes

ippRecalls =  ippRecalls[~ippRecalls['LICENCE_REVOKE_DATE'].isna()]

ippippRecalls[ippippRecalls['RESCIND_FLAG'] == True] # none
len(ippippRecalls) # 72

ippippRecalls.head()

receptions.head()

# Remove duplicate recalls from recalls data

ippRecalls[ippRecalls.duplicated(['FILE_REFERENCE','LICENCE_REVOKE_DATE'], keep=False)] # none

ippRecalls[ippRecalls.duplicated(['FAMILY_NAME', 'DOB', 'LICENCE_REVOKE_DATE'], keep=False)] # none

# remove blanks
strip_blanks(ippippRecalls)
strip_blanks(receptions)

    # Convert columns that should be datetime to datetime
ippRecalls.select_dtypes(include=['object']).dtypes

ippRecalls.select_dtypes(include=['datetime64']).dtypes


#---------------------------------- Remove Test cases
    # Check 'test' cases and remove
ippRecalls[ippRecalls['FAMILY_NAME'].str.contains('Test|Lumen',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none

ippRecalls[ippRecalls['FIRST_NAMES'].str.contains('Test|Lumen',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

ippRecalls[ippRecalls['PRISON_NUMBER'].str.contains('Test|Lumen',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES','PRISON_NUMBER']]


Test_Case_Mask =  (   (ippRecalls['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (ippRecalls['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (ippRecalls['FILE_REFERENCE'] != 'T18122')

# ippRecalls[Test_Case_Mask][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 3 cases

# ippRecalls =  ippRecalls[~Test_Case_Mask]
ippRecalls.shape # 7415

    # Check 'case' cases and remove
ippRecalls[ippRecalls['FAMILY_NAME'].str.contains('Case|Lumen',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

ippRecalls[ippRecalls['FIRST_NAMES'].str.contains('Case|Lumen',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

    # Check 'digit' cases - these are normally good and shoulbe untouched
ippRecalls[ippRecalls['FAMILY_NAME'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 
ippRecalls[ippRecalls['FIRST_NAMES'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 

ippRecalls = prepareMatch.prepareMatch(ippRecalls)

ippRecalls['LICENCE_REVOKE_DATE'] = ippRecalls['LICENCE_REVOKE_DATE'].dt.normalize()
receptions['MOV_TIME'] = receptions['MOV_TIME'].dt.normalize()

receptions.head()

#---------------------------------- Match to A&O Dataset on either NOMIS number, Prison Number or Name and DOB

query = """SELECT DISTINCT b.*, 
                            a.TO AS TO_PRISON, 
                            a.FROM AS FROM_LOCATION,
                            a.MOVEMENT_REASON,
                            a.MOV_TIME
                            
                    FROM ippRecalls AS b LEFT JOIN receptions AS a
                    
                    ON (b.LICENCE_REVOKE_DATE <= a.MOV_TIME) AND 
                      (a.NOMS_ID = b.NOMS_ID OR
                       a.NOMS_ID = b.NOMS_TRIM OR
                       a.NOMS_ID = b.NOMS_START OR
                       a.NOMS_ID = b.NOMS_END OR
                       a.NOMS_ID = b.PRISON_NUMBER OR
                       a.NOMS_ID = b.PN_TRIM OR
                       a.NOMS_ID = b.PN_START OR
                       a.NOMS_ID = b.PN_END)"""

matched1 = duckdb.sql(query).df()
matched1.shape # 114
matched1.head()

matched1 = matched1.sort_values(by=['FILE_REFERENCE','LICENCE_REVOKE_DATE','MOV_TIME'],ascending = [True,True,True])

# within each group, grab the first TO_PRISON
matched1['RECALL_RECPTION_PRISON'] = (
    matched1
      .groupby(['FILE_REFERENCE', 'LICENCE_REVOKE_DATE'])['TO_PRISON']
      .transform('first')
)

matched1['CURRENT_LOCATION'] = (
    matched1
      .groupby(['FILE_REFERENCE', 'LICENCE_REVOKE_DATE'])['TO_PRISON']
      .transform('last')
)

cols = ['NOMS_ID','FAMILY_NAME','LICENCE_REVOKE_DATE','MOV_TIME','CURRENT_ESTABLISHMENT_DESCRIPTION','TO_PRISON','RECALL_RECPTION_PRISON','CURRENT_LOCATION','MOVEMENT_REASON']

matched1 = matched1[cols + [col for col in matched1.columns if col not in cols]]

matched1[matched1.duplicated(['FILE_REFERENCE','LICENCE_REVOKE_DATE'],keep=False)]

matched2 = matched1.drop_duplicates(subset=['FILE_REFERENCE','LICENCE_REVOKE_DATE'], keep ='first').copy()

len(matched2)

matched2.to_excel('ipp_recalls_Apr_May_2025.xlsx',index=False)

