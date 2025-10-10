""" 
As discussed – Dame Anne is interested in breakdowns of the recall flow into prisons by month (or week if possible), up to September 2024:
- By gender
- By standard/fixed term recall
- By sentence length (which I understand, due to data quality issues, is available only by an under/over 12-month breakdown)
- By IPP, life, and EDS
- By reason for recall


By Eric Nyame, 09/10/2024
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

# Import population data from Amazon
recalledIPPs = pd.read_parquet("s3://alpha-omppg/isp-population/final/isp_pop_2025q2.parquet")

recalledIPPs['ISP_STATUS'].value_counts(dropna=False)
recalledIPPs.head()

recalledIPPs = recalledIPPs[
    recalledIPPs['ISP_STATUS'] == 'Recalled IPP'
]

len(recalledIPPs)

recalledIPPs.head()

colsToKeep =['NOMIS_ID', 'SURNAME','FORENAME','PRISON_NUMBER','DATEOFBIRTH','EXTRACTDATE','ISP_STATUS','PRISONNAME','DOS','TARIFF_EXPIRY_DATE']

dataForKirsty = recalledIPPs[colsToKeep].copy()

dataForKirsty.head()

dataForKirsty.to_excel('Recalled_IPPs_3oJune2025.xlsx',index=False)
