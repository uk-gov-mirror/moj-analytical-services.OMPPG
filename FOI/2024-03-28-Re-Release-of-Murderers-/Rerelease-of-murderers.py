""" 
GOAL: PRODUCE RERELEASES OF MANDATORY LIFERS
By Eric Nyame, 02/04/2024
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

#----------------------------------Set globals

year = 2023
snapshotDate = pd.Timestamp(2023,12,31)

#--------------- Import isp release data

rereleases = pd.read_sas(f"s3://alpha-omppg/ISP Releases/Final Data/isp_releases_2023q3.sas7bdat",encoding='latin1')

rereleases.columns = rereleases.columns.str.upper()

    # keep recall releases and release date from 2020
    
rereleases = rereleases[(rereleases['RELEASE_TYPE'] == 'Recall Re-release') &
                        (rereleases['RELEASE_DATE'].dt.year >= 2020)].copy()

    # Create release year column
    
rereleases['CAL_YEAR'] = rereleases['RELEASE_DATE'].dt.year # calendar year

# rereleases['YEAR2'] = rereleases['RELEASE_DATE'].dt.to_period("Y") # same as above

    # Create financial year elease year column
    
rereleases['FIN_YEAR'] = rereleases['RELEASE_DATE'].map(lambda x: str(x.year) + "/" + str(x.year+1) if x.month > 3 else str(x.year-1) + "/"+ str(x.year))

    # Keep only mandatory lifers or offenders with murder as index offence
    
# rereleases['CUSTODY_TYPE_DESCRIPTION'].value_counts()
# rereleases['INDEX_OFFENCE_DESCRIPTION'].value_counts(dropna=False)

custype_mandatory = ['Mandatory (MLP)','HMP [*]','CFL (murder) (S93)']

murderers = rereleases[(rereleases['CUSTODY_TYPE_DESCRIPTION'].isin(custype_mandatory)) | 
                      (rereleases['INDEX_OFFENCE_DESCRIPTION']=='Murder')].copy()

    # check counts    

#pd.crosstab(murderers['CUSTODY_TYPE_DESCRIPTION'],murderers['INDEX_OFFENCE_DESCRIPTION'],margins=True)

murderers.groupby(['CAL_YEAR']).size().reset_index(name='count')

murderers.groupby(['FIN_YEAR']).size().reset_index(name='count')

#pd.crosstab(murderers['CUSTODY_TYPE_DESCRIPTION'],murderers['INDEX_OFFENCE_DESCRIPTION'],margins=True).to_excel("data.xlsx")