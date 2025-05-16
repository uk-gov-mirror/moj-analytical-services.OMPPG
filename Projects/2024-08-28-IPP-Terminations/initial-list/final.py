""" 
GOAL: MATCH PPUD TO PROBATION CASELOAD DATA

By Eric Nyame, 28/08/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
# importlib.reload(Out_of_bounds_dates)
import prepareMatch
#importlib.reload(prepareMatch)
import openMatch
#importlib.reload(openMatch)
import TimeDiffs
import tariff_groups

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
        
#----------------------------------Import NOMIS data


deaths_in_community = pd.read_excel("final/Deaths-in-community-IPP-1-Apr-19-to-4-Oct-24.xlsx",skiprows=10)
deaths_in_community.head()

retain = ['COMMON_ID','FAMILY_NAME','DOS','RECALLED_OR_RELEASED','FIRST_REL_DATE','LATEST_REL_DATE','LATEST_RECALL','CURRENT_STATUS','TERM_ELIGIBLE_DATE','AUTO_TERM_DATE']

deaths_in_community.head()
deaths_in_community['Surname'] = deaths_in_community['Person on Probation - Name'].str.split(',').astype(str).apply(lambda x:x[0])
deaths_in_community['Surname'] = deaths_in_community['Surname'].str.strip().str.upper()

deaths_in_community['Forename'] = deaths_in_community['Person on Probation - Name'].str.split(',').astype(str).apply(lambda x:''.join(x[1:]))
deaths_in_community['Forename']= deaths_in_community['Forename'].str.strip().str.upper()

deaths_in_community= deaths_in_community.rename(columns={'Birth date':'DoB_probation'})
deaths_in_community= deaths_in_community.rename(columns={'NOMS No':'NOMS_No'})

ppud_matched_left['FAMILY_NAME'] = ppud_matched_left['FAMILY_NAME'].str.strip().str.upper()
ppud_matched_left['FIRST_NAMES'] = ppud_matched_left['FIRST_NAMES'].str.strip().str.upper()

strip_blanks(deaths_in_community)

# duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

# ppud_left =ppud_left.drop(['PN_TRIM','PN_LENGTH','PN_START','PN_END','NOMS_TRIM','NOMS_LENGTH','NOMS_START','NOMS_END','INIT'],axis=1)
ppud_matched_left['FNAME'] = ppud_matched_left['FAMILY_NAME']
ppud_matched_left = prepareMatch.prepareMatch(ppud_matched_left)
ppud_matched_left.head()
len(ppud_matched_left) # 8089

ppud_left.info()
deaths_in_community.info()
# deaths_in_community = deaths_in_community.drop('Latest Release Date',axis=1)

query = """SELECT a.COMMON_ID,
                  b.CRN as CRN_death
            FROM ppud_matched_left AS a 
            LEFT JOIN deaths_in_community AS b

            ON (       
                    (b.NOMS_No = a.NOMS_ID OR
                        b.NOMS_No = a.NOMS_TRIM OR
                        b.NOMS_No = a.NOMS_START OR
                        b.NOMS_No = a.NOMS_END OR
                        b.NOMS_No = a.PRISON_NUMBER OR
                        b.NOMS_No = a.PN_TRIM OR
                        b.NOMS_No = a.PN_START OR
                        b.NOMS_No = a.PN_END
                      ) AND b.NOMS_No IS NOT NULL
                      OR 
                      (
                        (a.FAMILY_NAME = b.Surname) AND 
                        (b.DoB_probation = a.DOB AND b.DoB_probation IS NOT NULL) AND
                        CONTAINS(b.Forename,a.FIRST_NAMES)
                      )
               )"""

matched = duckdb.sql(query).df()
matched = matched[~matched['CRN_death'].isna()]
matched.shape # 148
matched.head()
ppud_matched_left.shape

matched = pd.merge(ppud_matched_left,matched,how='left',on='COMMON_ID')

matched = matched.sort_values(['COMMON_ID','DOS','CRN_death'],na_position='first')
matched = matched.drop_duplicates(['COMMON_ID','DOS'],keep='last')
len(matched) # 8089, 8114
matched.head()

matched[matched['CRN_death'].notnull()]['CURRENT_STATUS'].value_counts()
matched.loc[matched['CRN_death'].notnull(),'CURRENT_STATUS'] = 'deceased'


matched['RELEASE_TYPE_DESCRIPTION'].value_counts()
matched[matched['RELEASE_TYPE_DESCRIPTION'] =='Death']['CURRENT_STATUS'].value_counts() # fine
matched[matched['RELEASE_TYPE_DESCRIPTION'] =='Compassionate']['CURRENT_STATUS'].value_counts()# fine
matched.loc[matched['RELEASE_TYPE_DESCRIPTION'] == 'Compassionate','CURRENT_STATUS'] = 'Compassionate'
matched[matched['RELEASE_TYPE_DESCRIPTION'] == 'Deportation']['CURRENT_STATUS'].value_counts() # fine

matched = matched.drop(['PN_TRIM','PN_LENGTH','PN_START','PN_END','NOMS_TRIM','NOMS_LENGTH','NOMS_START','NOMS_END','INIT','CRN_death','FNAME'],axis=1)

matched['CURRENT_STATUS'].value_counts()

matched.to_excel('ppud_matched_left_latest.xlsx',index=False)
matched.to_parquet('output-data/ppud_matched_left_latest.parquet')
