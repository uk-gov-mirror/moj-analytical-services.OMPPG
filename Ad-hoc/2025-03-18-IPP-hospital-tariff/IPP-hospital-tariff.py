""" 
GOAL: How many of those beyond the 10-year tariff are in secure mental hospitals?  
By Eric Nyame, 18/03/2025
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
import Out_of_bounds_dates
import prepareMatch
#importlib.reload(prepareMatch)
# import openMatch
#importlib.reload(openMatch)
import TimeDiffs
# import tariff_groups
#importlib.reload(tariff_groups)

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


year = 2023

pop = pd.read_parquet(f"s3://alpha-omppg/Mental-Health/2023/output/population_prepared_{year}.parquet")

pop.head()

pop['STATUS'].value_counts(dropna=False)
pop['DA_CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

ipps = pop[pop['DA_CUSTODY_TYPE_DESCRIPTION'].isin(['IPP','DPP'])]
ipps['STATUS'].value_counts(dropna=False)
ipps = ipps[ipps['STATUS']== 'aHospital']
len(ipps) # 241

ipps.head()
#----------------------------------Import PPUD data

month = str(12).zfill(2) # pads the number with a leading zero
day = 31
year = 2023
quarter = 4

ispPPUD = pd.read_excel(f's3://alpha-omppg/isp-population/PPUD/{year}Q{quarter}/PPUD_ISP_{year}Q{quarter}.xls')

ispPPUD = ispPPUD.drop_duplicates()

ispPPUD.info()

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

ispPPUD.select_dtypes(include=['datetime64']).dtypes

#---------------------------------- Match to 
# duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query = """SELECT DISTINCT a.*, 
                            b.TARIFF_EXPIRY_DATE, 
                            b.DOS,
                            b.LATEST_RELEASE_DATE,
                            b.NOMS_ID AS NOMS_ID_B,
                            b.FILE_REFERENCE AS FILE_REFERENCE_B,
                            b.PRISON_NUMBER AS PRISON_NUMBER_B,
                            b.CUSTODY_TYPE_DESCRIPTION
                                                        
                    FROM ipps AS a LEFT JOIN ispPPUD AS b
                    
                    ON  
                      ( 
                       (a.NOMS_ID = b.NOMS_ID AND a.NOMS_ID IS NOT NULL) OR
                       (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                       (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL)
                      )"""
ippTariffs = duckdb.sql(query).df()
ippTariffs.shape # 248

ippTariffs.head()

    # Rate quality of matches
    
def calculate_match(row):
    
    condition_a = (row['NOMS_ID'] == row['NOMS_ID_B']) & (pd.notna(row['NOMS_ID']))
    condition_b = (row['FILE_REFERENCE'] == row['FILE_REFERENCE_B']) & (pd.notna(row['FILE_REFERENCE']))
    condition_c = (row['PRISON_NUMBER'] == row['PRISON_NUMBER_B']) & (pd.notna(row['PRISON_NUMBER']))
    
    if condition_a:
        return 2
    elif condition_b | condition_c:
        return 1
    else:
        return 0

    # Create Match column by applying the function to each row
ippTariffs['MATCH'] = ippTariffs.apply(calculate_match, axis=1)


ippTariffs = ippTariffs.sort_values(by=['FILE_REFERENCE','MATCH','TARIFF_EXPIRY_DATE'],ascending = [True,False,False])

ippTariffs[ippTariffs.duplicated('FILE_REFERENCE',keep=False)]
isPTNodup = ippTariffs.drop_duplicates(subset='FILE_REFERENCE', keep ='first').copy()

isPTNodup.shape # 240

#---------------------------------- Create final derived variables
    # tariff past

notIPP = isPTNodup['TARIFF_EXPIRY_DATE'].dt.year < 2005
sum(notIPP) # 2

isPTNodup[notIPP]

isPTNodup.loc[notIPP,'TARIFF_EXPIRY_DATE'] = np.nan

tpast1 = (isPTNodup['TARIFF_EXPIRY_DATE'].isna()) | (isPTNodup['TARIFF_EXPIRY_DATE'] == pd.Timestamp(1900,1,1))
tpast3 = isPTNodup['TARIFF_EXPIRY_DATE'] <= pd.Timestamp(2023,12,31)

isPTNodup.loc[tpast1,'TARIFF_PAST'] = 'n/a'
isPTNodup.loc[~(tpast1) & (tpast3),'TARIFF_PAST'] = 'Y'

isPTNodup['TARIFF_PAST'].value_counts(dropna=False)

    # Tariff length in years and months

tmth = isPTNodup['TARIFF_EXPIRY_DATE'] >= isPTNodup['DOS']
tmth2 = (isPTNodup['TARIFF_EXPIRY_DATE'].dt.year == 1900) | (isPTNodup['TARIFF_EXPIRY_DATE'].dt.year == pd.Timestamp.max.year)

isPTNodup['TARIFF_MONTHS'] = np.where(tmth,
                                        isPTNodup.apply(lambda x: TimeDiffs.month_diff(x['DOS'],x['TARIFF_EXPIRY_DATE']),axis=1),
                                        np.nan)
                        
isPTNodup.loc[tmth2,'TARIFF_MONTHS'] = np.nan

isPTNodup['TARIFF_YEARS'] = isPTNodup['TARIFF_MONTHS'] // 12

      # Number of years and months spent in prison post tariff

isPTNodup['OVERTARIFF_MONTHS'] = np.where(isPTNodup['TARIFF_PAST'] == 'Y',
                                        isPTNodup.apply(lambda x: TimeDiffs.month_diff(x['TARIFF_EXPIRY_DATE'],pd.Timestamp(2023,12,31)),axis=1),
                                        np.nan)

isPTNodup['OVERTARIFF_YEARS'] = isPTNodup['OVERTARIFF_MONTHS'] // 12


isPTNodup['OVERTARIFF_YEARS'].value_counts(dropna=False)

isPTNodup['LATEST_RELEASE_DATE'].max()

released = (isPTNodup['LATEST_RELEASE_DATE'] > isPTNodup['DOS']) & (isPTNodup['DOS'].dt.year >= 2005)
sum(released) # 35

isPTNodup.head()

isPTNodup['OVERTARIFF_YEARS'].value_counts(dropna=False).sort_index()
isPTNodup[~released]['OVERTARIFF_YEARS'].value_counts(dropna=False).sort_index()


     