""" 
GOAL: Possible DPPs in prison, based on date of birth
By Eric Nyame, 09/05/2024
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
        

#---------------------------------- Load GPP data

# Import list
ipps_mar_2024 = pd.read_excel("s3://alpha-omppg/Ad hoc/2024-05-09-DPP-identification/IPPs-31-March-2024.xlsx",skiprows=1)

ipps_mar_2024.head()
ipps_mar_2024['AGE_SENT_COMMENCEMENT'] = ipps_mar_2024.apply(lambda x: TimeDiffs.year_diff(x['DATEOFBIRTH'],pd.Timestamp(2005,4,4).date()),axis=1)

dpp_age_mask = (ipps_mar_2024['AGE_SENT_COMMENCEMENT'] < 18)
ipps_mar_2024['EXCLUDE_ON_AGE'] = 'Y'
ipps_mar_2024.loc[dpp_age_mask,'EXCLUDE_ON_AGE'] = 'N'
ipps_mar_2024.head()

ipps_mar_2024.to_excel("IPPS-31-March_2024.xlsx",index=None)


#---------------------------------- ipps in community

# Import list
commnunity_ipps_aug1_2023 = pd.read_excel("s3://alpha-omppg/Ad hoc/2024-05-09-DPP-identification/ipps-in-community-August1.xlsx",skiprows=10)

commnunity_ipps_aug1_2023.head()

commnunity_ipps_aug1_2023['AGE_SENT_COMMENCEMENT'] = commnunity_ipps_aug1_2023.apply(lambda x: TimeDiffs.year_diff(x['DoB'],pd.Timestamp(2005,4,4).date()),axis=1)

dpp_age_mask_2 = (commnunity_ipps_aug1_2023['AGE_SENT_COMMENCEMENT'] < 18)
commnunity_ipps_aug1_2023['EXCLUDE_ON_AGE'] = 'Y'
commnunity_ipps_aug1_2023.loc[dpp_age_mask_2,'EXCLUDE_ON_AGE'] = 'N'

retain =['CRN','NOMS No.','Prison No.','Name','DoB','AGE_SENT_COMMENCEMENT','EXCLUDE_ON_AGE']

commnunity_ipps_aug1_2023 = commnunity_ipps_aug1_2023[retain + [col for col in commnunity_ipps_aug1_2023.columns if col not in retain]]
commnunity_ipps_aug1_2023.head()

commnunity_ipps_aug1_2023[commnunity_ipps_aug1_2023['CRN']=='D558474']

commnunity_ipps_aug1_2023.to_excel("IPPS-in-commty-1Aug2023.xlsx",index=None)

commnunity_ipps_aug1_2023.head()

#---------------------import release data

isp_releases = pd.read_excel("")