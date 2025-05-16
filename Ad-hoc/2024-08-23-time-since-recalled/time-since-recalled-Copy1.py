""" 
GOAL: PRODUCE TIME SINCE LAST RECALL OF IPP OFFENDERS IN CUSTODY. 
By Eric Nyame, 23/08/2024
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
import prepareMatch
#importlib.reload(prepareMatch)
import openMatch
# importlib.reload(openMatch)
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
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x) #
        

#----------------------------------Import NOMIS data

pop = pd.read_sas("s3://alpha-omppg/ISP Population/final-data/isp_pop_2022q3.sas7bdat",encoding='latin1')
pop.columns = pop.columns.str.upper()
pop.head()
print(pop.columns)
ipp_recalled = pop[pop['ISP_STATUS'] == 'Recalled IPP']

# Define the maximum number of days (e.g., let's assume the max in your data is 2800 days)
max_days_recalled = ipp_recalled['DAYS_RECALLED'].max()
max_days_recalled # 3466

# Create bins for each year band
bins = np.arange(0, max_days_recalled + 365, 365)

# Create labels for each bin
labels = [f'{i} years to <{i+1} years' for i in range(len(bins) - 1)]
labels[0] = 'under 1 year'  # First bin label
labels[1] = '1 year to < 2 years'  # First bin label

# Use pd.cut to categorize the DAYS_RECALLED into these bins
ipp_recalled['YEARS_RECALLED_BAND'] = pd.cut(ipp_recalled['DAYS_RECALLED'], bins=bins, labels=labels, right=False)

retain = ['NOMIS_ID', 'SURNAME','ISP_STATUS','LAST_RELEASE_DATE','LAST_LICENCE_REVOKE_DATE','EXTRACTDATE','MONTHS_RECALLED','DAYS_RECALLED','YEARS_RECALLED_BAND','LAST_RTC_DATE','LAST_RECALLNUM','LAST_RECALL_NUMBER_OF_REASONS','LAST_RECALL_REASONS','LAST_RECALL_AREA','LAST_RECALL_FURTHER_CHARGE','ISP_STATUS']

ipp_recalled = ipp_recalled[retain + [col for col in ipp_recalled.columns if not col in retain]]
ipp_recalled.head()


ipp_recalled['YEARS_RECALLED_BAND'].value_counts(dropna=False).sort_index()
# keep only certain sentences

ipp_recalled['MONTHS_RECALLED'].mean()

ipp_recalled[ipp_recalled['YEARS_RECALLED_BAND'] == '11 years to <12 years']
ipp_recalled.to_excel('RECALLED_IPP.xlsx',index=False)

ipp_recalled.groupby('YEARS_RECALLED_BAND').agg(
    avg_months_recalled=('MONTHS_RECALLED', 'mean'),
    avg_cases=('MONTHS_RECALLED', 'size')
).reset_index()