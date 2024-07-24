""" 
GOAL: On the RARR spreadsheet we need to pull in the recall type and date of RTC for the recall immediately prior to the RARR, as every RARR must have an RTC date on it. We then need to filter the RARR list for those cases that are Standard ORA recalls to get the data Ian is after. 
By Eric Nyame, 28/02/2024
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
        
#----------------------------------Set globals

yy = 23 # year as yy
mm = 12
dd = 31

year = 2023
quarter = 4 

#----------------------------------Import PPUD data

rtc = pd.read_excel("s3://alpha-omppg/Ad hoc/24 02 28 RARR and RTC/RTCs (31-5-22 to 27-2-24).xls")
rarrRels = pd.read_excel("s3://alpha-omppg/Ad hoc/24 02 28 RARR and RTC/RARR Releases (31-5-23 to 27-2-24).xls")

    # check data types and set datetime columns properly
rtc.info()
rarrRels.info()

rtc = rtc.drop_duplicates()
rarrRels = rarrRels.drop_duplicates()

rtc.shape
rarrRels.shape
    # remove trailing and leading blanks
strip_blanks(rtc)
strip_blanks(rarrRels)

#---------------------------------- Bring in RTC details to RARR release

# duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query = """SELECT a.*, 
                  b.RECALL_TYPE_DESCRIPTION as RECALL_TYPE_PRIOR,
                  b.RTC_DATE AS RTC_DATE_PRIOR 
                  
            FROM rarrRels AS a LEFT JOIN rtc AS b
            
            ON  (
                    (a.NOMS_ID = b. NOMS_ID AND a.NOMS_ID IS NOT NULL) OR
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) 
                ) AND
                a.ACTUAL >= b.RTC_DATE"""

matched = duckdb.sql(query).df()
# matched.columns
# cols = ['NOMS_ID','FAMILY_NAME','RTC_DATE_PRIOR','ACTUAL', 'RECALL_TYPE_PRIOR']

    # rearrange columns
    
matched = matched[cols + [i for i in matched.columns if i not in cols]]
matched['RTC_DATE_PRIOR'] = matched['RTC_DATE_PRIOR'].dt.normalize()

    # Deduplicate
    
matched = matched.sort_values(by = ['NOMS_ID','RTC_DATE_PRIOR'],ascending =[True,False])

nodups = matched.drop_duplicates(['NOMS_ID','ACTUAL'], keep='first')

    # save on AWS
    
nodups.to_excel("s3://alpha-omppg/Ad hoc/24 02 28 RARR and RTC/Enhanced_RARR_Releases.xlsx", index=False)