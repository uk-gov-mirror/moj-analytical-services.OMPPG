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


ispLastRev = pd.read_parquet(f"s3://alpha-omppg/ISP Population/Final Datasets/ISP_Pop_2024q1.parquet")

ispLastRev.loc[ispLastRev['SENTENCESTATUS'] == '(7) Recall','TARIFF_PAST'] = 'Y'

ispLastRev['TARIFF'].value_counts(dropna=False).sort_index()

ispLastRev.groupby(['PRISONGENDER','ISP_STATUS','TARIFF_PAST'])['EXTRACTDATE'].size().reset_index(name='count')

pd.crosstab([ispLastRev['PRISONGENDER'],ispLastRev['ISP_STATUS'],ispLastRev['TARIFF_PAST']],ispLastRev['EXTRACTDATE'],margins=True)

pd.crosstab([ispLastRev['ISP_STATUS'],ispLastRev['TARIFF_PAST'],ispLastRev['TARIFF']],ispLastRev['EXTRACTDATE'])

tb = ispLastRev[(ispLastRev['ISP_STATUS']=='Unreleased IPP') & ~(ispLastRev['OVERTARIFF_YEARS'].isna())].copy()

pd.crosstab(tb['OVERTARIFF_YEARS'],tb['TARIFF'], margins=True)

ispLastRev['ISP_STATUS'].value_counts(dropna=False)
