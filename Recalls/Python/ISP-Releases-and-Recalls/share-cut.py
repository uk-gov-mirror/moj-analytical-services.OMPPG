""" 
GOAL: Cut of re-release data for ISPs
By Eric Nyame, 27/08/2025
"""

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
#importlib.reload(openMatch)
import TimeDiffs

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

# ISP release data since 2010 up to 31 March 2025
isp_releases = pd.read_parquet(f"s3://alpha-omppg/isp_releases/final-data/isp_releases_2025q1.parquet")

# Keep only 2025Q1 data
isp_releases = isp_releases[isp_releases['RELEASE_DATE'] >= pd.Timestamp(2025,1,1)]

# Keep only re-releases
reReleases = isp_releases[isp_releases['RELEASE_TYPE'] == 'Recall Re-release']

reReleases['RELEASE_TYPE'].value_counts()

reReleases.to_excel("reReleases.xlsx",index=False)

reReleases.loc[reReleases['CUSTODY_TYPE_DESCRIPTION'] == 'DPP','CUSTODY_TYPE_DESCRIPTION'] = 'IPP'
reReleases.loc[reReleases['CUSTODY_TYPE_DESCRIPTION'] != 'IPP','CUSTODY_TYPE_DESCRIPTION'] = 'Life sentence'

reReleases['MONTHS_RECALLED'] = reReleases.apply(lambda x: TimeDiffs.month_diff(x['LAST_RTC_DATE'],x['RELEASE_DATE']),axis=1)

reReleases[['FILE_REFERENCE','CUSTODY_TYPE_DESCRIPTION','LAST_RTC_DATE','RELEASE_DATE','MONTHS_RECALLED']].sample(n = 10)

table_11_summary =reReleases.groupby('CUSTODY_TYPE_DESCRIPTION')['MONTHS_RECALLED'].agg(['size','mean']).reset_index()

table_11_summary

