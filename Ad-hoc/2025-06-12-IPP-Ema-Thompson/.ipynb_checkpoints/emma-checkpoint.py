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

ippRecalls =  ippRecalls.copy()
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

#---------------------------------- Drop duplicates

# 5 Look for excess matches and non-Matches and make corrections
ippRecalls['RESCIND_FLAG'].value_counts()

# Key for joining
ippRecalls['TEMP_LRD'] = ippRecalls['LICENCE_REVOKE_DATE'].dt.normalize()
extras['TEMP_LRD'] = extras['LICENCE_REVOKE_DATE'].dt.normalize()

#correction

query = """SELECT a.*, 
                  b.DOS, 
                  b.NUMBER_OF_RECALL_REASONS,
                  b.RECALL_REASON_DESCRIPTIONS,
                  b.TARIFF_EXPIRY_DATE,
                  b.FAMILY_NAME AS EXTRAS_FAMILY_NAME,
                  b.FIRST_NAMES AS EXTRAS_FIRST_NAME,
                  b.DOB AS EXTRAS_DOB,b.FILE_REFERENCE AS FR,
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
recalls_pub.shape # 10407, 9975,9782, 7415 no dups

retain_vars =['FILE_REFERENCE','PRISON_NUMBER', 'FAMILY_NAME', 'FIRST_NAMES','DOB',
              'LICENCE_REVOKE_DATE', 'EXTRAS_FAMILY_NAME', 'EXTRAS_FIRST_NAME','EXTRAS_DOB',
              'RTC_DATE', 'RECALL_TYPE_DESCRIPTION', 'FR','PN']

recalls_pub[recalls_pub.duplicated(['FILE_REFERENCE','LICENCE_REVOKE_DATE'], keep=False)] # 0#---------------------------------- Add whole life flag to PPUD ISP data

# duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query2 = """SELECT a.*, 
                  b.WHOLE_LIFE 
                  
            FROM ispPPUD AS a 
            LEFT JOIN (SELECT DISTINCT PRISON_NUMBER, WHOLE_LIFE, DOS FROM wlPPUD) AS b
            
            ON  a.PRISON_NUMBER = b.PRISON_NUMBER AND
            a.DOS = b.DOS"""

ispPPUD_Matched = duckdb.sql(query2).df()
ispPPUD_Matched.shape # 25326, 25222, 25147, 25052

ispPPUD_Matched['WHOLE_LIFE'].value_counts(dropna=False)

ispPPUD_Matched.loc[ispPPUD_Matched['WHOLE_LIFE'] == True,'TARIFF_EXPIRY_DATE'] = pd.Timestamp.max.normalize()

ispPPUD_Matched[ispPPUD_Matched['WHOLE_LIFE'] == True]['TARIFF_EXPIRY_DATE'].head()

ippippRecalls = prepareMatch.prepareMatch(ippippRecalls)

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
matched1.shape # 111

ispTariffs = ispTariffs.sort_values(by=['NOMIS_ID','MATCH','SENT_RANK','CUS_PROPER','TARIFF_EXPIRY_DATE','DOS','LATEST_RELEASE_DATE'],ascending = [True,False,True,False,False,True,False])

ispTNodup = ispTariffs.drop_duplicates(subset='NOMIS_ID', keep ='first').copy()

ispTNodup.shape # 10899, 10902, 10939,10961, 10995

#----------------------------------Add detailed offence groups

ispTNodup['OFFENCE_UPPER'] = ispTNodup['OFFENCE'].str.upper()
ispTNodup = ispTNodup.drop(['CUS_PROPER','SENT_RANK'], axis = 1)

offLookup = pd.read_excel("s3://alpha-omppg/isp-population/Reference/ISP Lookup.xls",sheet_name='Offences')
offLookup.columns = offLookup.columns.str.upper()
strip_blanks(offLookup)
offLookup = offLookup.drop_duplicates(subset='OFFENCE_UPPER', keep ='first')
offLookup.info()

query4 = """SELECT a.*, 
                  b.DETAILED_OFFENCE_GROUP 
                  
            FROM ispTNodup AS a LEFT JOIN offLookup AS b
            
            ON  a.OFFENCE_UPPER = b.OFFENCE_UPPER """

ispTOffences = duckdb.sql(query4).df()

ispTOffences.shape

    # drop some columns
    
ispTOffences = ispTOffences.drop(['MATCH','SURNAME_PPUD', 'DOB_PPUD', 'INIT_PPUD','PN_TRIM', 'PN_START', 'PN_END', 'NOMS_ID_PPUD', 'NOMS_TRIM', 'NOMS_START', 'NOMS_END', 'OFFENCE_UPPER'],axis = 1)

#---------------------------------- Create final derived variables
    # tariff past
    
notIPP = (ispTOffences['SENTENCESTATUS'] == '(5) IPP') & (ispTOffences['TARIFF_EXPIRY_DATE'].dt.year < 2005)

ispTOffences.loc[notIPP,'TARIFF_EXPIRY_DATE'] = pd.NaT

tpast1 = (ispTOffences['TARIFF_EXPIRY_DATE'].isna()) | (ispTOffences['TARIFF_EXPIRY_DATE'] == pd.Timestamp(1900,1,1))
tpast2 = (ispTOffences['WHOLE_LIFE'] == True) | (ispTOffences['TARIFF_EXPIRY_DATE'] >= ispTOffences['EXTRACTDATE'])
tpast3 = ispTOffences['TARIFF_EXPIRY_DATE'] < ispTOffences['EXTRACTDATE']

ispTOffences.loc[tpast1,'TARIFF_PAST'] = 'n/a'
ispTOffences.loc[~(tpast1) & (tpast2),'TARIFF_PAST'] = 'N'
ispTOffences.loc[~(tpast1) & ~(tpast2) & (tpast3),'TARIFF_PAST'] = 'Y'

ispTOffences.loc[ispTOffences['SENTENCESTATUS'] == '(7) Recall','TARIFF_PAST'] = 'Y'

ispTOffences['TARIFF_PAST'].value_counts(dropna=False)

    # Tariff length in years and months

tmth = ispTOffences['TARIFF_EXPIRY_DATE'] >= ispTOffences['DOS']
tmth2 = (ispTOffences['TARIFF_EXPIRY_DATE'].dt.year == 1900) | (ispTOffences['TARIFF_EXPIRY_DATE'].dt.year == pd.Timestamp.max.year)

ispTOffences['TARIFF_MONTHS'] = np.where(tmth,
                                        ispTOffences.apply(lambda x: TimeDiffs.month_diff(x['DOS'],x['TARIFF_EXPIRY_DATE']),axis=1),
                                        np.nan)
                        
ispTOffences.loc[tmth2,'TARIFF_MONTHS'] = np.nan

ispTOffences['TARIFF_YEARS'] = ispTOffences['TARIFF_MONTHS'] // 12

    # Years and months in prison

ispTOffences['SERVED_MONTHS'] = ispTOffences.apply(lambda x: TimeDiffs.month_diff(x['DOS'],x['EXTRACTDATE']),axis=1)

ispTOffences['SERVED_YEARS'] = ispTOffences['SERVED_MONTHS'] // 12

    # Number of tariffs spent in prison

ispTOffences['TARIFFS_SERVED'] = np.where((ispTOffences['TARIFF_MONTHS'].isna()) | (ispTOffences['TARIFF_EXPIRY_DATE'] == ispTOffences['DOS']),
                                         np.nan,
                                         (ispTOffences['EXTRACTDATE'] -ispTOffences['DOS'])//(ispTOffences['TARIFF_EXPIRY_DATE'] -ispTOffences['DOS']))

     # Number of years and months spent in prison post tariff

ispTOffences['OVERTARIFF_MONTHS'] = np.where(ispTOffences['TARIFF_PAST'] == 'Y',
                                        ispTOffences.apply(lambda x: TimeDiffs.month_diff(x['TARIFF_EXPIRY_DATE'],x['EXTRACTDATE']),axis=1),
                                        np.nan)

ispTOffences['OVERTARIFF_YEARS'] = ispTOffences['OVERTARIFF_MONTHS'] // 12

    # Age at time of sentence

ispTOffences['SENTENCED_AGE'] = np.where(ispTOffences['DOS'] > ispTOffences['DATEOFBIRTH'],
                                         ispTOffences.apply(lambda x: TimeDiffs.year_diff(x['DATEOFBIRTH'],x['DOS']),axis=1),
                                        np.nan)

  # Hitting tariff in next quarter
next_day = pd.Timestamp(year,3,day)+ np.timedelta64(1,'D')
next_day
next_day_year = next_day.year
next_day_quarter = next_day.quarter

ted_in_quart_cond = ((ispTOffences['TARIFF_EXPIRY_DATE'].dt.quarter == next_day_quarter) & (ispTOffences['TARIFF_EXPIRY_DATE'].dt.year == next_day_year))

ispTOffences['TARIFF_IN_QUARTER'] = pd.NaT 

ispTOffences.loc[ted_in_quart_cond, 'TARIFF_IN_QUARTER'] = ispTOffences['TARIFF_EXPIRY_DATE']

    # Tariff length - publication categories

ispTOffences2 = tariff_groups.tariff_groups(ispTOffences)

ispTOffences2.head()
ispTOffences2['TARIFF'].value_counts(dropna=False)

    # Invalid Latest Release Date

ispTOffences2.loc[ispTOffences2['LATEST_RELEASE_DATE'] < ispTOffences2['TARIFF_EXPIRY_DATE'], 'LATEST_RELEASE_DATE'] = pd.NaT

ispTOffences2.info()

#---------------------------------- Temporary Save, delete later
# ispTOffences2.to_parquet("ispTariffsFinal.parquet")


