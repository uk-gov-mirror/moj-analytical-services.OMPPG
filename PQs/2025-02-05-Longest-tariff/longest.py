""" 
To ask the Secretary of State for Justice, what the longest period is that a person is in prison over their minimum tariff; and what the original tariff length was for that person.

By Eric Nyame, 05/02/2025
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

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
import prepareMatch
#importlib.reload(prepareMatch)
import openMatch
# importlib.reload(openMatch)
import TimeDiffs
importlib.reload(TimeDiffs)
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

ispPopulation = pd.read_parquet("s3://alpha-omppg/isp-population/final/isp_pop_2024q4.parquet")
ispPopulation.info()
ispPopulation.dtypes
ispPopulation.head()
ispPopulation['ISP_STATUS'].value_counts(dropna=False)

mask_overtariff = ispPopulation['OVERTARIFF_MONTHS'].notna()
ispPopulation['OVERTARIFF_DAYS'] = np.nan
ispPopulation.loc[mask_overtariff,'OVERTARIFF_DAYS'] = (ispPopulation['EXTRACTDATE']-ispPopulation['TARIFF_EXPIRY_DATE']).dt.days

ispPopulation.head()

unreleased = ispPopulation[ispPopulation['ISP_STATUS'].str.contains('Unreleased',case=False,na=False)]
unreleased['ISP_STATUS'].value_counts(dropna=False)

unreleased = unreleased.sort_values('OVERTARIFF_DAYS',ascending=False)
unreleased.head()

show(unreleased.head(10), buttons=["excelHtml5"])

show(unreleased[unreleased['OVERTARIFF_DAYS'].isna()], buttons=["excelHtml5"])

unreleased[unreleased['TARIFF_EXPIRY_DATE'].isna()].to_excel("missing_tariff.xlsx")