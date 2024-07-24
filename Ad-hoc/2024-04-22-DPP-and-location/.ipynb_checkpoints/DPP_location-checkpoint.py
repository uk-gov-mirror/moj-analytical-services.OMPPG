""" 
GOAL: Names of DPPs and location
By Eric Nyame, 22/04/2024
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

# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x) #
        

#---------------------------------- Load GPP data

# Import MH SAS population data
pop = pd.read_sas("s3://alpha-omppg/ISP Population/Final Datasets/isp_pop_2024q1.sas7bdat", encoding='latin1')

pop.columns = pop.columns.str.upper()
pop['ISP_STATUS'].value_counts(dropna=False)

dpp_condition = (pop['ISP_STATUS'] == 'Unreleased IPP') & (pop['CUSTODY_TYPE_DESCRIPTION'] == 'DPP')
dpp = pop[dpp_condition]

dpp.head()
                     
len(dpp)
                     
dpp[['NOMIS_ID','SURNAME','FORENAME','CUSTODY_TYPE_DESCRIPTION','ISP_STATUS','PRISONNAME','CELLLOCATION','GENDER',]].to_excel("DPPS.xlsx", index=False)

