""" 
To ask His Majesty’s Government what was the average tariff length imposed for murder in (1) 2022, and (2) 2023. 

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

# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #
        
# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>
        
#----------------------------------SOme global variables are from 4 Releases_to_Recall program

month = str(12).zfill(2) # pads the number with a leading zero
day = 31
year = 2024
quarter = 4

#----------------------------------Import PPUD data
ispPPUD = pd.read_excel(f's3://alpha-omppg/isp-population/PPUD/{year}Q{quarter}/PPUD_ISP_{year}Q{quarter}.xls')
wlPPUD = pd.read_excel(f's3://alpha-omppg/isp-population/PPUD/{year}Q{quarter}/PPUD_WholeLife_{year}Q{quarter}.xls')

ispPPUD = ispPPUD.drop_duplicates()
wlPPUD = wlPPUD.drop_duplicates()

ispPPUD.info()
wlPPUD.info()

#----------------------------------Datetime columns appearing as object type - change
ispPPUD.select_dtypes(include=['object']).dtypes # find datetime column showing as an object column

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
ispPPUD_Matched.shape # 25222, 25147

ispPPUD_Matched['WHOLE_LIFE'].value_counts(dropna=False)

# Check how murder is entered as an offence

murder_mask = ispPPUD_Matched['INDEX_OFFENCE_DESCRIPTION'].str.contains('Murder', na = False, case = False,)

ispPPUD_Matched[murder_mask]['INDEX_OFFENCE_DESCRIPTION'].value_counts().to_frame()

# Murder cases from 2000 onwards, no whole life orders

murderers = ispPPUD_Matched[
                            (ispPPUD_Matched['INDEX_OFFENCE_DESCRIPTION'] == 'Murder') & \
                            (ispPPUD_Matched['DOS'].dt.year >= 2000) & \
                            (ispPPUD_Matched['WHOLE_LIFE'] != True)
                           ].copy()

# Calculate tariff_days, tariff_months and tariff_years

murderers['TARIFF_DAYS'] = murderers.apply(
                                            lambda row: (row['TARIFF_EXPIRY_DATE'] - row['DOS']).days \
                                            if (row['DOS'] < row['TARIFF_EXPIRY_DATE']) else pd.NA,
                                            axis = 1
                                          )

    # Tariff length in years and months

murderers['TARIFF_EXPIRY_DATE'] = murderers['TARIFF_EXPIRY_DATE'].dt.normalize()
murderers['DOS'] = murderers['DOS'].dt.normalize()
ispPPUD_Matched.head()

ispPPUD_Matched.dtypes

tmth = murderers['TARIFF_EXPIRY_DATE'] >= murderers['DOS']
tmth2 = murderers['TARIFF_EXPIRY_DATE'].dt.year == 1900

murderers['TARIFF_DAYS'] = murderers['TARIFF_EXPIRY_DATE'] - murderers['DOS']
murderers.loc[tmth2,'TARIFF_DAYS'] = np.nan

murderers['TARIFF_MONTHS'] = np.where(tmth,
                                        murderers.apply(lambda x: TimeDiffs.month_diff(x['DOS'],x['TARIFF_EXPIRY_DATE']),axis=1),
                                        np.nan)
                        
murderers.loc[tmth2,'TARIFF_MONTHS'] = np.nan

murderers['TARIFF_YEARS'] = murderers['TARIFF_MONTHS'] // 12

  # Year of sentence
murderers['SENTENCE_YEAR'] = murderers['DOS'].dt.year

    # Age at time of sentence


in_scope = murderers['SENTENCE_YEAR']>= 2022

show( np.round(murderers[in_scope].pivot_table(index='SENTENCE_YEAR',
                                      values='TARIFF_MONTHS',
                                      observed=True,
                                      aggfunc='mean')), buttons=["excelHtml5"])

show( np.round(murderers[in_scope].pivot_table(index='SENTENCE_YEAR',
                                      values='TARIFF_MONTHS',
                                      observed=True,
                                      aggfunc='median')), buttons=["excelHtml5"])

