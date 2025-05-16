""" 
GOAL: PRODUCE MAPPA TABLES FOR PUBLICATION
By Eric Nyame, 27/09/2024
"""

#---------------------------------- Import Packages

import pandas as pd
# from pandas.api.types import CategoricalDtype
import numpy as np
import os
import sys
# import duckdb
# import importlib

# openpyxl
# from openpyxl import Workbook, load_workbook
# from openpyxl.styles import Font, Alignment
# from openpyxl.utils import get_column_letter

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

# sys.path.append('/home/jovyan/OMPPG/Macro Library')
# from my_log import my_log
# import Out_of_bounds_dates
# import prepareMatch
# importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
# import TimeDiffs

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
        
        # Period variables

mappa_2023_24 = pd.read_excel("../Table All Areas Source.xlsx")
mappa_2023_24
totals = mappa_2023_24.iloc[:,2:].sum()
totals = pd.DataFrame([totals])
totals.head()

totals.to_excel('Mappa_totals.xlsx',index=False)

