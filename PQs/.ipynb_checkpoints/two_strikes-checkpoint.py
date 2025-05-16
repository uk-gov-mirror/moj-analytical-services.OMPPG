""" 
GOAL: CREATE GPP AND INFORMATION TO QUARTERLY ISP POP FOR OMSQ
By Eric Nyame, 14/04/2024
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

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
import prepareMatch
#importlib.reload(prepareMatch)
import openMatch
#importlib.reload(openMatch)
import TimeDiffs
import tariff_groups
#importlib.reload(tariff_groups)

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


#---------------------------------- Save

last_year = pd.read_sas("s3://alpha-omppg/ISP Population/final-data/isp_pop_2023q4.sas7bdat",encoding='latin1')


last_year.columns = last_year.columns.str.upper()
last_year['EXTRACTDATE'].value_counts()
last_year['ISP_STATUS'].value_counts(dropna=False)

lifers = last_year[last_year['ISP_STATUS'].str.contains('Life', case=False)]
lifers['ISP_STATUS'].value_counts(dropna=False)
lifers['CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)
lifers[lifers['DOS'] > pd.Timestamp(2005,4,4)]['CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

this_year = pd.read_parquet("s3://alpha-omppg/isp-population/final/isp_pop_2024q2.parquet")
this_year['EXTRACTDATE'].value_counts()

this_year['ISP_STATUS'].value_counts(dropna=False)

lifers_this_year = this_year[this_year['ISP_STATUS'].str.contains('Life', case=False)]
lifers_this_year['ISP_STATUS'].value_counts(dropna=False)
lifers_this_year['CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

two_strikes = lifers_this_year[(lifers_this_year['CUSTODY_TYPE_DESCRIPTION'].isin(['Automatic','Life sentence for 2nd listed offence'])) & (lifers_this_year['DOS'] > pd.Timestamp(2005,4,4))]
two_strikes
lifers_this_year[lifers_this_year['DOS'] > pd.Timestamp(2005,4,4)]['CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

print(two_strikes['DOS'])
