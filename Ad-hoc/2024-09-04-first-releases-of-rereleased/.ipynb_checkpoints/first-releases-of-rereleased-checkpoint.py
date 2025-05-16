""" 
GOAL: PRODUCE TABLE 11 - CONTINUATION FROM TABLE 10 CODE.
By Eric Nyame, 17/04/2024
"""

import pandas as pd
from pandas.api.types import CategoricalDtype
import numpy as np
import sys
import duckdb
import importlib

# openpyxl
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
# import prepareMatch
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

# Get last final recall data for the last 5 quarters----------------------------------------------------------------------


releases_original = pd.read_parquet('s3://alpha-omppg/isp_releases/final-data/isp_releases_2024q1.parquet')

ipp_releases_original = releases_original [releases_original['CUSTODY_TYPE_DESCRIPTION'].isin(['IPP','DPP'])]
len(ipp_releases_original) # 9425

ipp_releases_original.head()

(ipp_releases_original['DOS'].dt.year < 2005).sum()
ipp_releases_original[ipp_releases_original['DOS'].dt.year < 2005]

# Remove the three wrong cases
ipp_releases_original = ipp_releases_original[ipp_releases_original['DOS'].dt.year >= 2005]

(ipp_releases_original['DOS'].dt.year > 2014).sum()

len(ipp_releases_original) # 9422

ipp_releases_original['FIRST_DOS'] = ipp_releases_original.groupby('FILE_REFERENCE')['DOS'].transform(lambda x: x.min())

ipp_releases_original['FIRST_REL_DATE'] = ipp_releases_original[ipp_releases_original['RELEASE_DATE'] > ipp_releases_original['FIRST_DOS']].groupby('FILE_REFERENCE')['RELEASE_DATE'].transform(lambda x: x.min())

ipp_releases_original['RELEASE_TYPE'].unique()
releases =ipp_releases_original[ipp_releases_original['RELEASE_TYPE'] == 'Recall Re-release']
releases = releases[releases['RELEASE_DATE'].dt.year.isin([2022,2023])]
releases['RELEASE_DATE'].dt.year.value_counts(dropna=False)

releases['FIRST_CORRECT'] = (releases['FIRST_REL_DATE'] > releases['FIRST_DOS'])

retain = ['FILE_REFERENCE','FAMILY_NAME','DOS','FIRST_DOS','FIRST_RELEASE_DATE','FIRST_REL_DATE','RELEASE_DATE','FIRST_CORRECT']
releases = releases[retain + [col for col in releases.columns if col not in retain]]
releases.head()

releases['FIRST_CORRECT'].value_counts(dropna=False)
releases['YEARS_SINCE_FIRST_REL'] = releases.apply(lambda x: TimeDiffs.year_diff(x['FIRST_DOS'],x['FIRST_REL_DATE']),axis=1)
releases['YEARS_SINCE_FIRST_REL'].value_counts(dropna=False).sort_index()