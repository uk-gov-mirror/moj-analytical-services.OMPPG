""" 
GOAL: TRACK INCREASE IN NOTIFICATIONS AND THE OFFENCES DRIVING IT
By Eric Nyame, 12/02/2024
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

#---------------------------------- Import own predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
# import prepareMatch
# importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
import TimeDiffs

#----------------------------------Set display options

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


#----------------------------------Set Global Parameters

#years = [2022,2023]
#quarters =['q1','q2','q3','q4']


#---------------------------------- Import notifications data
nots = pd.read_excel('sfo_compendium_2023_24.xlsx',sheet_name = None) # sheet_name = None imports all sheets

# type(notifications) # dict
# notifications.keys()

# put the sheets into one dataframe
notifications = pd.concat(nots.values(),ignore_index = True)

notifications.head()
notifications.info() # ensure STAGE_12_DOCN_RECEIVED_ACTUAL is datetime

# remove not specified cases
specials = notifications['SFO_ID'].isin([67138, 67228,67349,68158,69296,71264,71362,71449,71693,72933,72707,67420,69256,72951]) 
notifications['PROBATION_AREA_DESCRIPTION'].value_counts(dropna=False).reset_index()
notifications = notifications[(notifications['PROBATION_AREA_DESCRIPTION'] != 'Not Applicable') |(specials)]

# period column
notifications['YEAR'] = notifications['STAGE_12_DOCN_RECEIVED_ACTUAL'].dt.year
notifications['MONTH'] = notifications['STAGE_12_DOCN_RECEIVED_ACTUAL'].dt.month

notifications['PERIOD'] = notifications.apply(lambda row: f"{row['YEAR']-1}/{row['YEAR']}" if 1 <= row['MONTH'] <= 3 else f"{row['YEAR']}/{row['YEAR']+1}", axis=1)

notifications['DUMMY'] = 1
notifications.head()

notifications.groupby('PERIOD').size()

noti = notifications.pivot_table(index='DUMMY',columns='PERIOD',aggfunc='size',fill_value=0).reset_index()
noti['DUMMY'] = 'Total SFO notifications'

reviews = notifications[~notifications['STAGE_3_DOCN_RECEIVED_ACTUAL'].isna()].pivot_table(index='DUMMY',columns='PERIOD',aggfunc='size',fill_value=0).reset_index()
reviews['DUMMY'] = 'Total SFO reviews'

convictions = notifications[(notifications['OUTCOME_DESCRIPTION']=='Sentenced (SFO)') | (specials)].pivot_table(index='DUMMY',columns='PERIOD',aggfunc='size',fill_value=0).reset_index()
convictions['DUMMY'] = 'Total SFO convictions'

outstanding = notifications[notifications['OUTCOME_DESCRIPTION']=='Not Specified'].pivot_table(index='DUMMY',columns='PERIOD',aggfunc='size',dropna=False,fill_value=0).reset_index()
outstanding['DUMMY'] = 'Total Outstanding Outcomes'

show(pd.concat([noti,reviews,convictions,outstanding],ignore_index=True),buttons=["excelHtml5"])



