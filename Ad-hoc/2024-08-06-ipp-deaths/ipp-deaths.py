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
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x) #
        


#----------------------------------Import PPUD data
year = 2024
quarter = 2
recalls = pd.read_excel('s3://alpha-omppg/Recalls/PPUD/ISP/PPUD_ISP_Recalls_2024Q2.xls')
deaths = pd.read_excel('ipp_deaths_in_custody.xlsx')

recalls['NOMS_ID'] = recalls['NOMS_ID'].str.upper()
deaths['NUMBER NOMIS'] = deaths['NUMBER NOMIS'].str.upper()

len(deaths) # 86
recalls.head()

strip_blanks(recalls)
strip_blanks(deaths)

recalls.info()
deaths.info()

deaths['DOD'] = pd.to_datetime(deaths['DOD'], dayfirst=True)

#---------------------------------- Add whole life flag to PPUD ISP data

# duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")
recalls['LICENCE_REVOKE_DATE'] = recalls['LICENCE_REVOKE_DATE'].dt.normalize()
recalls.info()
recalls['LICENCE_REVOKE_DATE'].head()

deaths = deaths.rename(columns={'NUMBER NOMIS':'NOMIS_ID'})

recalls = prepareMatch.prepareMatch(recalls)

#---------------------------------- Match to A&O Dataset on either NOMIS number, Prison Number or Name and DOB

query = """SELECT DISTINCT a.*, 
                            b.LICENCE_REVOKE_DATE
                            
                    FROM deaths AS a LEFT JOIN recalls AS b
                    
                    ON a.DOD >= b.LICENCE_REVOKE_DATE AND 
                      (a.NOMIS_ID = b.NOMS_ID OR
                       a.NOMIS_ID = b.NOMS_TRIM OR
                       a.NOMIS_ID = b.NOMS_START OR
                       a.NOMIS_ID = b.NOMS_END OR
                       a.NOMIS_ID = b.PRISON_NUMBER OR
                       a.NOMIS_ID = b.PN_TRIM OR
                       a.NOMIS_ID = b.PN_START OR
                       a.NOMIS_ID = b.PN_END)"""

matched = duckdb.sql(query).df()
matched.shape #106

matched = matched.sort_values(by=['NOMIS_ID','LICENCE_REVOKE_DATE'],ascending = [True,False])
matched
matched2 = matched.drop_duplicates(subset=['DOD', 'SURNAME', 'NAME', 'ESTAB', 'NOMIS_ID'], keep ='first').copy()
len(matched2)

matched2.to_excel('ipp_deaths.xlsx',index=False)