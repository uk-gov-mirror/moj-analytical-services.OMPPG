""" 
9796 (named day) To ask the Secretary of State for Justice, how many and what proportion of people serving an imprisonment for public protection sentence in prison were originally given a tariff of (a) six months, (b) 12 months, (c) 18 months, (d) two years, (e) three years and (f) five years or under. Asked by: Kim Johnson (Liverpool Riverside)

By Eric Nyame, 18/10/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
# import sys
# import duckdb
# import importlib
from itables import show
# import re

# from dateutil.relativedelta import relativedelta

#---------------------------------- Import own predefined functions, akin to macros in SAS

# sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
# import Out_of_bounds_dates
# import prepareMatch
# importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
# import TimeDiffs

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

#def strip_blanks(df):
    #for col in df.select_dtypes(include='object').columns:
        #isp_popcol] = isp_popcol].apply(lambda x: x.strip() if (isinstance(x, str) and #not x.isspace()) else x) #
        
# Import ISP pop data

year = 2024
quarter = 2
isp_pop = pd.read_parquet(f"s3://alpha-omppg/isp-population/final/isp_pop_{year}q{quarter}.parquet")

ipp_unreleased = isp_pop[isp_pop['ISP_STATUS'] =='Unreleased IPP']
ipp_unreleased['EXTRACTDATE'].unique()

ipp_unreleased['TARIFF'].value_counts()

ipp_unreleased['TARIFF_DAYS'] = 
# Define the categories explicitly using masks
conditions = [
    ipp_unreleased['TARIFF_MONTHS'].isna(),
    (ipp_unreleased['TARIFF_MONTHS'] <= 6),  # [0,6]
    (ipp_unreleased['TARIFF_MONTHS'] > 6) & (ipp_unreleased['TARIFF_MONTHS'] <= 12),  # (6,12]
    (ipp_unreleased['TARIFF_MONTHS'] > 12) & (ipp_unreleased['TARIFF_MONTHS'] <= 18),  # (12,18]
    (ipp_unreleased['TARIFF_MONTHS'] > 18) & (ipp_unreleased['TARIFF_MONTHS'] <= 24),  # (18,24]
    (ipp_unreleased['TARIFF_MONTHS'] > 24) & (ipp_unreleased['TARIFF_MONTHS'] <= 36),  # (24,36]
    (ipp_unreleased['TARIFF_MONTHS'] > 36) & (ipp_unreleased['TARIFF_MONTHS'] <= 60)  # (36,60]
]

# Corresponding category labels
labels = [
    np.nan,
    'Up to 6 months',
    'More than 6 months to 12 months',
    'More than 12 months to 18 months',
    'More than 18 months to 2 years',
    'More than 2 years to 3 years',
    'More than 3 years to 5 years'
]

# Use np.select to apply the conditions and assign the labels

ipp_unreleased['TARIFF_CATEGORY'] = np.select(conditions, labels, default='Above 5 years')

ipp_unreleased.head()

show(ipp_unreleased['TARIFF_CATEGORY'].value_counts(dropna=False),buttons=["excelHtml5"])

# Show the result
print(df)

# Define the categories explicitly using masks
conditions_2 = [
    ipp_unreleased['TARIFF_MONTHS'].isna(),
    (ipp_unreleased['TARIFF_MONTHS'] < 6),  # [0,6]
    (ipp_unreleased['TARIFF_MONTHS'] >= 6) & (ipp_unreleased['TARIFF_MONTHS'] < 12),  # (6,12]
    (ipp_unreleased['TARIFF_MONTHS'] >= 12) & (ipp_unreleased['TARIFF_MONTHS'] < 18),  # (12,18]
    (ipp_unreleased['TARIFF_MONTHS'] >= 18) & (ipp_unreleased['TARIFF_MONTHS'] < 24),  # (18,24]
    (ipp_unreleased['TARIFF_MONTHS'] >= 24) & (ipp_unreleased['TARIFF_MONTHS'] < 36),  # (24,36]
    (ipp_unreleased['TARIFF_MONTHS'] >= 36) & (ipp_unreleased['TARIFF_MONTHS'] <= 60),  # (36,60]
    (ipp_unreleased['TARIFF_MONTHS'] > 60) & (ipp_unreleased['TARIFF_MONTHS'] <= 120),  # (36,60]
    (ipp_unreleased['TARIFF_MONTHS'] > 120)
]

# Corresponding category labels
labels_2 = [
    np.nan,
    'Less than 6 months',
    '6 months to less than 12 months',
    '12 months to less than 18 months',
    '18 months to less than 2 years',
    '2 years to less than 3 years',
    '3 years to 5 years',
    'More than 5 years to 10 years',
    'More than 10 years'
]

# Use np.select to apply the conditions and assign the labels

ipp_unreleased['TARIFF_CATEGORY_2'] = np.select(conditions_2, labels_2, default='Unknown')

ipp_unreleased.head()

show(ipp_unreleased['TARIFF_CATEGORY_2'].value_counts(dropna=False),buttons=["excelHtml5"])
ipp_unreleased['TARIFF'].value_counts(dropna=False)

ipp_unreleased.pivot_table(index='TARIFF_CATEGORY_2',columns='TARIFF',aggfunc='size',fill_value=0)


ipp_unreleased[(ipp_unreleased['TARIFF_CATEGORY_2']=='More than 5 years to 10 years') &(ipp_unreleased['TARIFF']=='e Greater than 10 years')][['DOS','TARIFF_EXPIRY_DATE','TARIFF_MONTHS','TARIFF_YEARS','TARIFF_CATEGORY_2','TARIFF']]





tmiss = ipp_unreleased['TARIFF_YEARS'].isna()
t6 = ipp_unreleased['TARIFF_MONTHS'] < 6
t12 = ipp_unreleased['TARIFF_MONTHS'] < 12
t18 = ipp_unreleased['TARIFF_MONTHS'] < 18
t24 = ipp_unreleased['TARIFF_MONTHS'] < 24
t36 = ipp_unreleased['TARIFF_MONTHS'] < 36
t60 = (ipp_unreleased['TARIFF_MONTHS'] < 60) | ( (ipp_unreleased['TARIFF_MONTHS'] == 60) & (ipp_unreleased['TARIFF_EXPIRY_DATE'].dt.day == ipp_unreleased['DOS'].dt.day))
t120 = (ipp_unreleased['TARIFF_MONTHS'] < 120) | ( (ipp_unreleased['TARIFF_MONTHS'] == 120) & (ipp_unreleased['TARIFF_EXPIRY_DATE'].dt.day == ipp_unreleased['DOS'].dt.day))

# Define the categories explicitly using masks
conditions_3 = [
    tmiss,
    ~tmiss & t6,  # [0,6]
    ~(tmiss | t6) & t12,  # (6,12]
    ~(tmiss | t6 | t12) & t18,  # (12,18]
    ~(tmiss | t6 | t12 | t18) & t24,  # (18,24]
    ~(tmiss | t6 | t12 | t18 | t24) & t36,  # (24,36]
    ~(tmiss | t6 | t12 | t18 | t24 | t36) & t60,  # (36,60]
    ~(tmiss | t6 | t12 | t18 | t24 | t36 | t60) & t120,  # (36,60]
    ~(tmiss | t6 | t12 | t18 | t24 | t36 | t60 | t120)
]

(~(tmiss | t6 | t12 | t18 | t24 | t36 | t60 | t120)).sum()
# Corresponding category labels
labels_3 = [
    np.nan,
    'Less than 6 months',
    '6 months to less than 12 months',
    '12 months to less than 18 months',
    '18 months to less than 2 years',
    '2 years to less than 3 years',
    '3 years to 5 years',
    'More than 5 years to 10 years',
    'More than 10 years'
]

# Use np.select to apply the conditions and assign the labels

ipp_unreleased['TARIFF_CATEGORY_3'] = np.select(conditions_3, labels_3, default='Unknown')

ipp_unreleased.head()

show(ipp_unreleased['TARIFF_CATEGORY_3'].value_counts(dropna=False),buttons=["excelHtml5"])
ipp_unreleased['TARIFF'].value_counts(dropna=False)