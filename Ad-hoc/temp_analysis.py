""" 
GOAL: PRODUCE OFFENCE BREAKDOWNSRESTRICTED PATIENTS STATISTICS FOR PUBLICATION
By Eric Nyame, 29/02/2024
"""

#---------------------------------- Import Packages

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

#--------------- Import the population dataset and replace long dash with normal dash

isp_releases = pd.read_sas("s3://alpha-omppg/ISP Releases/Final Data/isp_releases_2023q4.sas7bdat", encoding='latin1')
isp_releases.info()
isp_releases.columns = isp_releases.columns.str.upper()

# Check range of year-quarters to be sure you've covered relevant period
isp_releases['Year_Quarter'] = isp_releases['RELEASE_DATE'].dt.to_period('Q')
isp_releases['Year'] = isp_releases['RELEASE_DATE'].dt.to_period('Y')

isp_releases['CUSTODY_TYPE_DESCRIPTION'].unique()

ipp_releases = isp_releases[isp_releases['CUSTODY_TYPE_DESCRIPTION'].isin(['IPP','DPP'])].copy()

pd.crosstab(ipp_releases['RELEASE_TYPE'],ipp_releases['Year_Quarter'],margins = True)

pub_fixed['Year_Quarter'].value_counts(dropna=False).sort_index() # should start from 2013 Q4 to 2023 Q3.

# check missing nomis ids and dos
pub_fixed.shape[0] # 79022 rows
pub_fixed['NOMS_ID'].isna().sum()  # 192 missing NOMIS IDs
pub_fixed['DOS'].isna().sum()  # 2597 missing DOS

# count appearances of NOMIS and Date of sentence
group_counts = pub_fixed.groupby(['NOMS_ID', 'DOS']).size()
group_counts.value_counts(dropna=False).sort_index() # apperances of Nomis id-Dos combos
len(group_counts[group_counts > 1].index.get_level_values('NOMS_ID').unique()) # 9923