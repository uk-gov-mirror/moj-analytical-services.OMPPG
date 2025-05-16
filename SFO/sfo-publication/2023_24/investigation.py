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
notifications = pd.read_excel('sfo_compendium_2023_24.xlsx',sheet_name = None) # sheet_name = None imports all sheets

# type(notifications) # dict
# notifications.keys()

# put the sheets into one dataframe
notifications = pd.concat(notifications.values(),ignore_index = True)

notifications.head()
notifications.info() # ensure STAGE_12_DOCN_RECEIVED_ACTUAL is datetime

# remove not specified cases
notifications['NOMS_REGION_DESCRIPTION'].value_counts(dropna=False)
notifications = notifications[notifications['NOMS_REGION_DESCRIPTION'] != 'Not Specified']

# period column
notifications['YEAR'] = notifications['STAGE_12_DOCN_RECEIVED_ACTUAL'].dt.year
notifications['MONTH'] = notifications['STAGE_12_DOCN_RECEIVED_ACTUAL'].dt.month

notifications['PERIOD'] = notifications.apply(lambda row: f"{row['YEAR']-1}/{row['YEAR']}" if 1 <= row['MONTH'] <= 3 else f"{row['YEAR']}/{row['YEAR']+1}", axis=1)

notifications.head()

notifications.groupby('PERIOD').size()

notifications.pivot_table(index='YEAR',columns='MONTH',aggfunc='size',fill_value=0).to_excel('YEAR_MONTH.xlsx')

notifications.pivot_table(index='PERIOD',columns='MONTH',aggfunc='size',fill_value=0).to_excel('PERIOD_MONTH.xlsx')

# DATE OF SFO
notifications['SFO_YEAR'] = notifications['DATE_OF_SFO'].dt.year.astype('Int64')
notifications['SFO_MONTH'] = notifications['DATE_OF_SFO'].dt.month.astype('Int64')

notifications['SFO_PERIOD'] = np.nan
not_miss_sfdt = ~notifications['SFO_YEAR'].isna()
notifications.loc[not_miss_sfdt,'SFO_PERIOD'] = notifications[not_miss_sfdt].apply(lambda row: f"{row['SFO_YEAR']-1}/{row['SFO_YEAR']}" if 1 <= row['SFO_MONTH'] <= 3 else f"{row['SFO_YEAR']}/{row['SFO_YEAR']+1}", axis=1)

notifications.head()

notifications.groupby('SFO_PERIOD',dropna=False).size()

# NOTIFICATION PERIOD VS DATE OF SFO PERIOD

notifications.pivot_table(index='PERIOD',columns='SFO_PERIOD',aggfunc='size',fill_value=0).to_excel('NOTI_BY_SFO.xlsx')

notifications.pivot_table(index='PERIOD',columns='MONTH',aggfunc='size',fill_value=0).to_excel('PERIOD_MONTH.xlsx')


# NOTIFICATION PERIOD VS Highest risk

notifications['HIGHEST_RISK_OF_HARM_DESCRIPTION'].value_counts(dropna=False)
show(notifications.pivot_table(index='PERIOD',columns='HIGHEST_RISK_OF_HARM_DESCRIPTION',aggfunc='size',fill_value=0),buttons=["copyHtml5", "csvHtml5", "excelHtml5"])

# NOTIFICATION PERIOD VS NORMS REGION

notifications['NOMS_REGION_DESCRIPTION'].value_counts(dropna=False)
notifications['PROBATION_AREA_DESCRIPTION'].value_counts(dropna=False)
show(notifications.pivot_table(index='NOMS_REGION_DESCRIPTION',columns='PERIOD',aggfunc='size',fill_value=0),buttons=["excelHtml5"])

# NOTIFICATION PERIOD VS PROBATION AREA

notifications['PROBATION_AREA_DESCRIPTION'].value_counts(dropna=False)
show(notifications[notifications['PERIOD'].isin(['2022/2023','2023/2024'])].pivot_table(index=['NOMS_REGION_DESCRIPTION','PROBATION_AREA_DESCRIPTION'],columns='PERIOD',aggfunc='size',fill_value=0),buttons=["excelHtml5"])


# NOTIFICATION PERIOD VS PB Release

notifications['PB_RELEASED'].value_counts(dropna=False)
show(notifications.pivot_table(index='PB_RELEASED',columns='PERIOD',aggfunc='size',fill_value=0),buttons=["excelHtml5"])

# NOTIFICATION PERIOD VS SUper

notifications['SUPERVISION_TYPE_DESCRIPTION'].value_counts(dropna=False)
show(notifications.pivot_table(index='SUPERVISION_TYPE_DESCRIPTION',columns='PERIOD',aggfunc='size',fill_value=0),buttons=["excelHtml5"])
#---------------------------------- Clean up Notifications data

sfo_offences = notifications['SFO_OFFENCE_DESCRIPTION'].value_counts(dropna=False).reset_index()

sfo_offences.to_excel('sfo_index.xlsx',index=False)

notifications.info()
notifications.duplicated('SFO_ID',keep=False).sum() # 0

notifications["NOMS_REGION_DESCRIPTION"].value_counts(dropna = False)
                                     
#---------------------------------- Import lookup data

Offence_Lkup = pd.read_excel("temp_look_up.xlsx")
Offence_Lkup.duplicated(subset = "SFO_OFFENCE_DESCRIPTION", keep=False).sum()
Offence_Lkup.head()

#---------------------------------- Make uniform the entries in notifications data and lookup data

    # remove more than one blanks and remove trailing and starting blanks
strip_blanks(notifications)
strip_blanks(Offence_Lkup)

#---------------------------------- Join the two

query =  """SELECT a.PERIOD, 
                   b.OFFENCE
            FROM notifications AS a LEFT JOIN Offence_Lkup AS b 
            ON  a.SFO_OFFENCE_DESCRIPTION = b.SFO_OFFENCE_DESCRIPTION
            """

# Notifications.drop(['OFFENCE_SUMMARY','OFFENCE_SUMMARY_2'],axis = 1, inplace=True)
notifications = duckdb.sql(query).df()

notifications.\
    pivot_table(index = "OFFENCE", 
                columns = 'PERIOD',
                #values = 'first',
                fill_value = 0,
                aggfunc ='size').to_excel('Summary.xlsx')

