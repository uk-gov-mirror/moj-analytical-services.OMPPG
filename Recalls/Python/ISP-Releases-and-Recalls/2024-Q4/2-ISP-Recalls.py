""" 
GOAL: PRODUCE RE-RELEASES OF ISPS FOR OMSQ. A BY-PRODUCT IS FIRST RELEASES OF ISPS
By Eric Nyame, 05/02/2024
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

#----------------------------------globals are from 1.ISP Releases


#----------------------------------Import PPUD data

recallsPPUD = pd.read_excel(f's3://alpha-omppg/Recalls/PPUD/ISP/PPUD_ISP_Recalls_{year}Q{quarter}.xls')

strip_blanks(recallsPPUD)
recallsPPUD.info() # 10655, 10410,10176, 9906

    # Convert columns that should be datetime to datetime
recallsPPUD.select_dtypes(include=['object']).dtypes # find datetime column showing as an object column
dateColsToChange =['ISSUE_REVOCATION_TARGET']

        # Check bad dates
    
check1 = pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(recallsPPUD,col)],axis = 0,ignore_index=True)

check1= check1[dateColsToChange + [col for col in recallsPPUD.columns if col not in dateColsToChange]]
check1.head()
check1.shape #2 cases, mostly missing data represented as '00/01/1900 00:00:00'

    # Make two corrections to dates
for column in dateColsToChange:
    recallsPPUD.loc[recallsPPUD[column].astype(str).str.contains('2997'), column] = recallsPPUD[column].astype(str).str.replace('2997','2007', regex=True)
    recallsPPUD.loc[recallsPPUD[column]=="00/01/1900 00:00:00", column] = np.nan
    
    # Rerun check1 and see if if check1 is empty, then convert all datetime columns to datetime
check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(recallsPPUD,col)],axis = 0,ignore_index=True)
    
check1.shape # if zero, proceed

    # change certain columns to pandas datetime type

for column in dateColsToChange:
    recallsPPUD[column] = pd.to_datetime(recallsPPUD[column])

recallsPPUD.select_dtypes(include=['datetime64']).dtypes
recallsPPUD.head()
#---------------------------------- Add extra variables and rename

recallsPPUD['U_SENT'] = recallsPPUD['TARIFF_EXPIRY_DATE'].astype(str) + recallsPPUD['PRISON_NUMBER'].astype(str)

# recallsPPUD[recallsPPUD['TARIFF_EXPIRY_DATE'].isna()].head(50)[['PRISON_NUMBER','TARIFF_EXPIRY_DATE','U_SENT']]

recallsPPUD = recallsPPUD.rename(columns = {'CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION':'CUSTODY_TYPE_AT_RECALL'})

#---------------------------------- Remove Test cases
    # Check 'test' cases and remove
recallsPPUD[recallsPPUD['FAMILY_NAME'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

recallsPPUD[recallsPPUD['FIRST_NAMES'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

recallsPPUD[recallsPPUD['PRISON_NUMBER'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES','PRISON_NUMBER']]


Test_Case_Mask =  (   (recallsPPUD['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (recallsPPUD['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (recallsPPUD['FILE_REFERENCE'] != 'T18122')

recallsPPUD[Test_Case_Mask][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 2,3 cases

recallsPPUD2 = recallsPPUD[~Test_Case_Mask]
recallsPPUD2.shape # 10653, 10408,10175, 9904

    # Check 'case' cases and remove
recallsPPUD2[recallsPPUD2['FAMILY_NAME'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

recallsPPUD2[recallsPPUD2['FIRST_NAMES'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

    # Check 'digit' cases - these are normally good and shoulbe untouched
recallsPPUD2[recallsPPUD2['FAMILY_NAME'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 
recallsPPUD2[recallsPPUD2['FIRST_NAMES'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 

#---------------------------------- Drop duplicates

recallsPPUD2 = recallsPPUD2.drop_duplicates()

recallsPPUD2.shape
#---------------------------------- Recall date must be after dos

# recallsPPUD2['LICENCE_REVOKE_DATE'].dt.year.value_counts(dropna = False).sort_index()
# recallsPPUD2['DOS'].dt.year.value_counts(dropna = False).sort_index()

# recallsPPUD2[recallsPPUD['DOS'].isna()][['FILE_REFERENCE','PRISON_NUMBER','FAMILY_NAME','DOS','RELEASE_DATE','CUSTODY_TYPE_DESCRIPTION']]

    # Mimick SAS' handling of missing numeric/date variable
    
recallsPPUD2 = recallsPPUD2[(recallsPPUD2['LICENCE_REVOKE_DATE'].dt.date >= recallsPPUD2['DOS'].dt.date) | (recallsPPUD2['DOS'].isna())]
recallsPPUD2.shape

#---------------------------------- Count number of recalls per person per tarrif expiry date

recallsPPUD2 = recallsPPUD2.sort_values(by =['U_SENT','LICENCE_REVOKE_DATE'])

recallsPPUD2['RECALLNUM'] = recallsPPUD2.groupby('U_SENT').cumcount() + 1

#recallsPPUD2.head(50)[['FILE_REFERENCE','PRISON_NUMBER','TARIFF_EXPIRY_DATE','LICENCE_REVOKE_DATE','RECALLNUM']]

recallsPPUD2['RECALLNUM'].value_counts(dropna=False)

recallsPPUD2 = recallsPPUD2.drop(['U_SENT'],axis = 1)

recallsPPUD2.shape
#---------------------------------- Add information from reference lists to Recalls dataset

    # Import Lookup tables*/

CustodyRef = pd.read_excel(f's3://alpha-omppg/Recalls/Reference Data/Recalls Lookup.xls',sheet_name='CustodyType')
CustodyRef.columns = CustodyRef.columns.str.upper()
strip_blanks(CustodyRef)
CustodyRef.info()

AreaRef = pd.read_excel(f's3://alpha-omppg/Recalls/Reference Data/Recalls Lookup.xls',sheet_name='PS')
AreaRef.columns = AreaRef.columns.str.upper()
strip_blanks(AreaRef)
AreaRef.info()

query = """SELECT a.*, 
                   b.CUSTODYTYPE, 
                   b.CUSTODYTYPE2,
                   c.PROB_AREA, 
                   c.SUP_BODY, 
                   c.NPS_CRC_NAME
      
            FROM recallsPPUD2 AS a LEFT JOIN CustodyRef AS b 
            ON  (a.CUSTODY_TYPE_AT_RECALL = b.CUSTODY_TYPE_AT_RECALL) 
                                   LEFT JOIN AreaRef as c
            ON  (a.PROBATION_AREA_DESCRIPTION = c.PROBATION_AREA_DESCRIPTION)
            WHERE a.PROBATION_AREA_DESCRIPTION != 'Scotland' and
            a.PROBATION_AREA_DESCRIPTION != 'Northern Ireland' """

Recalls_Matched = duckdb.sql(query).df()
Recalls_Matched.shape # 10654, 10409,10176, 9905

Recalls_Matched[Recalls_Matched['CUSTODYTYPE'].isna()]['CUSTODY_TYPE_AT_RECALL'].unique() # unspecifieds
Recalls_Matched[Recalls_Matched['PROB_AREA'].isna()]['PROBATION_AREA_DESCRIPTION'].unique() # 0

#---------------------------------- Add extra variables

rec_filter = (
    (Recalls_Matched['LICENCE_REVOKE_DATE'] >= Recalls_Matched['TARIFF_EXPIRY_DATE']) |
    (Recalls_Matched['TARIFF_EXPIRY_DATE'].isna()) |
    (Recalls_Matched['TARIFF_EXPIRY_DATE'].dt.year == 1900) |
    (Recalls_Matched['TARIFF_EXPIRY_DATE'] < Recalls_Matched['DOS'])
)

recalls_final = Recalls_Matched[rec_filter].copy()

recalls_final['FURTHER_CHARGE'] = np.where(recalls_final['RECALL_REASON_DESCRIPTIONS'].str.contains('Further',case=False,na=False),100,0)

recalls_final['FURTHER_CHARGE'].value_counts(dropna=False)

recalls_final.loc[recalls_final['LICENCE_REVOKE_DATE'].dt.date < pd.Timestamp(2014,6,1).date(),'SUP_BODY'] = 'a. Probation'

recalls_final.loc[recalls_final['GENDER'] == 'F ( Was M )','GENDER'] = 'F'
recalls_final.loc[recalls_final['GENDER'] == 'M ( Was F )','GENDER'] = 'M'

# recalls_final['GENDER'].value_counts(dropna=False)

recalls_final['UNIQUEREF'] = recalls_final['PRISON_NUMBER'].astype(str) + recalls_final['LICENCE_REVOKE_DATE'].astype(str)

recalls_final[recalls_final['UNIQUEREF'].isna()]

# recalls_final.loc[recalls_final['TARIFF_EXPIRY_DATE'].dt.year < 2010,'RECALLNUM'] = np.nan

#---------------------------------- deduplicate

recalls_nodup = recalls_final.drop_duplicates(subset='UNIQUEREF', keep ='first').copy()
recalls_nodup.shape # 10640, 10395, 10162, 9891

#---------------------------------- Identify next recalls dates (not previous recalls)

    # Sort the DataFrame by PRISON_NUMBER and LRD in ascending order
recalls_nodup = recalls_nodup.sort_values(by=['PRISON_NUMBER', 'LICENCE_REVOKE_DATE'])

# Create the NEXT_RELEASE_DATE column by shifting RELEASE_DATE up by one within each PRISON_NUMBER group
recalls_nodup['NEXT_RECALL_DATE'] = recalls_nodup.groupby('PRISON_NUMBER')['LICENCE_REVOKE_DATE'].shift(-1)

recalls_nodup.head(50)[['PRISON_NUMBER', 'LICENCE_REVOKE_DATE','NEXT_RECALL_DATE']]

recalls_nodup.head()

recalls_nodup = recalls_nodup.drop(['UNIQUEREF'],axis = 1)

#---------------------------------- Temporary Save, delete later

recalls_nodup.to_parquet(f"isp_recalls_{year}q{quarter}_step1.parquet")

