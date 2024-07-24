""" 
GOAL: Possible DPPs in prison, based on date of birth
By Eric Nyame, 09/05/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
# print(duckdb.__version__)
import importlib
import inspect
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
        

#---------------------------------- Load GPP data

# Import list
isps_mar_2024 = pd.read_parquet("s3://alpha-omppg/ISP Population/final-data/ISP_Pop_2024q1.parquet")

isps_mar_2024.head()
isps_mar_2024['CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

inspect.getfullargspec(pd.pivot_table) 

pd.pivot_table(isps_mar_2024,
               index='CUSTODY_TYPE_DESCRIPTION',
               columns='ISP_STATUS', 
               dropna=False,
               aggfunc='size',  # Counting the number of occurrences
               fill_value=0,
              margins=True).reset_index()
isps_mar_2024.head()
isps_mar_2024['AGE_SENT_COMMENCEMENT'] = isps_mar_2024.apply(lambda x: TimeDiffs.year_diff(x['DATEOFBIRTH'],pd.Timestamp(2005,4,4).date()),axis=1)

hmp_mask = (isps_mar_2024['CUSTODY_TYPE_DESCRIPTION'] ==  'HMP [*]')
hmp_mask.sum()

hmp_pop_mar_2024 = isps_mar_2024[hmp_mask]
hmp_pop_mar_2024.shape

hmp_pop_mar_2024['TARIFF_PAST'].value_counts(dropna=False)

pd.pivot_table(hmp_pop_mar_2024,
               index=['CUSTODY_TYPE_DESCRIPTION','ISP_STATUS'],
               columns='TARIFF_PAST', 
               dropna=False,
               aggfunc='size',  # Counting the number of occurrences
               fill_value=0).reset_index()