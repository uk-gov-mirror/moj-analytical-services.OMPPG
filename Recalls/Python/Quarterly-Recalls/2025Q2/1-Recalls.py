""" 
GOAL: PRODUCE QUARTERLY RECALL DATA FOR OMSQ.
By Eric Nyame, 15/04/2024
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

#---------------------------------- Import own predefined functions, akin to macros in SAS

sys.path.append('/home/analyticalplatform/workspace/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
# import prepareMatch
# importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
import TimeDiffs

#----------------------------------Set display options

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.set_option('display.max_colwidth', None)

# function to remove trailing and leading blanks

def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #

        # Function to identify where bad datetime value is. Pass in the 

def dateOutOfBoundsColumn(dataset,value): # pass in the out-of-bounds date
    for col in dataset.columns:
        # Convert the column to string and check if any value contains the problematic date substring
        if dataset[col].astype(str).str.contains(value).any():
            hmm = dataset[col].astype(str).str.contains(value)
            cols_to_keep = ['NOMIS_ID','SURNAME','EXTRACTDATE',col]
            display(dataset[hmm][cols_to_keep])
            break

#dateOutOfBoundsColumn(pop,'9999-03-30')

# Function to show table in my preferred way
def show_data(data):
    show(data,
         scrollY="200px", 
         scrollCollapse=True, 
         paging=False,
         buttons=["excelHtml5"])


        # Period variables
quarter = 2 # 1:Jan-Mar, 2:Apr-Jun, 3:Jul-Sep, 4:Oct-Dec
year = 2025 # Enter the year being run in 4 digit format

extras = pd.read_excel(f's3://alpha-omppg/Recalls/PPUD/Extra Variables/PPUD_Recalls_{year}Q{quarter}_Extra.xlsx')
recalls = pd.read_excel(f's3://alpha-omppg/Recalls/PPUD/Audited/PPUD_Recalls_{year}Q{quarter}.xlsx')

extras = extras.replace("–","-",regex=True) # replace long dashes with normal dashes
recalls = recalls.replace("–","-",regex=True) # replace long dashes with normal dashes

# keep only cases with licence revocation date
recalls = recalls[~recalls['LICENCE_REVOKE_DATE'].isna()]

""" Note lengths of datasets

recalls.shape # 11042, 10106, 10407, 9975, 9782, 7417, 7157
extras.shape # 11167, 10214, 10522, 10123, 9906 (now contains rescinded to cover all), 9775, 7415, 7152
extras[extras['RESCIND_FLAG'] == False].shape # 11040, 10098, 9966

"""
# Check and remove cases with missing family name
recalls[recalls['FAMILY_NAME'].isna()] # 0

""" Check duplicate recalls
recalls[recalls.duplicated(['FILE_REFERENCE','LICENCE_REVOKE_DATE'], keep=False)] # none
extras[extras.duplicated(['FILE_REFERENCE','LICENCE_REVOKE_DATE'], keep=False)] # 0

recalls[recalls.duplicated(['FAMILY_NAME', 'DOB', 'LICENCE_REVOKE_DATE'], keep=False)] # 1
extras[extras.duplicated(['FAMILY_NAME', 'DOB', 'LICENCE_REVOKE_DATE'], keep=False)] # 1

