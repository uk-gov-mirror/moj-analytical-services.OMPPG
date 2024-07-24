""" 
GOAL: Number of standard recalls in the last 12 months, 
      ideally for those under 12 months sentence.
      
By Eric Nyame, 29/02/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
# print(duckdb.__version__)
import importlib

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
# from my_log import my_log
import Out_of_bounds_dates
import prepareMatch
importlib.reload(prepareMatch)
import openMatch
importlib.reload(openMatch)
import TimeDiffs
import tariff_groups
importlib.reload(tariff_groups)

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

# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x) #
        
#----------------------------------Set globals

yy = 23 # year as yy
mm = 12
dd = 31

year = 2023
quarter = 4 

#----------------------------------Import data

rec1 = pd.read_sas("s3://alpha-omppg/Recalls/Final Data/SAS/recalls_final_2022q4.sas7bdat", encoding='latin1')
rec2 = pd.read_sas("s3://alpha-omppg/Recalls/Final Data/SAS/recalls_final_2023q1.sas7bdat", encoding='latin1')
rec3 = pd.read_sas("s3://alpha-omppg/Recalls/Final Data/SAS/recalls_final_2023q2.sas7bdat", encoding='latin1')
rec4 = pd.read_sas("s3://alpha-omppg/Recalls/Final Data/SAS/recalls_final_2023q3.sas7bdat", encoding='latin1')

rec = pd.concat([rec1,rec2,rec3,rec4], axis = 0, ignore_index = True)


rec.columns = rec.columns.str.upper()

rec.info()

output = rec['RECALL_TYPE_DESCRIPTION'].value_counts(dropna=False)

# output.to_excel("output.xlsx")


# Individuals - standard ORA
ORA_type = ['Standard Recall - Under 12 Months','Emergency - Under 12 Months','Standard - HDC Non-Curfew - Under 12 Months','Emergency - HDC Non-Curfew - Under 12 Months']
ORA_std = rec[rec['RECALL_TYPE_DESCRIPTION'].isin(ORA_type)].copy()
len(ORA_std)

ORA_std[ORA_std['NOMS_ID'].isna()]

ORA_std_nodups = ORA_std.drop_duplicates('NOMS_ID', keep='first')

len(ORA_std_nodups)

ORA_std['Year_Quarter'] = ORA_std['LICENCE_REVOKE_DATE'].dt.to_period('Q')

ORA_std.groupby('Year_Quarter').size()
ORA_std.groupby('FURTHER_CHARGE').size()
output2 = ORA_std_nodups['RECALL_TYPE_DESCRIPTION'].value_counts(dropna=False)

# output2.to_excel("output2.xlsx")

ORA_std['RECALLNUM'] = ORA_std.groupby('NOMS_ID').cumcount() + 1


# Duplicates
Dups = ORA_std[ORA_std.duplicated('NOMS_ID', keep=False)]
Dups.head()
Dups.to_excel('Dups.xlsx')
