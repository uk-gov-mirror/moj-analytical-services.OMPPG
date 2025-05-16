""" 
GOAL: DPPs in prison
By Eric Nyame, 26/03/2025
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

# Function to identify where bad datetime value is. Pass in the 

def dateOutOfBoundsColumn(dataset,value): # pass in the out-of-bounds date
    for col in dataset.columns:
        # Convert the column to string and check if any value contains the problematic date substring
        if dataset[col].astype(str).str.contains(value).any():
            hmm = dataset[col].astype(str).str.contains(value)
            cols_to_keep = ['NOMIS_ID','SURNAME','EXTRACTDATE',col]
            display(dataset[hmm][cols_to_keep])
            break

# dateOutOfBoundsColumn(pop,'9999-03-30')

# Function to show table in my preferred way
def show_data(data):
    show(data,
         scrollY="200px", 
         scrollCollapse=True, 
         paging=False,
         buttons=["excelHtml5"])

# -------------------------------------
Dec23 = pd.read_sas("s3://alpha-omppg/isp-population/final/isp_pop_2024q1.sas7bdat", encoding='latin1')
Dec23.columns = Dec23.columns.str.upper()
Mar24 = pd.read_parquet("s3://alpha-omppg/isp-population/final/isp_pop_2024q1.parquet")
Jun24 = pd.read_parquet("s3://alpha-omppg/isp-population/final/isp_pop_2024q2.parquet")


Dec23['EXTRACTDATE'].unique()
Mar24['EXTRACTDATE'].unique()
Jun24['EXTRACTDATE'].unique()

mask1 = (Jun24['ISP_STATUS'].str.contains('IPP',case=False,na=False)) & (Jun24['CUSTODY_TYPE_DESCRIPTION'] == 'DPP')
sum(mask1) # 97

dppJun24 = Jun24[mask1]
dppJun24 = pd.merge(dppJun24,Mar24[['NOMIS_ID','ISP_STATUS','CUSTODY_TYPE_DESCRIPTION']],on='NOMIS_ID',how='left',suffixes=(None,'_y'))
cols = ['NOMIS_ID','SURNAME','ISP_STATUS','ISP_STATUS_y','CUSTODY_TYPE_DESCRIPTION','CUSTODY_TYPE_DESCRIPTION_y','EXTRACTDATE','LAST_LICENCE_REVOKE_DATE','LATEST_RELEASE_DATE','DOS','DATEOFBIRTH','PPUD_STATUS','OFFENCE','INDEX_OFFENCE_DESCRIPTION','PRISONNAME','CRO_NO','FORENAME']

dppJun24 = dppJun24[cols]
dppJun24

dppJun24[dppJun24['ISP_STATUS'] != dppJun24['ISP_STATUS_y']]

dppJun24[dppJun24['CUSTODY_TYPE_DESCRIPTION'] != dppJun24['CUSTODY_TYPE_DESCRIPTION_y']]

dppJun24.to_excel('DPPs.xlsx')

#------------------------------lllllllllllllllllllllllllll

mask2 = (Mar24['ISP_STATUS'].str.contains('IPP',case=False,na=False)) & (Mar24['CUSTODY_TYPE_DESCRIPTION'] == 'DPP')
sum(mask2) # 80

dppMar24 = Mar24[mask2]
dppMar24 = pd.merge(Jun24,dppMar24[['NOMIS_ID','ISP_STATUS','CUSTODY_TYPE_DESCRIPTION']],on='NOMIS_ID',how='right',suffixes=(None,'_y'))

len(dppMar24)

cols = ['NOMIS_ID','SURNAME','ISP_STATUS','ISP_STATUS_y','CUSTODY_TYPE_DESCRIPTION','CUSTODY_TYPE_DESCRIPTION_y','EXTRACTDATE','LAST_LICENCE_REVOKE_DATE','LATEST_RELEASE_DATE','DOS','DATEOFBIRTH','PPUD_STATUS','OFFENCE','INDEX_OFFENCE_DESCRIPTION','PRISONNAME','CRO_NO','FORENAME']

dppMar24 = dppMar24[cols]
dppMar24

dppMar24[dppMar24['ISP_STATUS'] != dppMar24['ISP_STATUS_y']]

dppMar24[dppMar24['CUSTODY_TYPE_DESCRIPTION'] != dppMar24['CUSTODY_TYPE_DESCRIPTION_y']]

dppMar24.to_excel('DPPsMarch24.xlsx')

#----------------------------------Set Global Parameters
