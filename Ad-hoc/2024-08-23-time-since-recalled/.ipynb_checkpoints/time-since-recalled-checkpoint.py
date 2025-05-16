""" 
GOAL: PRODUCE TIME SINCE LAST RECALL OF IPP OFFENDERS IN CUSTODY. 
By Eric Nyame, 23/08/2024
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
import openMatch
# importlib.reload(openMatch)
import TimeDiffs
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

# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x) #
        

#----------------------------------Import NOMIS data

pop = pd.read_parquet("s3://alpha-omppg/isp-population/final/isp_pop_2024q2.parquet")
pop.head()
print(pop.columns)
ipp_recalled = pop[pop['ISP_STATUS'] == 'Recalled IPP']

for col in pop.columns:
    print("'" + col + "'",end=',')
    
'AGE','LAST_MOVEMENT_DIRECTION','SEXUAL','AGEBAND','LAST_MOVEMENT_FROM','SURNAME','CRO_NO','LAST_MOVEMENT_REASON','VIOLENT','CSRA_LEVEL','LAST_MOVEMENT_TO','PRISONGENDER','DATEOFRELEASE','LAST_MOVEMENT_TYPE','PRISONPGDREGION','DATEOFBIRTH','CELLLOCATION','FNPSTATUS','DRUG_OFFENCES','OFFENCE','MAINFUNCTION','PRISONCODE','MAIN_OFFENCE_STATUTE','PRISONPROBATIONREGION','ETHNICGROUP','MARITALSTATUS','PRISONEDREGION','EXTRACTDATE','MATERNITY_ONGOING_OR_INACTIVE','SECCATSUMMARY','F2052START','MATERNITYSTATUS','OFFENCEGROUP','F2052_STATUS','NATIONALITYNAME','SENTENCESTATUS','SEX_OFFENDER_REGISTER','FIRSTCONVICTED','NOMIS_ID','IMPRISONMENTSTATUSSHORT','FIRSTMOVEMENT','GENDER','FIRSTSENTENCED','PNCID_NO','FORENAME','PRISONNAME','IEP','RELIGION','IMPRISONMENT_STATUS_CATEGORY','SEC_CAT_ASSESSMENT_DATE','INDEFINITE_SENTENCE','SECURITYCATEGORY','LAST_MOVEMENT_DATE','INITIAL','OFFGRP4','OFFGRP2','PROGRESSION_REGIME','OPEN_TYPE','CONDITIONS','DOS','TARIFF_EXPIRY_DATE','EXCLUDED_FROM_OPEN','WHOLE_LIFE','CUSTODY_TYPE_DESCRIPTION','STATUS_DESCRIPTION','LATEST_RELEASE_DATE','DETERMINATE_FLAG','PRISON_NUMBER','INDEX_OFFENCE_DESCRIPTION','PPUD_PRISON','PROBATION_SERVICE_DESCRIPTION','EFFECTIVE_TED','DETAILED_OFFENCE_GROUP','TARIFF_PAST','TARIFF_MONTHS','TARIFF_YEARS','SERVED_MONTHS','SERVED_YEARS','TARIFFS_SERVED','OVERTARIFF_MONTHS','OVERTARIFF_YEARS','SENTENCED_AGE','TARIFF_IN_QUARTER','TARIFF','FIRST_RELEASE_DATE','FIRST_RELEASE_CONDITIONS','MONTHS_BEFORE_RELEASE','YEARS_BEFORE_RELEASE','LAST_RELEASE_DATE','LAST_RELEASE_TYPE','LAST_RELEASE_CONDITIONS','LAST_LICENCE_REVOKE_DATE','LAST_RTC_DATE','LAST_RECALLNUM','LAST_RECALL_NUMBER_OF_REASONS','LAST_RECALL_REASONS','LAST_RECALL_AREA','LAST_RECALL_FURTHER_CHARGE','ISP_STATUS','PPUD_STATUS','DAYS_RECALLED','MONTHS_RECALLED','CUSTODY_STAGE','ISP_TYPE','LAST_REVIEW_REASON','LAST_REVIEW_RESULT','LAST_REVIEW_DATE','LAST_SUBSEQUENT_OUTCOME','LAST_SUBSEQUENT_DATE','LAST_REVIEWNUM','MAX_PROGRESS','PROGRESS_DATE','OPEN_REVIEWNUM','LAST_OPEN_DATE','PREVIOUS_PROGRESS'


# Define the maximum number of days (e.g., let's assume the max in your data is 2800 days)
max_days_recalled = ipp_recalled['DAYS_RECALLED'].max()
max_days_recalled # 4197

# Create bins for each year band
bins = np.arange(0, max_days_recalled + 365, 365)

# Create labels for each bin
labels = [f'{i} years to <{i+1} years' for i in range(len(bins) - 1)]
labels[0] = 'under 1 year'  # First bin label
labels[1] = '1 year to < 2 years'  # First bin label

# Use pd.cut to categorize the DAYS_RECALLED into these bins
ipp_recalled['YEARS_RECALLED_BAND'] = pd.cut(ipp_recalled['DAYS_RECALLED'], bins=bins, labels=labels, right=False)

retain = ['NOMIS_ID', 'SURNAME','ISP_STATUS','LAST_RELEASE_DATE','LAST_LICENCE_REVOKE_DATE','EXTRACTDATE','MONTHS_RECALLED','DAYS_RECALLED','YEARS_RECALLED_BAND','LAST_RTC_DATE','LAST_RECALLNUM','LAST_RECALL_NUMBER_OF_REASONS','LAST_RECALL_REASONS','LAST_RECALL_AREA','LAST_RECALL_FURTHER_CHARGE','ISP_STATUS']

ipp_recalled = ipp_recalled[retain + [col for col in ipp_recalled.columns if not col in retain]]
ipp_recalled.head()


ipp_recalled['YEARS_RECALLED_BAND'].value_counts(dropna=False).sort_index()
# keep only certain sentences

ipp_recalled['MONTHS_RECALLED'].mean()

ipp_recalled[ipp_recalled['YEARS_RECALLED_BAND'] == '11 years to <12 years']
ipp_recalled.to_excel('RECALLED_IPP.xlsx',index=False)

ipp_recalled.groupby('YEARS_RECALLED_BAND').agg(
    avg_months_recalled=('MONTHS_RECALLED', 'mean'),
    avg_cases=('MONTHS_RECALLED', 'size')
).reset_index()