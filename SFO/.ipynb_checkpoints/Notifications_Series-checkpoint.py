""" 
GOAL: TRACK INCREASE IN NOTIFICATIONS AND THE OFFENCES DRIVING IT
By Eric Nyame, 12/02/2024
"""

#---------------------------------- Import Packages and set options

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


#---------------------------------- Import notifications data
    
    # Import all tabs for notifications data up to 31 March 2023
compendium = pd.read_excel("s3://alpha-omppg/SFO/SFO_Compendium_2023.xlsx", sheet_name = None)

    # Get the sheet names
sheets = list(compendium.keys())
# sheets

    # Concatenate the sheets to get notifications data for 1 April 2014 to 31 March 2022
Notifications = pd.concat([compendium[sheet] for sheet in sheets[1:]],
                    axis = 'index', 
                    ignore_index=True)

    # Import notification data for each month since 2023

# for i in range(7,13):
    #print(f'Nots_0{i} = pd.read_excel("s3://alpha-omppg/SFO/Data for Sonia/Notifications/0{i} 2023.xls"')
    
Nots_04 = pd.read_excel("s3://alpha-omppg/SFO/Data for Sonia/Notifications/04 2023.xls")
Nots_05 = pd.read_excel("s3://alpha-omppg/SFO/Data for Sonia/Notifications/05 2023.xls")
Nots_06 = pd.read_excel("s3://alpha-omppg/SFO/Data for Sonia/Notifications/06 2023.xls")
Nots_07 = pd.read_excel("s3://alpha-omppg/SFO/Data for Sonia/Notifications/07 2023.xls")
Nots_08 = pd.read_excel("s3://alpha-omppg/SFO/Data for Sonia/Notifications/08 2023.xls")
Nots_09 = pd.read_excel("s3://alpha-omppg/SFO/Data for Sonia/Notifications/09 2023.xls")
Nots_10 = pd.read_excel("s3://alpha-omppg/SFO/Data for Sonia/Notifications/10 2023.xls")
Nots_11 = pd.read_excel("s3://alpha-omppg/SFO/Data for Sonia/Notifications/11 2023.xls")
Nots_12 = pd.read_excel("s3://alpha-omppg/SFO/Data for Sonia/Notifications/12 2023.xls")
                         
# ['Notifications'] + [f"Nots_0{i}" for i in range(7,13)]
# print(*['Notifications','Nots_07','Nots_08','Nots_09','Nots_10','Nots_10','Nots_12'],sep=", ")

    # Concatenate the data to get 1 April 2014 - latest
Notifications = pd.concat([Notifications, Nots_04,Nots_05,Nots_06,Nots_07, Nots_08, Nots_09, Nots_10, Nots_11,Nots_12],
                    axis = 'index', 
                    ignore_index=True) 

#---------------------------------- Clean up Notifications data

Notifications.info()
Notifications.drop_duplicates("SFO_ID", inplace = True)
Notifications.shape

Notifications["NOMS_REGION_DESCRIPTION"].value_counts(dropna = False)
                                     
Notifications = Notifications[Notifications["NOMS_REGION_DESCRIPTION"] != 'Not Specified']
Notifications.shape

#---------------------------------- Import lookup data

Nots_Offence_Lkup = pd.read_excel("s3://alpha-omppg/SFO/Notifications_Offence_Lookup.xlsx")
Nots_Offence_Lkup.duplicated(subset = "SFO_OFFENCE_DESCRIPTION", keep=False).sum()
Nots_Offence_Lkup

#---------------------------------- Make uniform the entries in notifications data and lookup data

    # remove more than one blanks and remove trailing and starting blanks
Notifications['SFO_OFFENCE_DESCRIPTION'] = Notifications['SFO_OFFENCE_DESCRIPTION'].str.replace(r'\s+',' ',regex=True).str.strip()

Nots_Offence_Lkup['SFO_OFFENCE_DESCRIPTION'] =Nots_Offence_Lkup['SFO_OFFENCE_DESCRIPTION'].str.replace(r'\s+',' ',regex=True).str.strip()

#---------------------------------- Join the two

query =  """SELECT a.*, 
                   b.OFFENCE_SUMMARY
            FROM Notifications AS a LEFT JOIN Nots_Offence_Lkup AS b 
            ON  a.SFO_OFFENCE_DESCRIPTION = b.SFO_OFFENCE_DESCRIPTION
            """

# Notifications.drop(['OFFENCE_SUMMARY','OFFENCE_SUMMARY_2'],axis = 1, inplace=True)

Notifications = duckdb.sql(query).df()
Notifications .info()
Notifications.head()

#Notifications["OFFENCE_SUMMARY"].isna().sum()
#Notifications[Notifications["OFFENCE_SUMMARY"].isna()][['STAGE_12_DOCN_RECEIVED_ACTUAL','SFO_ID','SFO_OFFENCE_DESCRIPTION']]
#Notifications[Notifications["OFFENCE_SUMMARY"].isna()]['SFO_OFFENCE_DESCRIPTION'].value_counts(dropna=False).to_frame()
# 0

#---------------------------------- Tabulate

Nots_summary = Notifications.groupby(['OFFENCE_SUMMARY', Notifications['STAGE_12_DOCN_RECEIVED_ACTUAL'].dt.to_period('Q')]).size().unstack(fill_value=0)

Nots_summary 

Nots_summary .to_excel("Nots_Offence_by_qtr2b.xlsx",index_label=None)

#---------------------------------- ignore

NPS_mask = ~Notifications["NOMS_REGION_DESCRIPTION"].str.contains('CRC|Not Specified',case = False,na=False)

tabu = Notifications[NPS_mask].groupby(['OFFENCE_SUMMARY', Notifications[NPS_mask]['STAGE_12_DOCN_RECEIVED_ACTUAL'].dt.to_period('Q')]).size().unstack(fill_value=0)

tabu
tabu.to_excel("Nots_Offence_by_qtr.xlsx",index_label=None)

Notifications[NPS_mask].groupby(['OFFENCE_SUMMARY', Notifications[NPS_mask]['STAGE_12_DOCN_RECEIVED_ACTUAL'].dt.to_period('2Q')]).size().unstack(fill_value=0)

Notifications[NPS_mask].groupby(['OFFENCE_SUMMARY', Notifications[NPS_mask]['STAGE_12_DOCN_RECEIVED_ACTUAL'].dt.year]).size().unstack(fill_value=0)

Notifications[NPS_mask].\
    pivot_table(index = "OFFENCE_SUMMARY", 
                colums =
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


