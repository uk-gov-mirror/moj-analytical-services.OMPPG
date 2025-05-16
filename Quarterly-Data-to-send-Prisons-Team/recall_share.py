""" 
GOAL: .
By Eric Nyame, 21/08/2024
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
# import prepareMatch
# importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
import TimeDiffs

# Set display options

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.set_option('display.max_colwidth', None)

# Ensures no wrapping of cell contents - run it separately

"""
%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>
"""

recalls = pd.read_parquet("s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2024q4.parquet")
recalls.to_excel('recalls_final_2024q3.xlsx',index=False)
