""" 
Please provide all data (organised by month and year) held on the number of Serious Further Offence (SFO) reviews that have been triggered by convictions involving death by dangerous driving and death by careless driving. For the above request, provide data from 2010 to 2024. I would like you to provide the information digitally via email where possible (samantha.k.pointon@outlook.com); where not possible, printed and posted to me.

By Eric Nyame, 19/11/2024
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


#---------------------------------- Import notifications data
nots = pd.read_excel('~/OMPPG/SFO/sfo-publication/2023_24/sfo_compendium_2023_24.xlsx',sheet_name = None) # sheet_name = None imports all sheets

# type(notifications) # dict
# nots.keys()

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

# convictions
convictions = notifications[(notifications['OUTCOME_DESCRIPTION']=='Sentenced (SFO)') | (specials)]

strip_blanks(convictions)

convictions_Offence_Lkup = pd.read_excel("s3://alpha-omppg/SFO/Conviction_Offence_Lookup.xls")

# convictions_Offence_Lkup.head()

query =  """SELECT a.SFO_ID, a.PERIOD,a.CONVICTION_OFFENCE_DESCRIPTION,a.SUPERVISION_TYPE_DESCRIPTION,
                   a.YEAR, a.MONTH,b.CONVICTION_OFFENCE_USE
            FROM convictions AS a LEFT JOIN convictions_Offence_Lkup AS b 
            ON  a.CONVICTION_OFFENCE_DESCRIPTION = b.CONVICTION_OFFENCE_DESCRIPTION
            """

convictions_2 = duckdb.sql(query).df()
len(convictions_2) #3295

show(convictions_2[convictions_2['CONVICTION_OFFENCE_USE'].isna()],buttons=["excelHtml5"]) # future year

# Tabulate
show(convictions_2.pivot_table(index='CONVICTION_OFFENCE_USE',columns='PERIOD',aggfunc='size',dropna=False,fill_value=0),buttons=["excelHtml5"])

show(convictions_2.pivot_table(index='CONVICTION_OFFENCE_USE',columns='YEAR',aggfunc='size',dropna=False,fill_value=0),buttons=["excelHtml5"])

# Deaths by careless driving only
death_by_driving = convictions_2[convictions_2['CONVICTION_OFFENCE_USE'] == '7 Causing death by dangerous driving']
len(death_by_driving) # 119

show(death_by_driving.pivot_table(index='YEAR',columns='MONTH',aggfunc='size',dropna=False,fill_value=0),buttons=["excelHtml5"])

death_by_driving[death_by_driving['YEAR'] == 2023]
