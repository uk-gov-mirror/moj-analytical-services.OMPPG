""" 
FOI: 
The total number of IPP sentences given out is 8711, to date can you tell me how many individuals have had their IPP licence terminated?
Men -
Women -
Children -

"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
#import importlib
from itables import show
# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
import Out_of_bounds_dates
import prepareMatch
import openMatch
import TimeDiffs
import tariff_groups


# Set display options

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

################# Import data

ippTerminations = pd.read_excel("s3://alpha-omppg/data-central/ipp-terminations/IPP-Terminations-02-04-25.xlsx")
sex_data_ipp = pd.read_excel("s3://alpha-omppg/isp-population/PPUD/2025Q1/PPUD_ISP_2025Q1.xls")

"""
ippTerminations.columns

ippTerminations.head()

ippTerminations['ACTUAL'].max() # 1 April 2025

"""

# Match publication date cut off

ippTerminations = ippTerminations[ippTerminations['ACTUAL'] <= pd.Timestamp(2024,12,31)]

"""
len(ippTerminations) # 2295

sum( # any duplicated review?
    ippTerminations.duplicated('REVIEW_ID', keep=False)
) # 0

sum( # any duplicated offender ID?
    ippTerminations.duplicated('OFFENDER_ID', keep=False)
) # 0

sum( # any duplicated Prison_number?
    ippTerminations.duplicated('PRISON_NUMBER', keep=False)
) # 0

# any missing Prison_number?
ippTerminations['PRISON_NUMBER'].isna().any() # False

"""
# Bring in gender data

query = """
        SELECT
        a.*, b.GENDER
        
        FROM ippTerminations as a LEFT JOIN sex_data_ipp as b
        ON (a.NOMS_ID = b.NOMS_ID AND a.NOMS_ID IS NOT NULL) OR
           (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)"""
matched = duckdb.sql(query).df()

"""
matched.shape

matched[matched.duplicated('OFFENDER_ID', keep=False)]
"""

# Deduplicate

matched = matched.sort_values(by = ['GENDER'],ascending=False)
matched = matched.drop_duplicates(subset=['OFFENDER_ID','PRISON_NUMBER','GENDER'])

"""
matched.shape # 2295 

matched['TITLE'].value_counts(dropna=False)
"""

# Breakdown

matched['CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

matched['GENDER'].value_counts(dropna=False)

""" Results
IPP    2201
DPP      94
Total  2295

Gender breakdown:
M              2214
F                77
F ( Was M )       3
None              1 # make it a male

matched[matched['GENDER'].isna()]
"""