"""
# remove index 7238 from recalls
#recalls = recalls[~recalls.index.isin([7238])]

# remove index 10454 from extras
#extras = extras[~extras.index.isin([10454])]

# remove blanks
strip_blanks(recalls)
strip_blanks(extras)

    # Convert columns that should be datetime to datetime
recalls.select_dtypes(include=['object']).dtypes
recalls.info()
dateColsToChange =['RTC_DATE'] # should contain datetime columns with dtype=object

        # Check bad dates
    
check1 = pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(recalls,col)],axis = 0)

check1= check1[dateColsToChange + [col for col in recalls.columns if col not in dateColsToChange]]
check1.shape # 7 cases to be dropped. Stopped recalls, not returned to custody
check1
check1.index
check1['FILE_REFERENCE'].values
    # Delete cancelled or decessased cases where there is no rtc date and the cancellation or death occured by the return-to-custody date. This requires manual chcking
    
# recalls = recalls[~recalls.index.isin([2022,3849,7580,9998])]
len(recalls) # 10102

    # Rerun check1 and see if if check1 is empty, then convert all datetime columns to datetime
check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(recalls,col)],axis = 0)

check1= check1[dateColsToChange + [col for col in recalls.columns if col not in dateColsToChange]] 
check1.shape # if zero, proceed

    # change the dtype of columns icertain columns to pandas datetime type

for column in dateColsToChange:
    recalls[column] = pd.to_datetime(recalls[column])

recalls.select_dtypes(include=['datetime64']).dtypes

""" Check 'test' cases and remove

