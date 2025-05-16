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

sys.path.append('/home/jovyan/OMPPG/Macro Library')
# from my_log import my_log
import Out_of_bounds_dates
import prepareMatch
importlib.reload(prepareMatch)
import openMatch
importlib.reload(openMatch)
import TimeDiffs
import tariff_groups
importlib.reload(tariff_groups)

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

# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #
        
#---------------------------------- globals are already set


#----------------------------------Import PPUD data
ispPPUD = pd.read_excel(f's3://alpha-omppg/isp-population/PPUD/{year}Q{quarter}/PPUD_ISP_{year}Q{quarter}.xls')
wlPPUD = pd.read_excel(f's3://alpha-omppg/isp-population/PPUD/{year}Q{quarter}/PPUD_WholeLife_{year}Q{quarter}.xls')

ispPPUD = ispPPUD.drop_duplicates()
wlPPUD = wlPPUD.drop_duplicates()

ispPPUD.info()
wlPPUD.info()

#----------------------------------Datetime columns appearing as object type - change
ispPPUD.select_dtypes(include=['object']).dtypes # find datetime column showing as an object column
dateColsToChange = ['LATEST_RELEASE_DATE']

check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(ispPPUD,col)],axis = 0,ignore_index=True)

check1= check1[dateColsToChange + [col for col in ispPPUD.columns if col not in dateColsToChange]]
check1
check1.shape # 0

    # Make two corrections to dates
for column in dateColsToChange:
    ispPPUD[column] = ispPPUD[column].astype(str).str.replace("8201-05-08 00:00:00", "2018-01-31 00:00:00") 
    ispPPUD[column] = ispPPUD[column].astype(str).str.replace("6201-07-09 00:00:00", "2011-06-09 00:00:00") 
    ispPPUD[column] = ispPPUD[column].astype(str).str.replace("2995-12-28 00:00:00", "") 
    ispPPUD[column] = ispPPUD[column].astype(str).str.replace("2922-01-07 00:00:00", "") 
    
   
    # Rerun check1 and see if if check1 is empty, then convert all datetime columns to datetime
    
check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(ispPPUD,col)],axis = 0,ignore_index=True)

check1= check1[dateColsToChange + [col for col in ispPPUD.columns if col not in dateColsToChange]]
check1.shape # 0

    # change certain columns to pandas datetime type

for column in dateColsToChange:
    ispPPUD[column] = pd.to_datetime(ispPPUD[column])

strip_blanks(ispPPUD)
strip_blanks(wlPPUD)

ispPPUD.info()
wlPPUD.info()

ispPPUD.select_dtypes(include=['datetime64']).dtypes
ispPPUD.dtypes.value_counts()
wlPPUD.info()
#---------------------------------- Add whole life flag to PPUD ISP data

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

ispPPUD_Matched = prepareMatch.prepareMatch(ispPPUD_Matched)

#---------------------------------- Match to A&O Dataset on either NOMIS number, Prison Number or Name and DOB

query3 = """SELECT DISTINCT a.*, 
                            b.DOS, b.TARIFF_EXPIRY_DATE, 
                            b.EXCLUDED_FROM_OPEN, 
                            b.WHOLE_LIFE, 
                            b.CUSTODY_TYPE_DESCRIPTION, 
                            b.STATUS_DESCRIPTION,
                            b.LATEST_RELEASE_DATE, 
                            b.FAMILY_NAME AS SURNAME_PPUD, 
                            b.DOB AS DOB_PPUD, 
                            b.INIT AS INIT_PPUD,
                            --b.DETERMINATE_FLAG,
                            b.PRISON_NUMBER, 
                            b.PN_TRIM, 
                            b.PN_START, 
                            b.PN_END,
                            b.INDEX_OFFENCE_DESCRIPTION,
                            b.CURRENT_ESTABLISHMENT_DESCRIPTION AS PPUD_PRISON, 
                            b.NOMS_ID AS NOMS_ID_PPUD, 
                            b.NOMS_TRIM, 
                            b.NOMS_START, 
                            b.NOMS_END,
                            b.PROBATION_SERVICE_DESCRIPTION
                            
                    FROM openMatched AS a LEFT JOIN ispPPUD_Matched AS b
                    
                    ON a.EXTRACTDATE >= b.DOS AND 
                      (a.NOMIS_ID = b.NOMS_ID OR
                       a.NOMIS_ID = b.NOMS_TRIM OR
                       a.NOMIS_ID = b.NOMS_START OR
                       a.NOMIS_ID = b.NOMS_END OR
                       a.NOMIS_ID = b.PRISON_NUMBER OR
                       a.NOMIS_ID = b.PN_TRIM OR
                       a.NOMIS_ID = b.PN_START OR
                       a.NOMIS_ID = b.PN_END)"""

ispTariffs = duckdb.sql(query3).df()
ispTariffs.shape # 22450, 21775, 21444,21084

# subset
sentence_cond = (
    (ispTariffs['SENTENCESTATUS'].isin(['(5) IPP','(6) Life'])) | 
    (~(ispTariffs['CUSTODY_TYPE_DESCRIPTION'].isna())) | 
    (~(ispTariffs['TARIFF_EXPIRY_DATE'].isna())) 
)
        
ispTariffs = ispTariffs[sentence_cond]

ispTariffs.shape # 11263, 11264, 11303,11323, 11351

ispTariffs['SENTENCESTATUS'].value_counts(dropna=False)

    # Rate quality of matches
    
def calculate_match(row):
    
    condition_a = pd.notna(row['NOMIS_ID']) and (
        row['NOMIS_ID'] in [row['NOMS_ID_PPUD'], row['NOMS_TRIM'], row['NOMS_START'], row['NOMS_END']]
    )
    
    condition_b = pd.notna(row['NOMIS_ID']) and (
        row['NOMIS_ID'] in [row['PRISON_NUMBER'], row['PN_START'], row['PN_END'], row['PN_TRIM']]
    )
    condition_c = (
        pd.notna(row['SURNAME']) and row['SURNAME'] == row['SURNAME_PPUD'] and
        pd.notna(row['DATEOFBIRTH']) and row['DATEOFBIRTH'] == row['DOB_PPUD'] and
        pd.notna(row['INITIAL']) and row['INITIAL'] == row['INIT_PPUD']
    )
    
    if condition_a and condition_c:
        return 4
    elif (condition_a or condition_b) and condition_c:
        return 3
    elif (condition_a or condition_b):
        return 2
    elif condition_c:
        return 1
    else:
        return 0

    # Create Match column by applying the function to each row
ispTariffs['MATCH'] = ispTariffs.apply(calculate_match, axis=1)

ispTariffs['EFFECTIVE_TED'] = ispTariffs.groupby('NOMIS_ID')['TARIFF_EXPIRY_DATE'].transform('max')

ispTariffs['CUS_PROPER'] = np.where(ispTariffs['CUSTODY_TYPE_DESCRIPTION'].isin(['IPP', 'DPP']),'(5) IPP','(6) Life')

ispTariffs['SENT_RANK'] = np.where(ispTariffs['SENTENCESTATUS'] == ispTariffs['CUS_PROPER'],1,2)

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


