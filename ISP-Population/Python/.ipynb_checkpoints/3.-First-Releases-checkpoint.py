""" 
GOAL: ADD FIRST RELEASE INFORMATION FOR QUARTERLY ISP POP FOR OMSQ
By Eric Nyame, 05/02/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
# print(duckdb.__version__)
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
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x) #
        
#----------------------------------Set globals

yy = 23 # year as yy
mm = 12
dd = 31

year = 2023
quarter = 4 

#---------------------------------- Load ISP release and tariff data

# isp_releases_2023q4 =  pd.read_pickle("~/OMPPG/Recalls/Python/ISP Releases and Recalls/2023 Q4/isp_releases_2023q4.pkl")
isp_releases_2023q4 =  pd.read_parquet("~/OMPPG/Recalls/Python/ISP Releases and Recalls/2023 Q4/isp_releases_2023q4.parquet")

firstRel = isp_releases_2023q4[isp_releases_2023q4['RELEASE_TYPE']=='First Release']

ispTariffsFinal = pd.read_parquet("ispTariffsFinal.parquet")

# ispTariffsFinal.info()

firstRel.shape


{col: firstRel[col].max() for col in firstRel.columns if pd.api.types.is_datetime64_any_dtype(firstRel[col])}

check12 = ispTOffences2.drop(['TARIFF_EXPIRY_DATE','EFFECTIVE_TED'])
#ispPPUD = pd.read_excel(f's3://alpha-omppg/ISP Population/PPUD/{year}Q{quarter}/PPUD_ISP_{year}Q{quarter}.xls')
#wlPPUD = pd.read_excel(f's3://alpha-omppg/ISP Population/PPUD/{year}Q{quarter}/PPUD_WholeLife_{year}Q{quarter}.xls')


#----------------------------------Match to ISP Population Dataset on either NOMIS number, Prison Number or Name and DOB

duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query = """SELECT DISTINCT a.*, 
                        b.RELEASE_DATE AS FIRST_RELEASE_DATE, 
                        b.RELEASE_CONDITIONS AS FIRST_RELEASE_CONDITIONS,
                        b.FAMILY_NAME AS SURNAME_PPUD, 
                        b.DOB AS DOB_PPUD, 
                        b.INIT AS INIT_PPUD,
                        b.PRISON_NUMBER AS PN2, 
                        b.PN_TRIM, 
                        b.PN_START, 
                        b.PN_END, 
                        b.NOMS_ID AS NOMS_ID_PPUD, 
                        b.NOMS_TRIM, 
                        b.NOMS_START, 
                        b.NOMS_END
                        
            FROM ispTariffsFinal AS a LEFT JOIN firstRel AS b ON
                        (a.EXTRACTDATE >= b.DOS OR b.DOS IS NULL) AND
                        a.EXTRACTDATE > b.RELEASE_DATE AND
                        (a.TARIFF_EXPIRY_DATE <= b.RELEASE_DATE OR a.TARIFF_EXPIRY_DATE IS NULL) AND
                        a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL"""

ispRelMatched = duckdb.sql(query).df()
ispRelMatched.shape

#---------------------------------- Rate quality of the match
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
ispRelMatched['MATCH'] =ispRelMatched.apply(calculate_match, axis=1)

    # deduplicate
ispRelMatched = ispRelMatched.sort_values(by=['MATCH','FIRST_RELEASE_DATE'],ascending = [False,True])

ispFirstRel =ispRelMatched.drop_duplicates(subset='NOMIS_ID', keep ='first').copy()
ispFirstRel.shape

#---------------------------------- *Create final derived variables

    # Time served before first release
ispFirstRel['MONTHS_BEFORE_RELEASE'] = np.nan
ispFirstRel['YEARS_BEFORE_RELEASE'] = np.nan

non_miss_rel_dos = (~ispFirstRel['FIRST_RELEASE_DATE'].isna()) & (~ispFirstRel['DOS'].isna()) # first release and dos not missing

ispFirstRel.loc[non_miss_rel_dos,'MONTHS_BEFORE_RELEASE'] = ispFirstRel.apply(lambda x: TimeDiffs.month_diff(x['DOS'],x['FIRST_RELEASE_DATE']),axis=1)
ispFirstRel.loc[non_miss_rel_dos,'YEARS_BEFORE_RELEASE'] = ispFirstRel.apply(lambda x: TimeDiffs.year_diff(x['DOS'],x['FIRST_RELEASE_DATE']),axis=1)

ispFirstRel = ispFirstRel.drop(['MATCH', 'SURNAME_PPUD', 'DOB_PPUD', 'INIT_PPUD', 'PN2', 'PN_TRIM','PN_START', 
                                        'PN_END', 'NOMS_ID_PPUD', 'NOMS_TRIM', 'NOMS_START', 'NOMS_END'],axis=1)

ispFirstRel.shape

#---------------------------------- Save
ispFirstRel.to_parquet("ispFirstRel.parquet")
