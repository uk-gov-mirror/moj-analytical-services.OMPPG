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

# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #
        
#----------------------------------SOme global variables are from 4 Releases_to_Recall program

month = str(6).zfill(2) # pads the number with a leading zero
day = 30
year = 2025
quarter = 2


#---------------------------------- Load GPP data

nowRecalled = pd.read_parquet(f"s3://alpha-omppg/isp-population/final/isp_pop_2025q2.parquet")

nowRecalled = nowRecalled[nowRecalled['ISP_STATUS'] =='Recalled IPP']

nowRecalled['ISP_STATUS'].value_counts()

nowRecalled.head()
len(nowRecalled) # 1508
nowRecalled['PPUD_STATUS'].value_counts(dropna=False)

len(nowRecalled['LAST_RTC_DATE']) # 1508 non missing
len(nowRecalled['LAST_SUBSEQUENT_DATE']) # 1508 non missing

nowRecalled['LAST_SUBSEQUENT_DATE'] = nowRecalled['LAST_SUBSEQUENT_DATE'].dt.normalize()
nowRecalled['LAST_RTC_DATE'] = nowRecalled['LAST_RTC_DATE'].dt.normalize()


b4Nov2024 = nowRecalled[nowRecalled['LAST_SUBSEQUENT_DATE'] <
pd.Timestamp(2024,11,15)]

len(b4Nov2024) # 1138

b4Nov2024['LAST_REVIEW_RESULT'].value_counts(dropna=False)

louisaMask = (b4Nov2024['LAST_REVIEW_RESULT'] != 'Release') & (b4Nov2024['LAST_SUBSEQUENT_DATE'] > b4Nov2024['LAST_RTC_DATE'])

finalData = b4Nov2024[louisaMask].copy()
len(finalData) # 617
finalData['LAST_RTC_DATE'].max()

finalData = finalData.sort_values(by='LAST_RTC_DATE',ascending=False)

cols = ['NOMIS_ID','SURNAME','LAST_RTC_DATE','LAST_SUBSEQUENT_DATE','LAST_REVIEW_RESULT']

finalData = finalData[cols + [f for f in finalData.columns if f not in cols]]

finalData.head(10)

finalData['IMPRISONMENTSTATUSSHORT'].value_counts(dropna=False)

finalData['PPUD_STATUS'].value_counts(dropna=False)
finalData['IMPRISONMENT_STATUS_CATEGORY'].value_counts(dropna=False)
finalData[finalData['IMPRISONMENTSTATUSSHORT']=='LR_LIFE'].head()

finalData.to_excel('Recalled_Louis.xlsx',index=False)
