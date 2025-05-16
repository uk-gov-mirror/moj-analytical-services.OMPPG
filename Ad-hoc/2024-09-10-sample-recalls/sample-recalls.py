""" 
GOAL: SAMPLE OF STANDARD RECALLS
By Eric Nyame, 10/09/2024
"""

import pandas as pd
# from pandas.api.types import CategoricalDtype
import numpy as np
import sys
# import duckdb
# import importlib

# openpyxl
#from openpyxl import Workbook, load_workbook
#from openpyxl.styles import Font, Alignment
# from openpyxl.utils import get_column_letter

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

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Get last final recall data for the last 5 quarters----------------------------------------------------------------------


recalls = pd.read_excel('Recalls2024Q2.xls', sheet_name='Recalls_2024_Q2')
recalls.head()

recalls['CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION'].value_counts()

det_recalls = recalls[recalls['CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION'] == 'Determinate'].copy() # exclude extended cases too

det_recalls['RECALL_TYPE_DESCRIPTION'].value_counts()
det_recalls['STANDARD_DET'] = 'Yes'
det_recalls.loc[det_recalls['RECALL_TYPE_DESCRIPTION'].str.contains('fix|ftr', case=False),'STANDARD_DET'] = 'No'
det_recalls.loc[det_recalls['RECALL_TYPE_DESCRIPTION'] == 'Indeterminate Recall','STANDARD_DET'] = 'No'
# det_recalls.loc[det_recalls['RECALL_TYPE_DESCRIPTION'].str.contains('HDC', case=False),'STANDARD_DET'] = 'No'

det_recalls.pivot_table(index='RECALL_TYPE_DESCRIPTION',columns='STANDARD_DET', fill_value=0,aggfunc='size')

det_recalls.info()
det_recalls.columns

retain = [ 'NOMS_ID', 'FAMILY_NAME','FIRST_NAMES', 'LICENCE_REVOKE_DATE', 'NUMBER_OF_RECALL_REASONS',
         'RECALL_REASON_DESCRIPTIONS', 'RECALL_TYPE_DESCRIPTION', 'CUSTODY_TYPE_DESCRIPTION',
       'CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION', 'DOB', 'DOS',
       'CRO_PNC','NOMS_REGION_DESCRIPTION', 
       'OUT_OF_HOURS','PRISON_NUMBER', 'PROBATION_AREA_DESCRIPTION',
       
       'RTC_DATE', 'STANDARD_DET']

out_of_hours = det_recalls[(det_recalls['STANDARD_DET'] == 'Yes') & (det_recalls['OUT_OF_HOURS'] == True)].copy()
out_of_hours = out_of_hours[~out_of_hours['RTC_DATE'].isna()]
out_of_hours = out_of_hours.sort_values('LICENCE_REVOKE_DATE',ascending=False)
out_of_hours.head()
# out_of_hours_final = out_of_hours[:30][retain]
len(out_of_hours_final) # 30
out_of_hours_final.head()

out_of_hours.to_excel('out_of_hours.xlsx',index=False)

not_out_of_hours = det_recalls[(det_recalls['STANDARD_DET'] == 'Yes') & (det_recalls['OUT_OF_HOURS'] == False)].copy()
not_out_of_hours = not_out_of_hours[~not_out_of_hours['RTC_DATE'].isna()]
not_out_of_hours = not_out_of_hours.sort_values('LICENCE_REVOKE_DATE',ascending=False)
# not_out_of_hours_final = not_out_of_hours[:70][retain]
len(not_out_of_hours_final) # 30
not_out_of_hours_final.head()

not_out_of_hours.to_excel('not_out_of_hours.xlsx',index=False)
