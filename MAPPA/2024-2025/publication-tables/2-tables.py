""" 
GOAL: PRODUCE MAPPA TABLES FOR PUBLICATION
"""

#---------------------------------- Import Packages

import pandas as pd
# from pandas.api.types import CategoricalDtype
import numpy as np
import os
import sys
# import duckdb
# import importlib

from itables import show

# openpyxl
# from openpyxl import Workbook, load_workbook
# from openpyxl.styles import Font, Alignment
# from openpyxl.utils import get_column_letter

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

# sys.path.append('/home/jovyan/OMPPG/Macro Library')
# from my_log import my_log
# import Out_of_bounds_dates
# import prepareMatch
# importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
# import TimeDiffs

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
        
        # Period variables

mappa_latest = pd.read_excel("../Table All Areas Source.xlsx")
mappa_latest.head()
totals = mappa_latest.sum(numeric_only=True).reset_index()
totals
totals.info()
totals.columns = ['Item','Count']

totals['Item'].tolist()

# Table1

table1 = totals[totals['Item'].isin(table1_values)].copy()
table1.loc[len(table1)] = ['CAT3L1', None]
table1['Item'] =table1['Item'].astype(CategoricalDtype(categories=table1_values, ordered=True))

table1.groupby('Item')['Count'].sum().reset_index()

# Table3 - RSO national

# Table 4
table4 = totals[totals['Item'].isin(table4_values)].copy()
table4 = table4.set_index('Item').T
table4 = table4[table4_values]
table4

# Table 5a
table5a = totals[totals['Item'].isin(['CAT1CON','CAT1CAUT'])].copy()
table5a = table5.set_index('Item').T
table5a

# Table 5b
table5b_values = ['CAT1L1CON', 'CAT1L1CAUT', 'CAT1L2CON', 'CAT1L2CAUT', 'CAT1L3CON','CAT1L3CAUT']

table5b = totals[totals['Item'].isin(table5b_values)].copy()
table5b['Item'] =table5b['Item'].astype(CategoricalDtype(categories=table5b_values, ordered=True))

table5b.groupby('Item')['Count'].sum().reset_index()

# Table6
table6_values = ['SOPOGRANT','NOGRANT','FTOGRANT']

table6 = totals[totals['Item'].isin(table6_values)].copy()
table6.set_index('Item').T

# Table7a
table7a_values = ['LEVEL2BREACHT7','LEVEL3BREACHT7','BREACHTOTALT7',]

table7a = totals[totals['Item'].isin(table7a_values)].copy()
table7a.set_index('Item').T

# Table7b
table7b_values =['BREACHTOTALT7', 'LEVEL2BREACHT7','LEVEL3BREACHT7','CAT1L2LICBREACH',
'CAT1L3LICBREACH',  'CAT2L2LICBREACH','CAT2L3LICBREACH','CAT3L2LICBREACH','CAT3L3LICBREACH',
'CAT4L2LICBREACH', 'CAT4L3LICBREACH']

table7b = totals[totals['Item'].isin(table7b_values)].copy()
table7b
table7b['Item'] =table7b['Item'].astype(CategoricalDtype(categories=table7b_values, ordered=True))

table7b.groupby('Item')['Count'].sum().reset_index()

# Table7c
table7c_values =['CAT1L2SOPOBREACH','CAT1L3SOPOBREACH', 'SOPOTOTALT7']

table7c = totals[totals['Item'].isin(table7c_values)].copy()
table7c
table7b['Item'] =table7b['Item'].astype(CategoricalDtype(categories=table7b_values, ordered=True))
table7c.set_index('Item').T

# Table8
table8_values =['LEVEL1SFOCHARGE', 'LEVEL2SFOCHARGE', 'LEVEL3SFOCHARGE','TOTALSFOCHARGE']
 

table8 = totals[totals['Item'].isin(table8_values)].copy()
table8
table8['Item'] =table8['Item'].astype(CategoricalDtype(categories=table8_values, ordered=True))
table8.groupby('Item')['Count'].sum().reset_index().T
    
]
# Table9a
table9a_values =['CAT1L1SFO','CAT1L2SFO', 'CAT1L3SFO', 'CAT2L1SFO', 'CAT2L2SFO', 'CAT2L3SFO', 'CAT3L2SFO', 'CAT3L3SFO', 'CAT4L1SFO','CAT4L2SFO', 'CAT4L3SFO']
 

table9a = totals[totals['Item'].isin(table9a_values)].copy()
table9a


# Table9b
table9b_conv_values =['CAT1L1SFOCONV','CAT1L2SFOCONV', 'CAT1L3SFOCONV', 'CAT2L1SFOCONV',
 'CAT2L2SFOCONV', 'CAT2L3SFOCONV', 'CAT3L2SFOCONV', 'CAT3L3SFOCONV','CAT4L1SFOCONV',
 'CAT4L2SFOCONV', 'CAT4L3SFOCONV']

table9b_conv= totals[totals['Item'].isin(table9b_conv_values)].copy()
table9b_conv = table9b_conv.rename(columns={'Count':'Convictions'})

table9b_conv['Item']=table9b_conv['Item'].map(table9b_conv_dict)

#-------------------------
table9b_still_values =['CAT1L1SFOCHARGE', 'CAT1L2SFOCHARGE', 'CAT1L3SFOCHARGE',
 'CAT2L1SFOCHARGE', 'CAT2L2SFOCHARGE', 'CAT2L3SFOCHARGE',
 'CAT3L2SFOCHARGE', 'CAT3L3SFOCHARGE','CAT4L1SFOCHARGE', 'CAT4L2SFOCHARGE', 'CAT4L3SFOCHARGE']

table9b_still = totals[totals['Item'].isin(table9b_still_values)].copy()
table9b_still = table9b_still.rename(columns={'Count':'StillCharged'})
table9b_still['Item']=table9b_still['Item'].map(table9b_still_dict)

#-----------------
table9b_other_values =['CAT1L1SFOOTHER', 'CAT1L2SFOOTHER', 'CAT1L3SFOOTHER',
 'CAT2L1SFOOTHER', 'CAT2L2SFOTHER', 'CAT2L3SFOOTHER', 'CAT3L2SFOOTHER',
 'CAT3L3SFOOTHER', 'CAT4L1SFOOTHER', 'CAT4L2SFOOTHER', 'CAT4L3SFOOTHER']

table9b_other = totals[totals['Item'].isin(table9b_other_values)].copy()
table9b_other = table9b_other.rename(columns={'Count':'Other'})
table9b_other['Item']=table9b_other['Item'].map(table9b_other_dict)

#Join

(
    table9b_conv
    .merge(table9b_still, on='Item', how='inner')
    .merge(table9b_other, on='Item', how='inner')
)
