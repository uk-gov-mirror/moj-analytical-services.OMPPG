""" 
GOAL: PRODUCE RECALL TABLES FOR OMSQ.
By Eric Nyame, 17/04/2024
"""

#---------------------------------- Import Packages

import pandas as pd
#from pandas.api.types import CategoricalDtype
import numpy as np
import sys
import duckdb
import importlib

# openpyxl
#from openpyxl import Workbook, load_workbook
#from openpyxl.styles import Font, Alignment
#from openpyxl.utils import get_column_letter

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
# from my_log import my_log
import Out_of_bounds_dates
import prepareMatch
# importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
import TimeDiffs

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
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x) #

        
ecsl_releases = pd.read_excel('ECSL_data.xlsx')
recalls = pd.read_excel('PPUD_recalls_october2023_to_12_Jul2024.xls')

ecsl_releases.head()
recalls.head()
ecsl_releases.info()
recalls.info()

strip_blanks(ecsl_releases)
strip_blanks(recalls)


# check duplicates
ecsl_releases[ecsl_releases.duplicated(['NOMS','Date'])] # none
len(ecsl_releases) # 10083


#---------------------------------- Match to A&O Dataset on either NOMIS number, Prison Number or Name and DOB

duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query = """SELECT DISTINCT a.*, 
                            b.LICENCE_REVOKE_DATE,
                            b.NOMS_ID AS NOMS_ID_PPUD, 
                            b.ECSL_CRD,
                            b.LICENCE_START,
                            b.TYPE_OF_LICENCE_DESCRIPTION,
                            b.PRISON_NUMBER
                            
                    FROM ecsl_releases AS a LEFT JOIN recalls AS b
                    
                    ON a.Date <= b.LICENCE_REVOKE_DATE AND 
                      (a.NOMS = b.NOMS_ID OR
                       a.NOMS = b.NOMS_TRIM OR
                       a.NOMS = b.NOMS_START OR
                       a.NOMS = b.NOMS_END OR
                       a.NOMS = b.PRISON_NUMBER OR
                       a.NOMS = b.PN_TRIM OR
                       a.NOMS = b.PN_START OR
                       a.NOMS = b.PN_END)"""

matched = duckdb.sql(query).df()
len(matched) # 11783

# deduplicate
matched = matched.sort_values(by=['NOMS','Date','LICENCE_REVOKE_DATE'])

#matched[matched.duplicated(['NOMS','Date'],keep=False)][['NOMS','Date','Last Name','LICENCE_REVOKE_DATE']].head(10)

matched = matched.sort_values(by=['NOMS','Date','LICENCE_REVOKE_DATE'])
matched2 = matched.drop_duplicates(['NOMS','Date'])
len(matched2)
# check
matched2[matched2['NOMS'].isin(['A0017CF','A0024EF','A0026AL'])][['NOMS','Date','Last Name','LICENCE_REVOKE_DATE']]

matched2.head()



window_condition = matched2['LICENCE_REVOKE_DATE'].dt.date <= matched2['CRD']
sum(window_condition)
2166

matched2['Within_window'] = (matched2['LICENCE_REVOKE_DATE'].dt.date <= matched2['CRD'])

matched2.head()

matched2.to_excel('ECSL_Releases_with_Recalls.xlsx',index=False)