recalls[recalls['FAMILY_NAME'].str.contains('Test|Lumen',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # none

recalls[recalls['FIRST_NAMES'].str.contains('Test|Lumen',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

recalls[recalls['PRISON_NUMBER'].str.contains('Test|Lumen',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES','PRISON_NUMBER']]

"""

Test_Case_Mask =  (   (recalls['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (recalls['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (recalls['FILE_REFERENCE'] != 'T18122')

"""
recalls[Test_Case_Mask][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 3 cases

"""

recalls = recalls[~Test_Case_Mask]
recalls.shape # 11041, 10102

"""Check 'case' or 'digit cases' 

recalls[recalls['FAMILY_NAME'].str.contains('Case|Lumen',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 3

recalls[recalls['FIRST_NAMES'].str.contains('Case|Lumen',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 1

    # Check 'digit' cases - these are normally good and shoulbe untouched
recalls[recalls['FAMILY_NAME'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 

recalls[recalls['FIRST_NAMES'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 

"""

#---------------------------------- Drop duplicates

# 5 Look for excess matches and non-Matches and make corrections
recalls['RESCIND_FLAG'].value_counts()
extras['RESCIND_FLAG'].value_counts()

# Key for joining
recalls['TEMP_LRD'] = recalls['LICENCE_REVOKE_DATE'].dt.normalize()
extras['TEMP_LRD'] = extras['LICENCE_REVOKE_DATE'].dt.normalize()

#correction

query = """SELECT a.*, 
                  b.DOS, 
                  b.NUMBER_OF_RECALL_REASONS,
                  b.RECALL_REASON_DESCRIPTIONS,
                  b.TARIFF_EXPIRY_DATE,
                  b.SED,
                  b.LICENCE_START,
                  b.PART_TOTAL_IN_DAYS,
                  b.FAMILY_NAME AS EXTRAS_FAMILY_NAME,
                  b.FIRST_NAMES AS EXTRAS_FIRST_NAME,
                  b.DOB AS EXTRAS_DOB,
                  b.FILE_REFERENCE AS FR,
                  b.PRISON_NUMBER AS PN,
                  b.STOPPED_REASON_DESCRIPTION,
                  b.RESCIND_FLAG AS RESCIND_FLAG_2
                  
           FROM recalls AS a LEFT JOIN extras AS b ON 
                ( (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                  (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) OR
                  (a.NOMS_ID = b.NOMS_ID AND a.NOMS_ID IS NOT NULL)
                ) AND 
                a.TEMP_LRD = b.TEMP_LRD """

recalls_pub = duckdb.sql(query).df()
recalls_pub.shape # 11042, 10103, 10407, 9975,9782, 7415 no dups

retain_vars =['FILE_REFERENCE','PRISON_NUMBER', 'FAMILY_NAME', 'FIRST_NAMES','DOB',
              'LICENCE_REVOKE_DATE', 'EXTRAS_FAMILY_NAME', 'EXTRAS_FIRST_NAME','EXTRAS_DOB',
              'RTC_DATE', 'RECALL_TYPE_DESCRIPTION', 'FR','PN']

    #check duplicates and remove
recalls_pub[recalls_pub.duplicated(['FILE_REFERENCE','LICENCE_REVOKE_DATE'], keep=False)] # 1

recalls_pub = recalls_pub[~recalls_pub.index.isin([4908])] # cancelled

    # Check Non-Matches and resolve, which would require you to match again
    # If the recalls no longer show up on PPUD, then delete
    
recalls_pub[recalls_pub['RECALL_REASON_DESCRIPTIONS'].isna()][['FILE_REFERENCE', 'PRISON_NUMBER', 'FAMILY_NAME', 'LICENCE_REVOKE_DATE', 'RTC_DATE', 'RECALL_TYPE_DESCRIPTION','EXTRAS_FAMILY_NAME','PN']] # none

    # Check recalls which were rescinded after return-to-custody date
    # Don't remove these as they were active at return-custody date
    
recalls_pub[recalls_pub['RESCIND_FLAG_2'] == True][['FILE_REFERENCE', 'STOPPED_REASON_DESCRIPTION','PRISON_NUMBER', 'FAMILY_NAME', 'LICENCE_REVOKE_DATE', 'RTC_DATE', 'RECALL_TYPE_DESCRIPTION','RESCIND_FLAG','UAL_FLAG']] # 2

len(recalls_pub) # 11041, 10100, 10401

    # Check UAL values
recalls_pub["UAL_FLAG"].value_counts(dropna=False)

# Deceased? Not UAL but have no RTC date -LEAVE IT AS IT IS
    
recalls_pub[(recalls_pub["RTC_DATE"].isna()) & (recalls_pub["UAL_FLAG"] != True)][['PRISON_NUMBER','LICENCE_REVOKE_DATE', 'RTC_DATE', 'UAL_FLAG', 'RECALL_TYPE_DESCRIPTION']] # 0

    # UAL but have RTC date?

recalls_pub[~(recalls_pub["RTC_DATE"].isna()) & (recalls_pub["UAL_FLAG"] == True)][['PRISON_NUMBER','LICENCE_REVOKE_DATE', 'RTC_DATE', 'UAL_FLAG', 'RECALL_TYPE_DESCRIPTION']] # none

# Improper probation area
recalls_pub[recalls_pub['PROBATION_AREA_DESCRIPTION'].isin(['Scotland','Not Applicable','Northern Ireland','Channel Islands'])] #0
  
    # Rename column

recalls_pub.rename(columns = {'CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION':'CUSTODY_TYPE_AT_RECALL'}, inplace = True)

    # Replace Not Applicable and Not Specified custody types
recalls_pub['CUSTODY_TYPE_AT_RECALL'].value_counts(dropna=False)

recalls_pub.loc[recalls_pub['CUSTODY_TYPE_AT_RECALL'].isin(['Not Applicable','Not Specified']), 'CUSTODY_TYPE_AT_RECALL'] = recalls_pub['CUSTODY_TYPE_DESCRIPTION']

# drop some variables
recalls_pub = recalls_pub.drop(columns=['EXTRAS_FAMILY_NAME','EXTRAS_FIRST_NAME','FR','PN','RESCIND_FLAG_2','STOPPED_REASON_DESCRIPTION','TEMP_LRD'])

    # Import Look up tables

CustodyRef = pd.read_excel('s3://alpha-omppg/Recalls/Reference Data/Recalls Lookup.xls',sheet_name='CustodyType')
AreaRef = pd.read_excel('s3://alpha-omppg/Recalls/Reference Data/Recalls Lookup.xls',sheet_name='PS')
RecallRef = pd.read_excel('s3://alpha-omppg/Recalls/Reference Data/Recalls Lookup.xls',sheet_name='RecallType')

CustodyRef.columns = CustodyRef.columns.str.upper() 
AreaRef.columns = AreaRef.columns.str.upper()
RecallRef.columns = RecallRef.columns.str.upper()

CustodyRef = CustodyRef.replace("–","-",regex=True) # replace long dashes with normal dashes
AreaRef = AreaRef.replace("–","-",regex=True) # replace long dashes with normal dashes
RecallRef = RecallRef.replace("–","-",regex=True) # replace long dashes with normal dashes

strip_blanks(CustodyRef)
strip_blanks(AreaRef)
strip_blanks(RecallRef)

# KEY********************Check non-Matches and upadate reference files and run again**************/

query2 = """SELECT a.PRISON_NUMBER, 
                a.CUSTODY_TYPE_AT_RECALL, 
                b.CUSTODYTYPE, 
                b.CUSTODYTYPE2,
                a.PROBATION_AREA_DESCRIPTION, 
                a.NOMS_REGION_DESCRIPTION, 
                c.PROB_AREA, 
                c.SUP_BODY, 
                c.NPS_CRC_NAME, 
                c.NPS_Division,
                a.RECALL_TYPE_DESCRIPTION, 
                d.TARGETTYPE, 
                d.SENTENCETYPE
          FROM recalls_pub as a 
          LEFT JOIN CustodyRef as b ON a.CUSTODY_TYPE_AT_RECALL = b.CUSTODY_TYPE_AT_RECALL
          LEFT JOIN AreaRef as c ON a.PROBATION_AREA_DESCRIPTION = c.PROBATION_AREA_DESCRIPTION
          LEFT JOIN RecallRef as d ON a.RECALL_TYPE_DESCRIPTION = d.RECALL_TYPE_DESCRIPTION
          WHERE 
            (c.PROB_AREA IS NULL OR
             c.SUP_BODY IS NULL OR
             d.TARGETTYPE IS NULL OR
             b.CUSTODYTYPE IS NULL OR
             b.CUSTODYTYPE2 IS NULL OR
             d.SENTENCETYPE IS NULL)
            AND a.PROBATION_AREA_DESCRIPTION NOT IN ('Scotland','Not Applicable','Northern Ireland','Channel Islands')
            AND a.RECALL_TYPE_DESCRIPTION != 'Not Applicable'
            AND a.CUSTODY_TYPE_AT_RECALL != 'Not Applicable'"""

recalls_unmatched_codes = duckdb.sql(query2).df()
recalls_unmatched_codes.shape # 0 make correction if not empty
#recalls_unmatched_codes['RECALL_TYPE_DESCRIPTION'].value_counts(dropna=False)
# recalls_unmatched_codes['RECALL_TYPE_DESCRIPTION'].unique()

# Add information from reference lists to Recalls dataset

query3 = """ SELECT a.*,
                b.CUSTODYTYPE, 
                b.CUSTODYTYPE2,
                c.PROB_AREA, 
                c.SUP_BODY, 
                c.NPS_CRC_NAME, 
                c.NPS_Division,
                d.TARGETTYPE, 
                d.SENTENCETYPE
            FROM recalls_pub as a 
            LEFT JOIN CustodyRef as b ON a.CUSTODY_TYPE_AT_RECALL = b.CUSTODY_TYPE_AT_RECALL
            LEFT JOIN AreaRef as c ON a.PROBATION_AREA_DESCRIPTION = c.PROBATION_AREA_DESCRIPTION
            LEFT JOIN RecallRef as d ON a.RECALL_TYPE_DESCRIPTION = d.RECALL_TYPE_DESCRIPTION
            WHERE 
                (a.PROBATION_AREA_DESCRIPTION NOT IN ('Scotland','Not Applicable','Northern Ireland','Channel Islands')) """
  
recalls_matched = duckdb.sql(query3).df()
recalls_matched.shape # 11041, 10101, 10401, 9975, 9782,7415

recalls_matched.head()

# ------------------------------ Additional variables once matches have been done

recalls_final = recalls_matched.copy()

recalls_final["RETURN_BY"] = np.where(
    quarter == 4, pd.Timestamp(year+1,3,31), 
    np.where(quarter == 3, pd.Timestamp(year,12,31),
    np.where(quarter == 2, pd.Timestamp(year,9,30), pd.Timestamp(year,6,30)))).item()

recalls_final.head()

    # Create target flags
recalls_final['DIFF'] = np.where(
    ~recalls_final['RTC_DATE'].isna() & ~recalls_final['PB_DECISION_AFTER_BREACH_ACTUAL'].isna(),
    (recalls_final['RTC_DATE'] - recalls_final['PB_DECISION_AFTER_BREACH_ACTUAL']).dt.total_seconds(),
    np.nan)

recalls_final['PINTARGET'] = np.where(
    ~recalls_final['REPORT_RECD_BY_UNIT_ACTUAL'].isna() & 
    ~recalls_final['REPORT_RECD_BY_UNIT_TARGET'].isna() & 
    (recalls_final['REPORT_RECD_BY_UNIT_ACTUAL'] <= recalls_final['REPORT_RECD_BY_UNIT_TARGET']),
    1, np.nan)

recalls_final['PPUINTARGET'] = np.where(
    ~recalls_final['LICENCE_REVOKE_DATE'].isna() & 
    ~recalls_final['ISSUE_REVOCATION_TARGET'].isna() & 
    (recalls_final['LICENCE_REVOKE_DATE'] <= recalls_final['ISSUE_REVOCATION_TARGET']),
    1, np.nan)

recalls_final['POLICEINTARGET'] = np.where(
    ~recalls_final['RTC_DATE'].isna() & 
    ~recalls_final['RTC_TARGET'].isna() & 
    (recalls_final['RTC_DATE'] <= recalls_final['RTC_TARGET']),
    1, np.nan)

recalls_final['STANDARDTARGET'] = np.where(
    ~recalls_final['DIFF'].isna() & (recalls_final['DIFF'] < 144*60*60) & (recalls_final['TARGETTYPE'] == 'standard'),
    1, np.nan)

recalls_final['EMERGENCYTARGET'] = np.where(
    ~recalls_final['DIFF'].isna() & (recalls_final['DIFF'] < 74*60*60) & (recalls_final['TARGETTYPE'] == 'emergency'),
    1, np.nan)

    # Define a helper function for RECALL_STATUS
    
def determine_recall_status(row):
    if row['TARGETTYPE'] == 'standard':
        if row['UAL_FLAG'] == False and (pd.isna(row['RTC_DATE']) or pd.isna(row['DIFF'])):
            return 'Standard - Missing data'
        elif row['UAL_FLAG'] == True or (row['LICENCE_REVOKE_DATE'].year < 2015 and row['RTC_DATE'] > row['RETURN_BY']):
            return 'Standard - Not returned'
        elif row['DIFF'] < 144*60*60:
            return 'Standard - Less than 144 hours'
        elif row['DIFF'] >= 144*60*60:
            return 'Standard - 144 hours to 3 months'
    elif row['TARGETTYPE'] == 'emergency':
        if row['UAL_FLAG'] == False and (pd.isna(row['RTC_DATE']) or pd.isna(row['DIFF'])):
            return 'Emergency - Missing data'
        elif row['UAL_FLAG'] == True or (row['LICENCE_REVOKE_DATE'].year < 2015 and row['RTC_DATE'] > row['RETURN_BY']):
            return 'Emergency - Not returned'
        elif row['DIFF'] < 74*60*60:
            return 'Emergency - Less than 74 hours'
        elif row['DIFF'] >= 74*60*60:
            return 'Emergency - 74 hours to 3 months'
    return np.nan

recalls_final['RECALL_STATUS'] = recalls_final.apply(determine_recall_status, axis=1)

# Additional attributes adjustments

# Recalculation of recall process and length based on conditions
recalls_final['RECALL_LENGTH'] = np.where(
    recalls_final['RECALL_TYPE_DESCRIPTION'].astype(str).str.contains("fix|ftr", case=False, na=False),
    "Fixed Term",
    "Standard"
)

"""
recalls_final.pivot_table(index=['RECALL_TYPE_DESCRIPTION','RECALL_LENGTH'],aggfunc='size')

recalls_final[recalls_final['RECALL_TYPE_DESCRIPTION'].isin(['HDC recall - 255 1 (a) breach of curfew conditions','HDC recall - 255 1 (b) inability to monitor'])][['PRISON_NUMBER','RECALL_TYPE_DESCRIPTION','PART_TOTAL_IN_DAYS']]
"""

recalls_final['RECALL_PROCESS'] = np.where(
    recalls_final['RECALL_STATUS'].astype(str).str.contains("Emergency", case=False, na=False),
    "Emergency",
    np.where(recalls_final['RECALL_STATUS'].astype(str).str.contains("Standard", case=False, na=False), "Standard", '')
)

recalls_final['RECALL_PROCESS'] = np.where(recalls_final['CUSTODYTYPE2'] == 'b. indeterminate', 'Emergency', recalls_final['RECALL_PROCESS'])
recalls_final['RECALL_LENGTH'] = np.where(recalls_final['CUSTODYTYPE2'] == 'b. indeterminate', 'Standard', recalls_final['RECALL_LENGTH'])
recalls_final['SENTENCETYPE'] = np.where(recalls_final['CUSTODYTYPE2'] == 'b. indeterminate', 'Other', recalls_final['SENTENCETYPE'])
recalls_final['RECALL_LENGTH'] = np.where(recalls_final['RECALL_PROCESS'] == 'Emergency', 'Standard', recalls_final['RECALL_LENGTH'])
recalls_final['SENTENCETYPE'] = np.where(recalls_final['LICENCE_REVOKE_DATE'] < pd.Timestamp("2015-02-01"), 'Other', recalls_final['SENTENCETYPE'])

    # Returns In or Out of Target
conditions_target = [
    recalls_final['RECALL_STATUS'].isin(['Standard - Less than 144 hours', 'Emergency - Less than 74 hours']),
    recalls_final['RECALL_STATUS'].isin(['Standard - 144 hours to 3 months', 'Emergency - 74 hours to 3 months']),
    recalls_final['RECALL_STATUS'].isin(['Standard - Not returned', 'Emergency - Not returned'])
]
choices_target = ['a. Returned in target', 'b. Returned outside target', 'c. Not returned']

recalls_final['RECALL_TARGET'] = np.select(conditions_target, choices_target, default='d. Resolved')

recalls_final[recalls_final['RECALL_TARGET'] == 'd. Resolved']

    # Facing Further Charge
recalls_final['FURTHER_CHARGE'] = np.where(
    recalls_final['RECALL_REASON_DESCRIPTIONS'].astype(str).str.contains("Further", case =False, na=False),100,0
)

    # Old Probation Trust
recalls_final['SUP_BODY'] = np.where(
    recalls_final['LICENCE_REVOKE_DATE'] < pd.Timestamp('2014-06-01'),'a. PT', recalls_final['SUP_BODY']
)

# Gender
recalls_final['GENDER'].value_counts(dropna=False)

conditions_gender = [
    recalls_final['GENDER'] == 'F ( Was M )',
    recalls_final['GENDER'] == 'M ( Was F )'
]
choices_gender = ['F', 'M']
recalls_final['GENDER'] = np.select(conditions_gender, choices_gender, default=recalls_final['GENDER'])

# Drop specified columns
recalls_final = recalls_final.drop(columns=['RESCIND_FLAG', 'MAPPA_LEVEL_DESCRIPTION', 'POLICE_FORCE_DESCRIPTION', 'EWS_NUMBER'])

recalls_final.head()

# Save on Amazon to continue

recalls_final.to_parquet(f"s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_{year}q{quarter}.parquet",index=False)
