""" 
GOAL: ATTEMPT PRODUCE ALL IPPs/DPPs BY PPUD AS AT 16 AUGUST 2024

By Eric Nyame, 28/08/2024
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
# import openMatch
# importlib.reload(openMatch)
import TimeDiffs
# import tariff_groups

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

# IMPORT RELEASES AND RECALLS DATA

master = pd.read_excel("IPP_Termination_Master_List_17_1_2024.xlsx")
master.head()

# --------------------------------------------------------------------------------------------
# 1. Exclude Deceased cases and Exclude cases already terminated 
# --------------------------------------------------------------------------------------------
master['AUTO_TERMINATED'].value_counts(dropna=False)
master['CURRENT_STATUS'].value_counts(dropna=False)

exclusion_condition = (
    ( master['AUTO_TERMINATED'].isin(['Yes','Yes_pending']) ) | ( master['CURRENT_STATUS'].isin(['deceased','Deceased']) ) 
)

sum(exclusion_condition) # 2357 = 618 + 1739 

wanted = master[~exclusion_condition]

# 2 Identify offenders who have not been released from IPP sentence
    # For these, ensure there is an active termination check review (check review to be opened if not) 

sum( wanted["FIRST_REL_DATE"].isna() ) # 2000
wanted[wanted["FIRST_REL_DATE"].isna()]['CURRENT_STATUS'].value_counts(dropna=False)


unreleased = wanted[wanted["FIRST_REL_DATE"].isna()]
unreleased = unreleased[unreleased['CURRENT_STATUS'].isin(['unreleased','hospital','ual',np.nan])]
unreleased['CURRENT_STATUS'].value_counts(dropna=False)

# --------------------------------------------------------------------------------------------
# 2 Identify offenders who have been released and are in custody and check 
    # they have an active/active referred GPP/ISP Recall review (no termination reviews required going forward) 
    # Offenders in custody but before the 2/3 year eligibility point will still need to be identified so that a PB Termination review can be opened in case they are re-released before this date
# --------------------------------------------------------------------------------------------
sum( wanted["FIRST_REL_DATE"].notna() ) # 3709
wanted[wanted["FIRST_REL_DATE"].notna()]['CURRENT_STATUS'].value_counts(dropna=False)

recalled = wanted[wanted["FIRST_REL_DATE"].notna()]
recalled = recalled[ recalled['CURRENT_STATUS'].isin(['recalled','Recalled','hospital']) ]
recalled['CURRENT_STATUS'].value_counts(dropna=False)

    # Create eligibility date (2/3 years from first release for DPP/IPP)

recalled.dtypes
sum(recalled['FIRST_REL_DATE'].isna()) # 0
sum(recalled['LATEST_REL_DATE'].isna()) # 0

recalled['FIRST_REL_DATE'] = pd.to_datetime(recalled['FIRST_REL_DATE'])
recalled['LATEST_REL_DATE'] = pd.to_datetime(recalled['LATEST_REL_DATE'])
    
recalled['TERMINATION_ELIGIBLE_DATE'] = recalled['FIRST_REL_DATE'] + pd.offsets.DateOffset(years=3)
recalled.loc[recalled['CUSTODY_TYPE_DESCRIPTION'] == 'DPP', 'TERMINATION_ELIGIBLE_DATE'] = recalled['FIRST_REL_DATE'] + pd.offsets.DateOffset(years=2)

    # Identify those before the eligibility date
recalled['BEFORE_ELIGIBILITY_DATE_10DEC2024'] = 'BEFORE'
recalled.loc[recalled['TERMINATION_ELIGIBLE_DATE'] <= pd.Timestamp(2024,12,10),'BEFORE_ELIGIBILITY_DATE_10DEC2024'] = 'AFTER'


# --------------------------------------------------------------------------------------------
# 3 Identify offenders who have been released 2 (DPP) /3 (IPP) or more years ago and have not had a previous termination review – a PB Termination review will need to be created 
# --------------------------------------------------------------------------------------------

released = wanted[wanted["FIRST_REL_DATE"].notna()].copy()
released = released[released['CURRENT_STATUS'].isin(['released','Released'])]
released['CURRENT_STATUS'].value_counts(dropna=False)

    # Create eligibility date (2/3 years from first release for DPP/IPP
    
released.dtypes
sum(released['FIRST_REL_DATE'].isna()) # 0
sum(released['LATEST_REL_DATE'].isna()) # 0

released['FIRST_REL_DATE'] = pd.to_datetime(released['FIRST_REL_DATE'])

released.iloc[[441]]
released.loc[2190,'LATEST_REL_DATE'] = pd.Timestamp(2024,3,25)
released['LATEST_REL_DATE'] = pd.to_datetime(released['LATEST_REL_DATE'])

released['TERMINATION_ELIGIBLE_DATE'] = released['FIRST_REL_DATE'] + pd.offsets.DateOffset(years=3)
released.loc[released['CUSTODY_TYPE_DESCRIPTION'] == 'DPP', 'TERMINATION_ELIGIBLE_DATE'] = released['FIRST_REL_DATE'] + pd.offsets.DateOffset(years=2)

    # Set expected automatic termination date
    
released['AUTO_TERMINATION_DATE '] = np.nan
auto_cond1 = released['TERMINATION_ELIGIBLE_DATE'] >= released['LATEST_REL_DATE']
auto_cond2 = released['TERMINATION_ELIGIBLE_DATE'] < released['LATEST_REL_DATE']

released.loc[auto_cond1, 'AUTO_TERMINATION_DATE '] = released['TERMINATION_ELIGIBLE_DATE'] + pd.offsets.DateOffset(years = 2)
released.loc[auto_cond2, 'AUTO_TERMINATION_DATE '] = released['LATEST_REL_DATE'] + pd.offsets.DateOffset(years = 2)

released['AUTO_TERMINATION_DATE '] = pd.to_datetime(released['AUTO_TERMINATION_DATE '])
