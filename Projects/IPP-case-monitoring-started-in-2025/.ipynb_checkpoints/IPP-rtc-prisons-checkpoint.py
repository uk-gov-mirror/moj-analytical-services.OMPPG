""" 
GOAL: PRODUCE RECALL TABLES FOR OMSQ.
By Eric Nyame, 17/04/2024
"""

#---------------------------------- Import Packages

import pandas as pd
from pandas.api.types import CategoricalDtype
import numpy as np
import sys
import duckdb
import importlib
import os

# openpyxl
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
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

# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #
        

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# ------------------------------------------
# Database
#-------------------------------------------

sheet_name = 'Sheet1'
cols_to_import = 'A:AG'

dbase = pd.read_excel("s3://alpha-omppg/Projects/IPP-case-monitoring-started-in-2025/monitoring-database.xlsx",sheet_name=sheet_name,usecols =cols_to_import,skiprows=3)

dbase.head()

temp_dbase = dbase[["NOMIS No.","Surname","First Name"]].copy()

temp_dbase= temp_dbase.rename(columns={'NOMIS No.':'NOMS_ID',
                            'First Name':'First_Names'})
temp_dbase.columns = temp_dbase.columns.str.upper()
temp_dbase = temp_dbase[temp_dbase['NOMS_ID'].notna()]
temp_dbase.head()

len(temp_dbase) # 22

# ------------------------------------------
# Recalls
#-------------------------------------------

recalls = pd.read_excel("s3://alpha-omppg/Projects/IPP-case-monitoring-started-in-2025/IPP_Recalls_July-August-2025.xlsx")

recalls['LICENCE_REVOKE_DATE'] = recalls['LICENCE_REVOKE_DATE'].dt.normalize()
recalls['RTC_DATE'] = recalls['RTC_DATE'].dt.normalize()

recalls['CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION'].value_counts(dropna=False) # IPP or DPP
recalls.head()

# duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")
query1 = """SELECT a.*,
               b.LICENCE_REVOKE_DATE,
               b.RTC_DATE,
               b.FILE_REFERENCE,
               b.PRISON_NUMBER,
               b.GENDER,
               b.PROBATION_AREA_DESCRIPTION,
               b.CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION	 AS CUST_TYPE_PROPER,
               b.CUSTODY_TYPE_DESCRIPTION,
               b.CURRENT_ESTABLISHMENT_DESCRIPTION as RECALL_CURRENT_ESTABLISHMENT,     
               
        FROM temp_dbase AS a LEFT JOIN recalls AS b
        On (
            a.NOMS_ID = b.NOMS_ID
           )"""

matched = duckdb.sql(query1).df()
len(matched) # 22
matched.head()

temp_dbase = matched.copy()

# ------------------------------------------
# RTC prisons
#-------------------------------------------

rtc_pris = pd.read_excel("s3://alpha-omppg/Projects/IPP-case-monitoring-started-in-2025/MIS-National-Receptions-July-August-2025.xlsx")

rtc_pris= rtc_pris.rename(columns={'Movement Reason':'Movement_Reason',
                            'Movement Type':'Movement_Type',
                            'Mov Time':'Mov_Time',
                            'Prison_Number':'PRISON_NUMBER'})
rtc_pris.head()
rtc_pris['Movement Type'].value_counts(dropna=False)

# duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")
query2 = """SELECT a.*,
               b.To AS RTC_PRISON,
               b.Movement_Reason,
               b.Movement_Type,
               b.From,
               b.Mov_Time
        FROM temp_dbase AS a LEFT JOIN rtc_pris AS b
        On (
            (a.NOMS_ID = b.NOMS_ID AND a.NOMS_ID IS NOT NULL ) OR 
            (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)
           ) AND
           (a.LICENCE_REVOKE_DATE <= b.Mov_Time)"""

matched = duckdb.sql(query2).df()
len(matched) # 32

matched = matched.sort_values(['NOMS_ID','LICENCE_REVOKE_DATE','Mov_Time'])
matched[matched.duplicated(['NOMS_ID'],keep=False)]

matched = matched.drop_duplicates(['NOMS_ID','LICENCE_REVOKE_DATE'])

