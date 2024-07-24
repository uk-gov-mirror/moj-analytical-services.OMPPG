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

# Set display options

pd.options.display.max_columns = None
pd.options.display.max_rows = None

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

#----------------------------------Set globals

year = 2022 
quarter = 4 

#----------------------------------Load prepared releases and recall datasets

recalls = pd.read_pickle(f'isp_recalls_{year}q{quarter}.pkl')
releases = pd.read_pickle(f'isp_releases_{year}q{quarter}.pkl')

recalls.info()
releases.info()

#sasReleases = pd.read_sas("s3://alpha-omppg/ISP Releases/Final Data/isp_releases_2023q4.sas7bdat",encoding='latin1')
#sasReleases.columns = sasReleases.columns.str.upper()
#sasReleases.info()
#sasReleases.sort_values('RELEASE_DATE',ascending=False).head()

#---------------------------------- Add last recall to releases dataset

query = """SELECT a.*, 
                  b.LICENCE_REVOKE_DATE AS LAST_LICENCE_REVOKE_DATE, 
                  b.RTC_DATE AS LAST_RTC_DATE, 
                  b.RECALLNUM AS LAST_RECALLNUM,
                  b.NUMBER_OF_RECALL_REASONS AS LAST_RECALL_NUMBER_OF_REASONS, 
                  b.RECALL_REASON_DESCRIPTIONS AS LAST_RECALL_REASONS,
                  b.NPS_CRC_NAME AS LAST_RECALL_AREA,
                  b.FURTHER_CHARGE AS LAST_RECALL_FURTHER_CHARGE, 
                  b.PRISON_NUMBER AS REC_PRISNUM, 
                  b.FILE_REFERENCE AS REC_FILEREF,
                  b.FAMILY_NAME AS REC_SURNAME, 
                  b.DOB AS REC_DOB
                  
            FROM releases AS a LEFT JOIN recalls AS b
            
            ON  (a.RELEASE_DATE > b.RTC_DATE) AND
                (a.RELEASE_DATE > b.LICENCE_REVOKE_DATE) AND
                (a.RELEASE_DATE <= b.NEXT_RECALL_DATE OR  b.NEXT_RECALL_DATE IS NULL) AND
                (
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL)
                )"""

recall_to_release = duckdb.sql(query).df()
recall_to_release.info() #15481

def calculate_match(row):
   
    condition_a = (row['FILE_REFERENCE'] == row['REC_FILEREF'])
    condition_b = (row['PRISON_NUMBER'] == row['REC_PRISNUM'])
      
    if condition_a and condition_b:
        return 2
    elif condition_a:
        return 1
    elif condition_b:
        return 1
    else:
        return 0

# Apply the function to each row
recall_to_release['MATCH'] = recall_to_release.apply(calculate_match, axis=1)

# recall_to_release[recall_to_release['PRISON_NUMBER'].isna()].head()[['FILE_REFERENCE','REC_FILEREF','MATCH','PRISON_NUMBER','REC_PRISNUM']]

# recall_to_release['MATCH'].value_counts(dropna=False)

#---------------------------------- deduplicate
recall_to_release.sort_values(by=['MATCH','LAST_LICENCE_REVOKE_DATE'],ascending = [False,False], inplace = True)
recall_to_release.drop_duplicates(subset=['PRISON_NUMBER','RELEASE_DATE'], keep ='first', inplace = True)
recall_to_release.shape # 15476

#---------------------------------- Add next recall to releases dataset

recall_to_release = recall_to_release.drop(['REC_DOB','REC_SURNAME','REC_FILEREF','REC_PRISNUM'],axis=1)

query2 = """SELECT a.*, 
                b.LICENCE_REVOKE_DATE AS NEXT_LICENCE_REVOKE_DATE, 
                b.RTC_DATE AS NEXT_RTC_DATE,
                b.RECALLNUM AS NEXT_RECALLNUM,
                b.NUMBER_OF_RECALL_REASONS AS NEXT_RECALL_NUMBER_OF_REASONS, 
                b.RECALL_REASON_DESCRIPTIONS AS NEXT_RECALL_REASONS,
                b.FURTHER_CHARGE AS NEXT_RECALL_FURTHER_CHARGE,
                b.NPS_CRC_NAME AS NEXT_RECALL_AREA,
                b.CUSTODYTYPE AS NEXT_RECALL_CUSTODYTYPE,
                b.PRISON_NUMBER AS REC_PRISNUM, b.FILE_REFERENCE AS REC_FILEREF,
                b.FAMILY_NAME AS REC_SURNAME, 
                b.DOB AS REC_DOB
        
            FROM recall_to_release AS a LEFT JOIN recalls AS b
            
            ON  (a.RELEASE_DATE <= b.LICENCE_REVOKE_DATE) AND
                (a.NEXT_RELEASE_DATE > b.LICENCE_REVOKE_DATE OR a.NEXT_RELEASE_DATE IS NULL) AND
                (
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL)
                )"""


