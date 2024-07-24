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


#---------------------------------- Load GPP data

year = 2024
quarter = 1

pop = pd.read_parquet(f"s3://alpha-omppg/ISP Population/final-data/isp_pop_{year}q{quarter}.parquet")

unreleased_ipps = pop[pop['ISP_STATUS'] == 'Unreleased IPP']


unreleased_ipps['TARIFF_YEARS'].value_counts(dropna=False)

unreleased_ipps[unreleased_ipps['TARIFF_YEARS'].isna()]

pop2 = pd.read_parquet(f"s3://alpha-omppg/isp-population/final/isp_pop_{year}q{quarter+1}.parquet")

unreleased_ipps_2 = pop2[pop2['ISP_STATUS'] == 'Unreleased IPP']


unreleased_ipps_2['TARIFF_YEARS'].value_counts(dropna=False)

unreleased_ipps_2[unreleased_ipps_2['TARIFF_YEARS'].isna()]
