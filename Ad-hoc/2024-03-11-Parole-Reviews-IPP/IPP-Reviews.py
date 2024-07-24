""" 
GOAL: PRODUCE RESTRICTED PATIENTS STATISTICS FOR PUBLICATION
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

pop = pd.read_sas("s3://alpha-omppg/ISP Population/Final Datasets/isp_pop_2023q4.sas7bdat", encoding='latin1')
pop.columns = pop.columns.str.upper()
pop.head()

urlsd_ipps = pop[pop['ISP_STATUS'] =='Unreleased IPP']
len(urlsd_ipps)

urlsd_ipps['LAST_REVIEWNUM'].value_counts(dropna=False)

dashB = pd.read_excel("s3://alpha-omppg/Projects/IPP Central Data System/2023 - 09/Exported Excel/unreleased_isp_2023q3.xlsx")
dashB.head()

dashB.columns = dashB.columns.str.upper()
dashB_un_ipps = dashB[(dashB['ISP_STATUS'] =='Unreleased') * (dashB['ISP_TYPE'] =='IPP') ]
len(dashB_un_ipps)
dashB_un_ipps['NUM_POST_REVS'].value_counts(dropna=False).sort_index()


dashB_2 = pd.read_excel("s3://alpha-omppg/Projects/IPP Central Data System/2023 - 06/Exported Excel/UNRELEASED_ISP_2023Q2.xlsx")
dashB_2.head()

dashB_2.columns = dashB_2.columns.str.upper()
dashB_un_ipps_2 = dashB_2[dashB_2['ISP_STATUS'] =='Unreleased IPP']
len(dashB_un_ipps_2)
dashB_un_ipps_2['LAST_REVIEWNUM'].value_counts(dropna=False).sort_index()

