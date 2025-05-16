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

cload = pd.read_excel("RARR_Whole_Caseload_2024_11_27.xlsx")
nload = pd.read_csv("DAO_2024_11_27.csv")
ftr = pd.read_excel("ftr_recent.xls")

cload.head()
nload.head()
ftr.head()
cload.info()

nload['IMPRISONMENT_STATUS_CATEGORY'].value_counts(dropna=False)
nload['SENTENCE_LENGTH_BANDED'].value_counts(dropna=False)

cload['Order Category\n'].value_counts()
cload = cload.rename(columns ={'NOMS No':'NOMIS_NO'})
ftr = ftr.rename(columns ={'NOMS_ID':'NOMIS_NO'})

ftr = ftr.sort_values("LICENCE_REVOKE_DATE", ascending=False)
ftr = ftr.drop_duplicates("NOMIS_NO")

ftr['LICENCE_REVOKE_DATE'] = ftr['LICENCE_REVOKE_DATE'].dt.normalize()
ftr['RTC_DATE'] = ftr['RTC_DATE'].dt.normalize()

cload = cload[cload['Order Category\n'] == 'Pre-Release']
len(cload) # 77426

(cload['NOMIS_NO'].isna()).sum() # 0
(nload['NOMIS_NO'].isna()).sum() # 0

cload2 =  pd.merge(cload, nload[['IMPRISONMENT_STATUS_CATEGORY','SENTENCE_LENGTH_BANDED','SENTENCE_START_TO_END_DAYS','SecCatSummary','SED','MAIN_OFFENCE_DESCRIPTION','PED','LAST_MOVEMENT_REASON','LAST_MOVEMENT_TYPE','NOMIS_NO']], how ='left',on='NOMIS_NO')

cload2 =  pd.merge(cload2, ftr[['LICENCE_REVOKE_DATE','RTC_DATE','RELEASE_BEFORE_RECALL','RECALL_TYPE_DESCRIPTION','DOS','LICENCE_END','LICENCE_START','NOMIS_NO']], how ='left',on='NOMIS_NO')

len(cload2) # 77426

cload2.head()

cload2.to_excel("RARR_cohort.xlsx")

# conditions - Andy

m1 = (cload2["Returned To Custody?"] == 'Recalled')
m2 = (cload2["Required Info"] == 'L1')
m3 = (cload2["RSR Score (CsA)"] < 3)


pd.Timestamp.today()
m3['HOW_LONG'] =  (cload3["PED"].isna()) 
cload3 = cload2[m1 & m2 & m3]
len(cload3) # 10180
cload3.head()

m4 = (cload3["LICENCE_REVOKE_DATE"].isna()) # not ftr
m5 = (cload3["PED"].isna()) # PED missing is not extended determinates

# PED missing is not extended determinates
cload3['RECALL_TYPE_DESCRIPTION'].value_counts(dropna=False)
cload3['SENTENCE_LENGTH_BANDED'].value_counts(dropna=False)
cload3[m4 & m5]['LAST_MOVEMENT_REASON'].value_counts(dropna=False)
cload3[m4 & m5]['LAS'].value_counts(dropna=False)
cload3.pivot_table(index =['Order Category\n',])

cload3[cload3['SENTENCE_LENGTH_BANDED'].isna()].head(15)
