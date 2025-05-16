""" 
GOAL: IDENTIFY DPP CASES IN THE PROBATION CASELOAD DATA PROBATION STATISTICS TEAM.
By Eric Nyame, 04/04/2025
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

# function to remove trailing and leading blanks

def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Function to identify where bad datetime value is. Pass in the 

def dateOutOfBoundsColumn(dataset,value): # pass in the out-of-bounds date
    for col in dataset.columns:
        # Convert the column to string and check if any value contains the problematic date substring
        if dataset[col].astype(str).str.contains(value).any():
            hmm = dataset[col].astype(str).str.contains(value)
            cols_to_keep = ['NOMIS_ID','surname','EXTRACTDATE',col]
            display(dataset[hmm][cols_to_keep])
            break

# dateOutOfBoundsColumn(pop,'9999-03-30')

# Function to show table in my preferred way
def show_data(data):
    show(data,
         scrollY="200px", 
         scrollCollapse=True, 
         paging=False,
         buttons=["excelHtml5"])


# import data
in_community = pd.read_excel("s3://alpha-omppg/Ad-hoc/DPPs-in-community/DPPs-to-check-on-licence-31-Dec-2024.xlsx")
ippTerminations = pd.read_excel("s3://alpha-omppg/Ad-hoc/DPPs-in-community/IPP-Terminations-as-at-02-April-2025.xlsx")

# remove long dashes
in_community = in_community.replace("–","-",regex=True) # replace long dashes with normal dashes
ippTerminations = ippTerminations.replace("–","-",regex=True) # replace long dashes with normal dashes

# check lengths
in_community.shape,ippTerminations.shape #((191, 10), (2515,23))

# remove long blanks
strip_blanks(in_community)
strip_blanks(ippTerminations)

in_community.head()
ippTerminations.head()

# rearrange columns
priority_community = ['noms_number','surname', 'date_of_birth_date']
priority_ppud = ['NOMS_ID','FAMILY_NAME', 'DOB']

in_community = in_community[priority_community + [col for col in in_community.columns if col not in priority_community]]
ippTerminations = ippTerminations[priority_ppud + [col for col in ippTerminations.columns if col not in priority_ppud]]

# view them
in_community.head()
ippTerminations.head()

# Match

query = """SELECT a.*, 
                b.NOMS_ID,
                b.ACTUAL,
                b.FAMILY_NAME,
                b.REVIEW_ID,
                b.SUBSEQUENT_OUTCOME_ACTUAL,
                b.DOB,
                b.CUSTODY_TYPE_DESCRIPTION,
                b.IPP_TERMINATED_FLAG,
                b.TITLE
                
                FROM in_community AS a LEFT JOIN ippTerminations AS b
                ON (a.noms_number = b.NOMS_ID AND a.noms_number IS NOT NULL) OR
                (
                    (a.surname = b.FAMILY_NAME) AND
                    (a.date_of_birth_date = b.DOB AND a.date_of_birth_date IS NOT NULL) 
                    /*AND
                    (
                    (a.FORENAME1 LIKE '%' || b.FIRST_NAMES || '%') OR (b.FIRST_NAMES LIKE '%' || a.FORENAME1 || '%')
                    )*/
                )"""

enhanced_community = duckdb.sql(query).df()
enhanced_community.shape # 191, originally 191

# How many terminated?
sum(enhanced_community['ACTUAL'].notna()) # 174

# Terminated before end of December 2024?
b4_Dec = (
    (enhanced_community['ACTUAL'] <= pd.Timestamp(2024,12,31)) | 
    (enhanced_community['SUBSEQUENT_OUTCOME_ACTUAL'] <= pd.Timestamp(2024,12,31))
)
b4_Dec.value_counts(dropna=False) # 167

enhanced_community['TERMINATED_BEFORE_31_DEC_2024'] = b4_Dec

# rearrange
priority_enhanced_community = ['noms_number','NOMS_ID','surname', 'FAMILY_NAME','date_of_birth_date','DOB','ACTUAL','SUBSEQUENT_OUTCOME_ACTUAL','TERMINATED_BEFORE_31_DEC_2024','CUSTODY_TYPE_DESCRIPTION']

enhanced_community = enhanced_community[priority_enhanced_community + [col for col in enhanced_community.columns if col not in priority_enhanced_community]]

enhanced_community.head()

# Deduplicate 
# in_community.duplicated([]'CRN').sum() # 0

# enhanced_community = enhanced_community.drop_duplicates(subset =['CRN','CUSTODY_TYPE_DESCRIPTION'])
# enhanced_community.shape # 3100, orginally 3098, so 2 duplicates.

# sort data
# enhanced_community = enhanced_community.sort_values('CRN')

# find duplicated cases where there is excess match
# enhanced_community[enhanced_community.duplicated('CRN',keep=False)]

# check dodgy matches which are matches without NOMIS ID being equal
# dodgy = (enhanced_community['NOMS_ID'] != enhanced_community['noms_number']) & (enhanced_community['FAMILY_NAME'].notna())

# dodgy.sum() # 139
# enhanced_community[dodgy].head()

# Create match type
sum(enhanced_community['ACTUAL'].isna()) # 17

enhanced_community[enhanced_community['ACTUAL'].isna()]
enhanced_community.head()

enhanced_community.to_excel("s3://alpha-omppg/Ad-hoc/DPPs-in-community/DPPs-termination-status-04-04-2025.xlsx",index=False)