recall_to_release2 = duckdb.sql(query2).df()
recall_to_release2.info()

#recall_to_release2[recall_to_release2['FILE_REFERENCE']=='K13370'].sort_values('RELEASE_DATE')
#sasReleases[sasReleases['FILE_REFERENCE']=='K13370'].sort_values('RELEASE_DATE')
#isp_releases_final[isp_releases_final['FILE_REFERENCE']=='K13370'].sort_values('RELEASE_DATE')

# Apply the function to each row
recall_to_release2['MATCH'] = recall_to_release2.apply(calculate_match, axis=1)

recall_to_release2['MATCH'].value_counts(dropna=False)

recall_to_release2['UNIQUEREF']= recall_to_release2['PRISON_NUMBER'].astype(str) + recall_to_release2['RELEASE_DATE'].astype(str)

#---------------------------------- deduplicate
recall_to_release2.sort_values(by=['MATCH','NEXT_LICENCE_REVOKE_DATE'],ascending = [False,True], inplace = True)
recall_to_release2.info()
recall_to_release2.head()

isp_releases_final = recall_to_release2.drop_duplicates(subset=['UNIQUEREF'], keep ='first')
isp_releases_final.shape #15476

isp_releases_final['MATCH'].value_counts(dropna=False)

isp_releases_final = isp_releases_final.drop(['REC_DOB','REC_SURNAME','REC_FILEREF','REC_PRISNUM'],axis=1)

# recall_to_release[recall_to_release['FILE_REFERENCE'].isin(['T4778','S7004'])]\
    #[['FILE_REFERENCE','PRISON_NUMBER','REC_FILEREF','REC_PRISNUM','RELEASE_DATE','LAST_LICENCE_REVOKE_DATE','LAST_RTC_DATE','MATCH']]

#sasReleases[sasReleases['FILE_REFERENCE'].isin(['T4778','S7004'])]\
    #[['FILE_REFERENCE','PRISON_NUMBER','RELEASE_DATE','LAST_LICENCE_REVOKE_DATE','LAST_RTC_DATE','NEXT_LICENCE_REVOKE_DATE']]

#recalls[recalls['FILE_REFERENCE'].isin(['T4778','S7004'])]\
 #   [['FILE_REFERENCE','PRISON_NUMBER','LICENCE_REVOKE_DATE','RTC_DATE']]

#---------------------------------- Create derived variables on releases dataset

isp_releases_final = isp_releases_final.copy()

isp_releases_final['LATEST_QUARTER'] = pd.Timestamp(year, quarter * 3 - 2, 1) - pd.Timedelta(days=1)

isp_releases_final['MONTHS_UNTIL_RECALL'] = (isp_releases_final['NEXT_LICENCE_REVOKE_DATE'] - isp_releases_final['RELEASE_DATE']) / np.timedelta64(1, 'M')
isp_releases_final['MONTHS_UNTIL_RECALL'] = isp_releases_final['MONTHS_UNTIL_RECALL'].apply(np.floor)
# isp_releases_final['MONTHS_UNTIL_RECALL'].value_counts(dropna=False).sort_index()

scope_rel_mask = isp_releases_final['RELEASE_DATE'] <= isp_releases_final['LATEST_QUARTER']
isp_releases_final['RECALLED_3_MONTHS'] = np.where(scope_rel_mask, 
                                                        np.where(isp_releases_final['MONTHS_UNTIL_RECALL'] < 3,100,0),
                                                    np.nan)

scope_rel_mask2 = isp_releases_final['RELEASE_DATE'] <= (isp_releases_final['LATEST_QUARTER'] - pd.DateOffset(months = 3))
isp_releases_final['RECALLED_6_MONTHS'] = np.where(scope_rel_mask2, 
                                                        np.where(isp_releases_final['MONTHS_UNTIL_RECALL'] < 6,100,0),
                                                    np.nan)

