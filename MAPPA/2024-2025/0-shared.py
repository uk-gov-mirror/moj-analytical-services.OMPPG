""" 
GOAL: PRODUCE RECALL TABLES FOR OMSQ.
By Eric Nyame, 17/04/2024
"""

#---------------------------------- Import Packages

import pandas as pd
from pandas.api.types import CategoricalDtype
import numpy as np
import sys
import duckdb
import importlib
import os

# openpyxl
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
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

# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #
        
        
        # Period variables
qtr = 1 # 1:Jan-Mar, 2:Apr-Jun, 3:Jul-Sep, 4:Oct-Dec
year = 2025 # Enter the year being run in 4 digit format

# Quarter mapping dictionary


def ethnicity(df,ethnicity_original,ethnicity_new):
    table_12_conditions = [
        df[ethnicity_original].str.contains('mixed', case=False, na=False),
        df[ethnicity_original].str.contains('black', case=False, na=False),
        df[ethnicity_original].str.contains('African', case=False, na=False),
        df[ethnicity_original].str.contains('white', case=False, na=False),
        df[ethnicity_original].str.contains('Asian', case=False, na=False),
        df[ethnicity_original].str.contains('Refusal', case=False, na=False),
        df[ethnicity_original].str.contains('chinese', case=False, na=False),
        df[ethnicity_original].str.contains('Other Ethnic Group', case=False, na=False),
        df[ethnicity_original].str.contains('Arab', case=False, na=False),
        df[ethnicity_original].str.contains('Other', case=False, na=False),
        df[ethnicity_original].str.contains('Not Known', case=False, na=False),
        df[ethnicity_original].str.contains('Not Applicable', case=False, na=False),
        df[ethnicity_original].str.contains('Prefer not to say', case=False, na=False),
        df[ethnicity_original].str.contains('Any Other', case=False, na=False)
    ]
  
    choices = [
        'Mixed',
        'Black or Black British',
        'Black or Black British',
        'White',
        'Asian or Asian British',
        'Not stated',
        'Asian or Asian British',  # Now classified as Asian
        'Other ethnic group',
        'Other ethnic group',
        'Other ethnic group',
        'Unknown',
        'Unknown',
        'Not stated',
        'Other ethnic group'
    ]

    df[ethnicity_new] = np.nan # set initially to nans
    df[ethnicity_new] = np.select(table_12_conditions, choices, default=df[ethnicity_new])

ethnicity_vals = ['Asian or Asian British', 'Black or Black British','Mixed','White', 'Other ethnic group', 'Not stated']