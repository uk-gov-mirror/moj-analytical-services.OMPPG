""" 
In your publication ‘Offender management statistics quarterly: July to September 2023’ there are statistics for IPP prisoners that remain in prison 10 years after they became eligible to apply for parole, but you have not provided any statistics for how many prisoners serving life sentences are released at the end of their minimum tariff expired Vs how many have been denied parole for 10 years + after their tariff expired. This is an unusual anomaly in the data supplied and it’s important for the public. Can you provide this data please? 

"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
#import importlib
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
# importlib.reload(TimeDiffs)
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

year = 2024
quarter = 4

# Get pop data

isp_pop = pd.read_parquet("s3://alpha-omppg/isp-population/final/isp_pop_2024q3.parquet")

# Keep unreleased lifers who are 10 or more years overtariff

mask = (isp_pop['ISP_STATUS'] == 'Unreleased Life') & (isp_pop['OVERTARIFF_YEARS'] >= 10)
sum(mask) # 640, the number to report

# Notes
# 1. The mask above, (isp_pop['OVERTARIFF_YEARS'] >= 10), automatically excludes whole life cases.
# 2. For whole life cases, overtariff is set to nan in the dataset.

# Show a breakdown
show(unreleased_life[mask]['OVERTARIFF_YEARS'].value_counts(dropna=False, sort=False).sort_index(), 
     buttons=["excelHtml5"]) # send to excel

