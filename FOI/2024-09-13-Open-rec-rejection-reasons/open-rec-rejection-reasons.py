""" 
GOAL: COUNT OF OPEN RECOMMENDATION REJECTION REASONS
By Eric Nyame, 13/09/2024
"""

import pandas as pd
# from pandas.api.types import CategoricalDtype
import numpy as np
# import sys
# import duckdb
# import importlib

# openpyxl
#from openpyxl import Workbook, load_workbook
#from openpyxl.styles import Font, Alignment
# from openpyxl.utils import get_column_letter

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

# sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
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

# Get last final recall data for the last 5 quarters----------------------------------------------------------------------


rejections = pd.read_excel('Open-rejections-2023.xls')
rejections.head()

rejections['NUMBER_OF_OPEN_REFUSAL_REASONS'].isna().sum() # 0
rejections['NUMBER_OF_OPEN_REFUSAL_REASONS'].sum() # 412
len(rejections) # 259

# Expand dataset to include one row for every reason

    # Split comma-separated reasons into a list, expand these into rows, and clean spaces
reasons = rejections.copy()
reasons['REASON_DESC'] = reasons['OPEN_REFUSAL_REASON_DESCRIPTIONS'].str.split(',')
reasons.head()

reasons = reasons.explode('REASON_DESC')
reasons.head()

reasons['REASON_DESC'] = reasons['REASON_DESC'].str.strip()

# Bring cases with no reason recorded
missing_reasons = rejections[rejections['NUMBER_OF_OPEN_REFUSAL_REASONS'].isna()]
len(missing_reasons) # 0

# Concatenate the 'expanded_reasons' and 'missing_reasons' datasets
reasons = pd.concat([reasons, missing_reasons], ignore_index=True)
reasons.shape # (414,22)

# Count occurrences of each 'REASON_DESC', and sort
reason_counts = reasons['REASON_DESC'].value_counts(dropna=False).reset_index()
reason_counts.columns = ['REASON_DESC', 'n']
reason_counts = reason_counts.sort_values('n', ascending=False)
reason_counts

# Calculate percentages and cumulative frequencies
reason_counts['PERCENT'] = (reason_counts['n'] / reason_counts['n'].sum()) * 100
reason_counts['CUM_FREQ'] = reason_counts['n'].cumsum()
reason_counts['CUM_PERCENT'] = reason_counts['PERCENT'].cumsum()
reason_counts

# Round the percentages
reason_counts['PERCENT'] = reason_counts['PERCENT'].round(2)
reason_counts['CUM_PERCENT'] = reason_counts['CUM_PERCENT'].round(2)
reason_counts