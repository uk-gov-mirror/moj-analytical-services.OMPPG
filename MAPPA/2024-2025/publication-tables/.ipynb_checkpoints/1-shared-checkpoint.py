""" 
GOAL: PRODUCE RECALL TABLES FOR OMSQ.

"""

#---------------------------------- Import Packages

import pandas as pd
from pandas.api.types import CategoricalDtype
import numpy as np
import sys
import duckdb
import importlib
import os

from itables import show

# openpyxl
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

# Function to show table in my preferred way
def show_data(data):
    show(data,
         scrollY="200px", 
         scrollCollapse=True, 
         paging=False,
         buttons=["excelHtml5"])
    
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

table1_values = ['TOTAL_MAPPA_OFFENDERS','CAT1TOT', 'CAT2TOT', 'CAT3TOT','CAT4TOT','LEVEL1TOTT1', 'CAT1L1', 'CAT2L1','CAT3L1', 'CAT4L1','LEVEL2TOTT1', 'CAT1L2','CAT2L2','CAT3L2','CAT4L2',
  'LEVEL3TOTT1','CAT1L3','CAT2L3','CAT3L3', 'CAT4L3']

table4_values =['CAT1L2YEAR', 'CAT1L3YEAR', 'CAT2L2YEAR','CAT2L3YEAR', 
                'CAT3L2YEAR', 'CAT3L3YEAR','CAT4L2YEAR','CAT4L3YEAR',
                'LEVEL2TOTT3', 'LEVEL3TOTT3']

table9b_conv_dict = {'CAT1L1SFOCONV': 'CAT1L1',
                     'CAT1L2SFOCONV': 'CAT1L2',
                     'CAT1L3SFOCONV': 'CAT1L3',
                     'CAT2L1SFOCONV': 'CAT2L1',
                     'CAT2L2SFOCONV': 'CAT2L2',
                     'CAT2L3SFOCONV': 'CAT2L3',
                     'CAT3L2SFOCONV': 'CAT3L2',
                     'CAT3L3SFOCONV': 'CAT3L3',
                     'CAT4L1SFOCONV': 'CAT4L1',
                     'CAT4L2SFOCONV': 'CAT4L2',
                     'CAT4L3SFOCONV': 'CAT4L3'}

table9b_still_dict = {'CAT1L1SFOCHARGE': 'CAT1L1',
                         'CAT1L2SFOCHARGE': 'CAT1L2',
                         'CAT1L3SFOCHARGE': 'CAT1L3',
                         'CAT2L1SFOCHARGE': 'CAT2L1',
                         'CAT2L2SFOCHARGE': 'CAT2L2',
                         'CAT2L3SFOCHARGE': 'CAT2L3',
                         'CAT3L2SFOCHARGE': 'CAT3L2',
                         'CAT3L3SFOCHARGE': 'CAT3L3',
                         'CAT4L1SFOCHARGE': 'CAT4L1',
                         'CAT4L2SFOCHARGE': 'CAT4L2',
                         'CAT4L3SFOCHARGE': 'CAT4L3'}

table9b_other_dict ={'CAT1L1SFOOTHER': 'CAT1L1',
                     'CAT1L2SFOOTHER': 'CAT1L2',
                     'CAT1L3SFOOTHER': 'CAT1L3',
                     'CAT2L1SFOOTHER': 'CAT2L1',
                     'CAT2L2SFOTHER': 'CAT2L2',
                     'CAT2L3SFOOTHER': 'CAT2L3',
                     'CAT3L2SFOOTHER': 'CAT3L2',
                     'CAT3L3SFOOTHER': 'CAT3L3',
                     'CAT4L1SFOOTHER': 'CAT4L1',
                     'CAT4L2SFOOTHER': 'CAT4L2',
                     'CAT4L3SFOOTHER': 'CAT4L3'}

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