""" 
GOAL: ATTEMPT PRODUCE ALL IPPs/DPPs BY PPUD AS AT 16 AUGUST 2024

By Eric Nyame, 28/08/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
# import importlib

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
# import Out_of_bounds_dates
import prepareMatch
#importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
import TimeDiffs
# import tariff_groups

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

# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #

# IMPORT RELEASES AND RECALLS DATA
female_recalls = pd.read_excel("female_recalls_up_to_30Nov2024.xls")

strip_blanks(female_recalls)

female_recalls.GENDER.value_counts(dropna=False)

# Determine recall number for each combination of date of sentence and licence revocation date

female_recalls['DOS'].isna().sum() # 10 cases with missing date of sentece, good
female_recalls['LICENCE_REVOKE_DATE'].isna().sum() # 0
female_recalls['NOMS_ID'].isna().sum() # 1854
female_recalls['FILE_REFERENCE'].isna().sum() # 179
female_recalls['PRISON_NUMBER'].isna().sum() # 0

# check duplicates
female_recalls.duplicated(['PRISON_NUMBER','DOS','LICENCE_REVOKE_DATE'],keep='first').sum() # 10
female_recalls.duplicated(['PRISON_NUMBER','LICENCE_REVOKE_DATE'],keep='first').sum() # 13

    # remove duplicate prison number and licence revoke date
female_recalls = female_recalls.sort_values(['PRISON_NUMBER','LICENCE_REVOKE_DATE'])

female_recalls = female_recalls.drop_duplicates(['PRISON_NUMBER','LICENCE_REVOKE_DATE'])
female_recalls.shape

    # count the recall number for each combination of prison number, dos and licence revoke date
female_recalls.info()

female_recalls = female_recalls.sort_values(['PRISON_NUMBER','DOS','LICENCE_REVOKE_DATE'])

female_recalls['RECALL_NUMBER'] = female_recalls.groupby(['PRISON_NUMBER','DOS']).cumcount() + 1
female_recalls['RECALL_TOTAL_SENTENCE'] = female_recalls.groupby(['PRISON_NUMBER','DOS']).transform('size')
female_recalls['RECALL_TOTAL_INDIVIDUAL'] = female_recalls.groupby(['PRISON_NUMBER']).transform('size')

female_recalls['IN_LAST_12_MONTHS'] = 0
female_recalls.loc[female_recalls['LICENCE_REVOKE_DATE'] >= pd.Timestamp(2023,12,1),'IN_LAST_12_MONTHS'] = 1

female_recalls['IN_LAST_12_MONTHS'] = female_recalls.groupby(['PRISON_NUMBER','DOS'])['IN_LAST_12_MONTHS'].transform('max')

retain = ['FILE_REFERENCE','FAMILY_NAME','DOS','LICENCE_REVOKE_DATE','RECALL_NUMBER','RECALL_TOTAL_SENTENCE','RECALL_TOTAL_INDIVIDUAL','IN_LAST_12_MONTHS','RECALL_TYPE_DESCRIPTION']

female_recalls = female_recalls[retain +[col for col in female_recalls.columns if col not in retain]]

female_recalls[female_recalls['IN_LAST_12_MONTHS'] > 0].head(100)

# Keep only the second fixed-term recalls
keep_cond = (female_recalls['RECALL_TOTAL_SENTENCE'] > 1) & (female_recalls['IN_LAST_12_MONTHS'] > 0)
female_recalls_2 = female_recalls[keep_cond] 

female_recalls_2 = female_recalls_2.sort_values(['PRISON_NUMBER','DOS','LICENCE_REVOKE_DATE'])
female_recalls_2.head(100)


female_recalls_2.to_excel("female_multiple_recalls_last_12_mths.xlsx",engine='xlsxwriter')