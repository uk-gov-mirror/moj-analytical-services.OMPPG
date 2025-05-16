""" 
GOAL: CREATE GPP AND INFORMATION TO QUARTERLY ISP POP FOR OMSQ
By Eric Nyame, 14/04/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
# print(duckdb.__version__)
# import importlib

from itables import show

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
import prepareMatch
# importlib.reload(prepareMatch)
import openMatch
#importlib.reload(openMatch)
import TimeDiffs
import tariff_groups
#importlib.reload(tariff_groups)

# Set display options

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.set_option('display.max_colwidth', None)

# Ensures no wrapping of cell contents - run it separately

# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x) #
        
%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

#---------------------------------- Load GPP data

isp = pd.read_parquet("s3://alpha-omppg/isp-population/final/isp_pop_2025q1.parquet")

isp['EXTRACTDATE'].value_counts()

ipp = isp[isp['ISP_STATUS'].str.contains('IPP',case=False,na=False)]
len(ipp)

ipp.pivot_table(index='O')
unreleased_ipp = ipp[ipp['ISP_STATUS'].str.contains('Unr',case=False,na=False)]

tariff_not_past = unreleased_ipp[unreleased_ipp['TARIFF_PAST'] == 'N'] 

len(tariff_not_past) # 8

tariff_not_past
3]ipp[ipp['ISP_STATUS'].str.contains('Unr',case=False,na=False)]
len(unreleased_ipp) # 1045

len(unreleased_ipp[unreleased_ipp['TARIFF_YEARS'] < 3]) # 416
unreleased_ipp[unreleased_ipp['TARIFF_YEARS'] < 3].head()
ipp.head()

rape = (ipp['OFFENCE'].str.contains('rape',case=False)) & (~ipp['OFFENCE'].str.contains('attempt',case=False))

ipp[rape]['OFFENCE'].value_counts(dropna=False)
ipp_rape = ipp[rape]

len(ipp_rape) # 415
ipp_rape.head(5)

ipp_rape['PRISON_NUMBER'].isna().sum()

ipp_rape.sample(50)

show(ipp_rape.sample(50), buttons=["excelHtml5"])