scope_rel_mask3 = isp_releases_final['RELEASE_DATE'] <= (isp_releases_final['LATEST_QUARTER'] - pd.DateOffset(months = 9))
isp_releases_final['RECALLED_12_MONTHS'] = np.where(scope_rel_mask3, 
                                                        np.where(isp_releases_final['MONTHS_UNTIL_RECALL'] < 12,100,0),
                                                    np.nan)

isp_releases_final['RELEASE_TYPE'] = np.where(isp_releases_final['LAST_RTC_DATE'].isna(),'First Release','Recall Re-release')

rel_type_mask = (isp_releases_final['RELEASE_DATE'] > isp_releases_final['FIRST_RELEASE_DATE']) & \
                (isp_releases_final['FIRST_RELEASE_DATE'] >= isp_releases_final['TARIFF_EXPIRY_DATE']) 

isp_releases_final['RELEASE_TYPE'] = np.where(rel_type_mask,'Recall Re-release',isp_releases_final['RELEASE_TYPE'])


rel_type_mask = (isp_releases_final['RELEASE_DATE'] > isp_releases_final['LAST_RELEASE_DATE']) & \
                (isp_releases_final['LAST_RELEASE_DATE'] >= isp_releases_final['TARIFF_EXPIRY_DATE']) 

isp_releases_final['RELEASE_TYPE'] = np.where(rel_type_mask,'Recall Re-release',isp_releases_final['RELEASE_TYPE'])

isp_releases_final['RELEASE_TYPE'] = np.where(isp_releases_final['RELEASE_DATE'].dt.year < 2013,'First Release',isp_releases_final['RELEASE_TYPE'])

served_mask = (isp_releases_final['RELEASE_TYPE'] == 'First Release') & (isp_releases_final['DOS'] < isp_releases_final['RELEASE_DATE'])

isp_releases_final['YEARS_SERVED']  = np.where(served_mask, 
                                               ((isp_releases_final['RELEASE_DATE'] - isp_releases_final['DOS']) / np.timedelta64(1, 'Y')).apply(np.floor),
                                               np.nan)

isp_releases_final['MONTHS_SERVED']  = np.where(served_mask, 
                                               ((isp_releases_final['RELEASE_DATE'] - isp_releases_final['DOS']) / np.timedelta64(1, 'M')).apply(np.floor),
                                               np.nan)

isp_releases_final.info() #15476
sasReleases.info() #15476


#---------------------------------- Some checks

sasReleases['RELEASE_TYPE'].value_counts(dropna=False)
isp_releases_final['RELEASE_TYPE'].value_counts(dropna=False)

sasFirsts = sasReleases[sasReleases['RELEASE_TYPE']=='First Release'][['FILE_REFERENCE','RELEASE_TYPE','RELEASE_DATE','DOS','MONTHS_SERVED']]
meFirsts = isp_releases_final[isp_releases_final['RELEASE_TYPE']=='First Release'][['FILE_REFERENCE','RELEASE_TYPE','RELEASE_DATE','DOS','MONTHS_SERVED']]

checkdf = meFirsts[~(meFirsts['FILE_REFERENCE'].isin(sasFirsts['FILE_REFERENCE']))]
checkdf.shape


isp_releases_final[isp_releases_final.FILE_REFERENCE.isin(checkdf.FILE_REFERENCE)][['FILE_REFERENCE','RELEASE_TYPE','RELEASE_DATE','FIRST_RELEASE_DATE','DOS','MONTHS_SERVED','LAST_RTC_DATE','TARIFF_EXPIRY_DATE','LAST_RELEASE_DATE']].sort_values(['FILE_REFERENCE','RELEASE_DATE'])

sasReleases[sasReleases['FILE_REFERENCE']=='103229'][['FILE_REFERENCE','RELEASE_TYPE','RELEASE_DATE','DOS','MONTHS_SERVED','LAST_RTC_DATE','TARIFF_EXPIRY_DATE','LAST_RELEASE_DATE']]


#---------------------------------- Temporary Save, delete later

isp_releases_final =isp_releases_final.drop(['MATCH','UNIQUEREF'],axis=1)

isp_releases_final.to_pickle(f"isp_releases_{year}q{quarter}_b.pkl")

