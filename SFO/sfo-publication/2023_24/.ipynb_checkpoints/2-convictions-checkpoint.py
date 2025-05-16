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
convictions = notifications[(notifications['OUTCOME_DESCRIPTION']=='Sentenced (SFO)') | (specials)]

strip_blanks(convictions)

len(convictions[~convictions['PERIOD'].isin(['2013/2014','2023/2024'])]) #3021

convictions.groupby('PERIOD').size()

convictions_Offence_Lkup = pd.read_excel("s3://alpha-omppg/SFO/Conviction_Offence_Lookup.xls")

convictions_Offence_Lkup.head()
Nots_Offence_Lkup.duplicated(subset = "SFO_OFFENCE_DESCRIPTION", keep=False).sum()
Nots_Offence_Lkup.head()

query =  """SELECT a.SFO_ID, a.PERIOD,a.CONVICTION_OFFENCE_DESCRIPTION,a.SUPERVISION_TYPE_DESCRIPTION,
                   b.CONVICTION_OFFENCE_USE
            FROM convictions AS a LEFT JOIN convictions_Offence_Lkup AS b 
            ON  a.CONVICTION_OFFENCE_DESCRIPTION = b.CONVICTION_OFFENCE_DESCRIPTION
            """

convictions_2 = duckdb.sql(query).df()
len(convictions_2) #3295

show(convictions_2[convictions_2['CONVICTION_OFFENCE_USE'].isna()],buttons=["excelHtml5"])
# Tabulate


show(convictions_2.pivot_table(index='CONVICTION_OFFENCE_USE',columns='PERIOD',aggfunc='size',dropna=False,fill_value=0),buttons=["excelHtml5"])

show(convictions_2.pivot_table(index='SUPERVISION_TYPE_DESCRIPTION',columns='PERIOD',aggfunc='size',fill_value=0),buttons=["excelHtml5"])

murders = convictions_2[convictions_2['CONVICTION_OFFENCE_USE']=='1 Murder']
show(murders.pivot_table(index='SUPERVISION_TYPE_DESCRIPTION',columns='PERIOD',aggfunc='size',fill_value=0),buttons=["excelHtml5"])