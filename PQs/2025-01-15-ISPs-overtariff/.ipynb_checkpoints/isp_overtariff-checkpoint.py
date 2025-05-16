""" 
1) HL3986: To ask His Majesty's Government how many additional months beyond tariff people serving an indeterminate sentence are held on average.

2) HL3985: To ask His Majesty's Government how many people are currently in prison serving a sentence of imprisonment for public protection who have been held for 15 years or more beyond their original tariff, broken down by the exact number of years over tariff?

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
# importlib.reload(TimeDiffs)
import tariff_groups


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
        
#----------------------------------SOme global variables are from 4 Releases_to_Recall program

year = 2024
quarter = 3

#----------------------------------Import PPUD data

isp_pop = pd.read_parquet("s3://alpha-omppg/isp-population/final/isp_pop_2024q3.parquet")

    # ------------------- HL3985: IPPs over tariff for 15 years or more (breakown of individual overtariff months)

unreleased_ipp = isp_pop[isp_pop['ISP_STATUS'] == 'Unreleased IPP'] # unreleased IPPs

over_15 = unreleased_ipp['OVERTARIFF_YEARS'] >= 15 # mask for those over tariff at least 15 years

sum(over_15) # check it sums to 147 as published.

unreleased_ipp[over_15]['OVERTARIFF_YEARS'].value_counts(dropna=False, sort=False).reset_index() # check counts

show(unreleased_ipp[over_15]['OVERTARIFF_YEARS'].value_counts(dropna=False, sort=False).reset_index(), 
     buttons=["excelHtml5"]) # send to excel

# ------------------- HL3986: All isps unreleased 

unreleased_cond = isp_pop['ISP_STATUS'].str.contains('Unreleased',case=False, na=False)
sum(unreleased_cond)

both_unreleased = isp_pop[unreleased_cond] # lifers and IPPs unreleased

both_unreleased['OVERTARIFF_MONTHS'].describe() # summarise overtariff months (NAs are automatically excluded)

both_unreleased[both_unreleased['OVERTARIFF_MONTHS'] >= 0]['OVERTARIFF_MONTHS'].describe() # should be the same
