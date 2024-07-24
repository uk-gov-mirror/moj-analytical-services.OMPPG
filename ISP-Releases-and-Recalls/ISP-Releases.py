""" 
GOAL: PRODUCE RE-RELEASES OF ISPS FOR OMSQ. A BY-PRODUCT IS FIRST RELEASES OF ISPS
By Eric Nyame, 05/02/2024
"""

# Import Packages

import pandas as pd
import numpy as np
import sys # for adding folders to the search path

import re
import duckdb
from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
from my_log import my_log

# Set display options

pd.options.display.max_columns = None
pd.options.display.max_rows = None

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Import Release Data

releasespreTariffIPPs = pd.read_sas("s3://alpha-omppg/ISP Releases/PPUD/PPUD_Releases_tasets/isp_pop_2024q1.sas7bdat",encoding = 'latin1')
my_log(preTariffIPPs)

preTariffIPPs.columns = preTariffIPPs.columns.str.upper() # uppercase column headers

# Keep only pre-tariff IPPs

preTariffIPPMask = (preTariffIPPs['TARIFF_PAST'] == 'N') & (preTariffIPPs['ISP_STATUS'].str.contains('IPP',na=False))
preTariffIPPs = preTariffIPPs[preTariffIPPMask]

len(preTariffIPPs)
preTariffIPPs.dtypes.sort_index()

preTariffIPPs['TARIFF_EXPIRY_DATE'] = pd.to_datetime(preTariffIPPs['TARIFF_EXPIRY_DATE'], errors ='coerce')

columnOrder = ['NOMIS_ID','SURNAME','DOS','TARIFF_EXPIRY_DATE','EXTRACTDATE']
preTariffIPPs = preTariffIPPs[columnOrder + [var for var in preTariffIPPs.columns if var not in columnOrder]]

preTariffIPPs['DAYS_TO_TARIFF'] = preTariffIPPs['TARIFF_EXPIRY_DATE']  - preTariffIPPs['EXTRACTDATE']


def calculate_months_years(row,fromvar,tovar):
    if pd.isnull(row[fromvar]) or pd.isnull(row[tovar]):
        return pd.NA, pd.NA # returns values to be assigned to tariff_months and tariff_years
    elif row[fromvar] >= row[tovar]:
        return pd.NA,pd.NA  # Handle cases where DOS is on or after TARIFF_EXPIRY_DATE
    else:
        delta = relativedelta(row[tovar], row[fromvar])
        total_years = delta.years
        total_months = delta.years * 12 + delta.months
        return  total_months, total_years # returns values to be assigned to tariff_months and tariff_years

    # Apply the function to the DataFrame to create tariff_months and tariff_years
preTariffIPPs[['MONTHS_TO_TARIFF', 'YEARS_TO_TARIFF']] = preTariffIPPs.apply(
                                                                lambda row: calculate_months_years(row,'EXTRACTDATE','TARIFF_EXPIRY_DATE'), 
                                                                axis=1, 
                                                                result_type='expand'
                                                              )

columnOrder = ['NOMIS_ID','SURNAME','DOS','TARIFF_EXPIRY_DATE','EXTRACTDATE','DAYS_TO_TARIFF','MONTHS_TO_TARIFF','YEARS_TO_TARIFF']
preTariffIPPs = preTariffIPPs[columnOrder + [var for var in preTariffIPPs.columns if var not in columnOrder]]

preTariffIPPs.YEARS_TO_TARIFF.value_counts().sort_index()
preTariffIPPs.to_excel("pretarriff_IPPs.xlsx", index = None)


df = pd.DataFrame('some value', columns=['Header1','Header2','Header3'], index=np.arange(12))
added_columns = 'Header2'
dropped_columns = 'Header1'
def highlight_col(x):
    if x.name in added_columns:
        return ['background-color: #67c5a4']*x.shape[0]
    elif x.name in dropped_columns:
        return ['background-color: #ff9090']*x.shape[0]
    else:
        return ['background-color: None']*x.shape[0]
col_loc_add = df.columns.get_loc(added_columns) + 2
col_loc_drop = df.columns.get_loc(dropped_columns) + 2
df.style.apply(highlight_col, axis=0)\
  .set_table_styles(
     [{'props': [('background-color', 'yellow')]},
     {'props': [('background-color', 'blue')]}])