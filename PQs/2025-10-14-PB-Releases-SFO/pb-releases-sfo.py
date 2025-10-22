""" 
To ask the Secretary of State for Justice, how many prisoners have been granted 
early parole in each of the last five years; and how many prisoners granted early 
parole subsequently committed (a) violent and (b) sexual offences in each of the last five years.

Interpretation agreed: number of Parole Board releases and those so released that committed SFOs.
"""

# import libraries

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/analyticalplatform/workspace/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
import prepareMatch
#importlib.reload(prepareMatch)
import openMatch
#importlib.reload(openMatch)
import TimeDiffs

# Set display options

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.set_option('display.max_colwidth', None)


# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x)

# import data from excel sheets
# ----------------------------------Import PB releases data
sheetNames = ['2018-19','2019-20','2020-21','2021-22','2022-23'] # sheet names in the excel file

# path to the excel file
filePath = '/home/analyticalplatform/workspace/OMPPG/PQs/2025-10-14-PB-Releases-SFO/PQ-78558-Data.xlsx' 

# read all sheets into a dictionary of DataFrames
sheetsData = {sheet: pd.read_excel(filePath, sheet_name=sheet) for sheet in sheetNames}

# combine all sheets into a single DataFrame with column to identify sheet of origin
pb_releases = pd.concat(
    [df.assign(Year=sheet) for sheet, df in sheetsData.items()], 
    ignore_index=True
    )

# details about the combined dataframe
pb_releases.head()
len(pb_releases) # 2758
pb_releases.info()

# Identify sexual offences in column CONVICTION_OFFENCE_DESCRIPTION

pb_releases['SEXUAL_OFFENCE'] = pb_releases['CONVICTION_OFFENCE_DESCRIPTION'].str.contains(
    'Sexual|Rape|Indecent|Assault on a female|Assault on a male|Buggery|Abuse|Exposure|Voyeurism|Pornography|Procuring', 
    case=False, 
    na=False
    )

pb_releases['SEXUAL_OFFENCE'].value_counts()

# check values of OUTCOME_DESCRIPTION - only 'Sentenced (SFO)' is relevant
pb_releases['OUTCOME_DESCRIPTION'].value_counts()

# check values of PB_RELEASED - only True is relevant
pb_releases['PB_RELEASED'].value_counts(dropna = False)

 # Count by year (row) and SEXUAL_OFFENCE(column), where PB_RELEASED is True and OUTCOME_DESCRIPTION is 'Sentenced (SFO)'
# Count of prisoners released by PB who were sentenced for SFOs
pb_released_sfo_mask = (pb_releases['PB_RELEASED'] == True) & (pb_releases['OUTCOME_DESCRIPTION'] == 'Sentenced (SFO)')

result = pb_releases[pb_released_sfo_mask].groupby(['Year', 'SEXUAL_OFFENCE']).size().unstack(fill_value=0)

result
#---------------------------------- Temporary Save, delete later
# Releases_final2.to_parquet(f"isp_releases_{year}q{quarter}_step1.parquet")