len(matched) # 22
matched[matched['NOMS_ID'].isin(['A4718AE','A6817AK','A9098AQ'])][['NOMS_ID','SURNAME','Mov_Time']]

matched.head()

temp_dbase = matched.copy()

# ------------------------------------------
# RARR considered
#-------------------------------------------

rarr_considered = pd.read_excel("s3://alpha-omppg/Projects/IPP-case-monitoring-started-in-2025/IPP-RARR-July_August-2025.xlsx")

rarr_considered.head()

rarr_considered['TITLE'].value_counts(dropna=False)

rarr_considered['DECISION'] = 'Release'
rarr_considered.loc[rarr_considered['TITLE'] != '10 - Issue RARR Decision','DECISION']='No Release'

rarr_considered['DECISION'].value_counts(dropna=False)

rarr_considered = rarr_considered.rename(columns={'ACTUAL':'RARR_DATE'})

rarr_considered.head()

# duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")
query3 = """SELECT a.*,
               b.DECISION,
               b.RARR_DATE
               
        FROM temp_dbase AS a LEFT JOIN rarr_considered AS b
        On (
            (a.NOMS_ID = b.NOMS_ID AND a.NOMS_ID IS NOT NULL ) OR 
            (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)
           ) AND
           (a.LICENCE_REVOKE_DATE <= b.RARR_DATE)"""

matched = duckdb.sql(query3).df()
len(matched) # 22

matched = matched.drop_duplicates(['NOMS_ID','LICENCE_REVOKE_DATE'])

matched.head()

temp_dbase = matched.copy()

# ------------------------------------------
# REFERRED CASES TO THE PB
#-------------------------------------------

gpp_referred = pd.read_excel("s3://alpha-omppg/Projects/IPP-case-monitoring-started-in-2025/IPP-referrals-July-August-2025.xlsx")

gpp_referred.head()

gpp_referred['REVIEW_STATUS_DESCRIPTION'].value_counts(dropna=False)

gpp_referred = gpp_referred.rename(columns={'ACTUAL':'GPP_REFERRAL_DATE'})

gpp_referred.head()

# duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")
query4 = """SELECT a.*,
               b.GPP_REFERRAL_DATE,
               b.REVIEW_STATUS_DESCRIPTION AS GPP_REVIEW_STATUS
               
        FROM temp_dbase AS a LEFT JOIN gpp_referred AS b
        On (
            (a.NOMS_ID = b.NOMS_ID AND a.NOMS_ID IS NOT NULL ) OR 
            (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)
           ) AND
           (a.LICENCE_REVOKE_DATE <= b.GPP_REFERRAL_DATE)"""

matched = duckdb.sql(query4).df()
len(matched) # 22

matched = matched.drop_duplicates(['NOMS_ID','LICENCE_REVOKE_DATE'])

matched.head()

temp_dbase = matched.copy()

# ------------------------------------------
# PB DIRECTIONS
#-------------------------------------------

directions = pd.read_excel("s3://alpha-omppg/Projects/IPP-case-monitoring-started-in-2025/IPP-PB-Directions-July-August-2025.xlsx")

directions.info()
directions.head()
directions['DIRECTION_DATE']  = pd.to_datetime(directions['DIRECTION_DATE'],errors='coerce')
directions['DIRECTION_DATE'] = directions['DIRECTION_DATE'].dt.normalize()

# duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")
query5 = """SELECT a.*,
               b.DIRECTION_DATE,
               
        FROM temp_dbase AS a LEFT JOIN directions AS b
        On (
            (a.NOMS_ID = b.NOMS_ID AND a.NOMS_ID IS NOT NULL ) OR 
            (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)
           ) AND
           (a.LICENCE_REVOKE_DATE <= b.DIRECTION_DATE)"""

matched = duckdb.sql(query5).df()
len(matched) # 28

matched = matched.drop_duplicates(['NOMS_ID','LICENCE_REVOKE_DATE'])

matched['DIRECTION'] = ''
matched.loc[matched['DIRECTION_DATE'].notna(),'DIRECTION'] = 'Yes'
matched.head()

temp_dbase = matched.copy()

temp_dbase.to_excel("prelims.xlsx",index=False)

