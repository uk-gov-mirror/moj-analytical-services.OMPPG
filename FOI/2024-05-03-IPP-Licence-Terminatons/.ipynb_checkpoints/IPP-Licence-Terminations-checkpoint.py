# QUESTION -
 """ 
 Please can you please provide me with the following information: 
1)How may people serving a) IPP sentences and b) DPP sentences have had their sentences terminated? 
 """

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib

import re

from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
# from my_log import my_log
import Out_of_bounds_dates
importlib.reload(Out_of_bounds_dates)
import prepareMatch
importlib.reload(prepareMatch)
import openMatch
importlib.reload(openMatch)
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

# Import Terminations Data
terminations_to_31Dec2023 = pd.read_excel("s3://alpha-omppg/FOI/2024-05-03-IPP-Licence-Terminatons/IPPDPP Terminations Agreed up to 31 Dec 2023.xlsx")
terminations_to_31Dec2023.info()
terminations_to_31Dec2023.head()

len(terminations_to_31Dec2023) # 281

#-Remove Test cases
    # Check 'test' cases and remove
terminations_to_31Dec2023[terminations_to_31Dec2023['FAMILY_NAME'].str.contains('Test',case = False,na = False)][['PRISON_NUMBER','FAMILY_NAME','FIRST_NAMES']]

terminations_to_31Dec2023[terminations_to_31Dec2023['FIRST_NAMES'].str.contains('Test',case = False,na = False)][['PRISON_NUMBER','FAMILY_NAME','FIRST_NAMES']]

terminations_to_31Dec2023[terminations_to_31Dec2023['PRISON_NUMBER'].str.contains('Test',case = False,na = False)][['PRISON_NUMBER','FAMILY_NAME','FIRST_NAMES','PRISON_NUMBER']]


Test_Case_Mask =  (   (terminations_to_31Dec2023['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (terminations_to_31Dec2023['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (terminations_to_31Dec2023['FILE_REFERENCE'] != 'T18122')

# terminations_to_31Dec2023[Test_Case_Mask][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 3 cases

terminations_to_31Dec2023 = terminations_to_31Dec2023[~Test_Case_Mask]
terminations_to_31Dec2023.shape # 281,19

    # Check 'case' cases and remove
terminations_to_31Dec2023[terminations_to_31Dec2023['FAMILY_NAME'].str.contains('Case',case = False,na = False)][['PRISON_NUMBER','FAMILY_NAME','FIRST_NAMES']] # 0

terminations_to_31Dec2023[terminations_to_31Dec2023['FIRST_NAMES'].str.contains('Case',case = False,na = False)][['PRISON_NUMBER','FAMILY_NAME','FIRST_NAMES']] # 0

    # Check 'digit' cases - these are normally good and shoulbe untouched
terminations_to_31Dec2023[terminations_to_31Dec2023['FAMILY_NAME'].str.contains(r'\d')][['PRISON_NUMBER','FAMILY_NAME','FIRST_NAMES']] 
terminations_to_31Dec2023[terminations_to_31Dec2023['FIRST_NAMES'].str.contains(r'\d')][['PRISON_NUMBER','FAMILY_NAME','FIRST_NAMES']] 

#---------------------------------- Drop duplicates#
# Remove duplicate terminations_to_31Dec2023 from terminations_to_31Dec2023 data

terminations_to_31Dec2023[terminations_to_31Dec2023.duplicated(['REVIEW_ID'], keep=False)] # none

# tabulate

terminations_to_31Dec2023['CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

(terminations_to_31Dec2023['ACTUAL'].dt.year).value_counts(dropna=False)
