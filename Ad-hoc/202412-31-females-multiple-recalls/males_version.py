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

rec_up_to_2009 = pd.read_excel("s3://alpha-omppg/data-central/recalls/Recalls_up_to_2009.xls")
rec_2010_2011 = pd.read_excel("s3://alpha-omppg/data-central/recalls/Recalls_2010_2011.xls")
rec_2012_2013 = pd.read_excel("s3://alpha-omppg/data-central/recalls/Recalls_2012_2013.xls")
rec_2014_2016 = pd.read_excel("s3://alpha-omppg/data-central/recalls/Recalls_2014_2016.xls")
rec_2017_2018 = pd.read_excel("s3://alpha-omppg/data-central/recalls/Recalls_2017_2018.xls")
rec_2019_2020 = pd.read_excel("s3://alpha-omppg/data-central/recalls/Recalls_2019_2020.xls")
rec_2021_2022 = pd.read_excel("s3://alpha-omppg/data-central/recalls/Recalls_2021_2022.xls")
rec_2023 = pd.read_excel("s3://alpha-omppg/data-central/recalls/Recalls_2023.xls")
rec_2024 = pd.read_excel("s3://alpha-omppg/data-central/recalls/Recalls_2024.xls")


for name in [name for name, obj in globals().items() if isinstance(obj, pd.DataFrame)]:
    print(name,end=',')

recalls = pd.concat([rec_up_to_2009,
                     rec_2010_2011,
                     rec_2012_2013,
                     rec_2014_2016,
                     rec_2017_2018,
                     rec_2019_2020,
                     rec_2021_2022,
                     rec_2023,
                     rec_2024,],ignore_index=True)

del rec_up_to_2009,rec_2010_2011,rec_2012_2013,rec_2014_2016,rec_2017_2018,rec_2019_2020,rec_2021_2022,rec_2023,rec_2024

recalls.head()
recalls.info()

strip_blanks(recalls)

recalls.GENDER.value_counts(dropna=False)
recalls.loc[recalls['GENDER'] == 'F ( Was M )','GENDER'] = 'F'
recalls.loc[recalls['GENDER'] == 'M ( Was F )','GENDER'] = 'M'

recalls[recalls['GENDER']=='#'].head()

# Determine recall number for each combination of date of sentence and licence revocation date

recalls['DOS'].isna().sum() # 180 cases with missing date of sentece, good
recalls['LICENCE_REVOKE_DATE'].isna().sum() # 0
recalls['NOMS_ID'].isna().sum() # 40055
recalls['FILE_REFERENCE'].isna().sum() # 2134
recalls['PRISON_NUMBER'].isna().sum() # 5

# check duplicates
recalls.duplicated(['PRISON_NUMBER','DOS','LICENCE_REVOKE_DATE'],keep='first').sum() # 728
recalls.duplicated(['PRISON_NUMBER','LICENCE_REVOKE_DATE'],keep='first').sum() # 742

    # remove duplicate prison number and licence revoke date
recalls = recalls.sort_values(['PRISON_NUMBER','LICENCE_REVOKE_DATE'])

recalls = recalls.drop_duplicates(['PRISON_NUMBER','LICENCE_REVOKE_DATE'])
recalls.shape

    # count the recall number for each combination of prison number, dos and licence revoke date
recalls.info()

recalls = recalls.sort_values(['PRISON_NUMBER','DOS','LICENCE_REVOKE_DATE'])

recalls['RECALL_NUMBER'] = recalls.groupby(['PRISON_NUMBER','DOS']).cumcount() + 1
recalls['RECALL_TOTAL_SENTENCE'] = recalls.groupby(['PRISON_NUMBER','DOS']).transform('size')
recalls['RECALL_TOTAL_INDIVIDUAL'] = recalls.groupby(['PRISON_NUMBER']).transform('size')

recalls['IN_LAST_12_MONTHS'] = 0
recalls.loc[recalls['LICENCE_REVOKE_DATE'] >= pd.Timestamp(2023,12,1),'IN_LAST_12_MONTHS'] = 1

recalls['IN_LAST_12_MONTHS'] = recalls.groupby(['PRISON_NUMBER','DOS'])['IN_LAST_12_MONTHS'].transform('max')

retain = ['FILE_REFERENCE','FAMILY_NAME','DOS','LICENCE_REVOKE_DATE','RECALL_NUMBER','RECALL_TOTAL_SENTENCE','RECALL_TOTAL_INDIVIDUAL','IN_LAST_12_MONTHS','RECALL_TYPE_DESCRIPTION']

recalls = recalls[retain +[col for col in recalls.columns if col not in retain]]

recalls[recalls['IN_LAST_12_MONTHS'] > 0].head(100)

# Keep only the second fixed-term recalls
keep_cond = (recalls['RECALL_TOTAL_SENTENCE'] > 1) & (recalls['IN_LAST_12_MONTHS'] > 0)
recalls_2 = recalls[keep_cond] 

recalls_2 = recalls_2.sort_values(['PRISON_NUMBER','DOS','LICENCE_REVOKE_DATE'])
recalls_2.head(100)


recalls_2.to_excel("multiple_recalls_last_12_mths.xlsx",engine='xlsxwriter')
