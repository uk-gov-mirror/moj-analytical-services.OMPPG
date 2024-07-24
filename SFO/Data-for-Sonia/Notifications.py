""" 
GOAL: TABULATE NOTIFICATION DATA FOR SONIA AND PUBLICATION
By Eric Nyame, 07/06/2023
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys # for adding folders to the search path
import duckdb
import importlib

import re

from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
from my_log import my_log
from Out_of_bounds_dates import date_out_of_bounds
import prepareMatch 
importlib.reload(prepareMatch)

# Set display options

pd.options.display.max_columns = None
pd.options.display.max_rows = None

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>


# Import Notifications data
Notifications = pd.read_excel("s3://alpha-omppg/SFO/Data for Sonia/Notifications/02 2024.xls")
Notifications.info()
Notifications.head()


Notifications.drop_duplicates("SFO_ID", inplace = True)
Notifications.info()

Notifications["NOMS_REGION_DESCRIPTION"].value_counts(dropna = False)
                                     N
Notifications = Notifications[Notifications["NOMS_REGION_DESCRIPTION"] != 'Not Specified']
Notifications.info()

Nots_Offence_Lkup = pd.read_excel("s3://alpha-omppg/SFO/Notifications_Offence_Lookup.xlsx")
Nots_Offence_Lkup.duplicated(subset = "SFO_OFFENCE_DESCRIPTION", keep=False).sum()
Nots_Offence_Lkup.head()

query =  """SELECT a.*, 
                   b.OFFENCE_SUMMARY
            FROM Notifications AS a LEFT JOIN Nots_Offence_Lkup AS b 
            ON  a.SFO_OFFENCE_DESCRIPTION = b.SFO_OFFENCE_DESCRIPTION
            """

Notifications = duckdb.sql(query).df()
Notifications .info()
Notifications.head()

Notifications[Notifications["OFFENCE_SUMMARY"].isna()]
# 0

# Tabulate

NPS_mask = ~Notifications["NOMS_REGION_DESCRIPTION"].str.contains('CRC|Not Specified',case = False,na=False)
Notifications[NPS_mask].\
    pivot_table(index = "NOMS_REGION_DESCRIPTION", 
                values = 'SFO_ID',
                fill_value = 0,
                aggfunc ='count',
               margins = True)

Notifications[~NPS_mask].\
    pivot_table(index = ["NOMS_REGION_DESCRIPTION","OFFENCE_SUMMARY"], 
                values = 'SFO_ID',
                fill_value = 0,
                aggfunc ='count',
               margins = True)

Notifications[NPS_mask].\
    pivot_table(index = "OFFENCE_SUMMARY", 
                values = 'SFO_ID',
                fill_value = 0,
                aggfunc ='count',
               margins = True)


