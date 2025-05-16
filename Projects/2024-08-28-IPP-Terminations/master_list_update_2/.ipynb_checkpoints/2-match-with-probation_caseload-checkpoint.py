""" 
GOAL: MATCH PPUD TO PROBATION CASELOAD DATA

By Eric Nyame, 28/08/2024
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
# importlib.reload(Out_of_bounds_dates)
import prepareMatch
#importlib.reload(prepareMatch)
import openMatch
#importlib.reload(openMatch)
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
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #
        
#----------------------------------Import NOMIS data

# Create eligibility date

#wanted = pd.read_parquet("output-data/wanted.parquet",columns=fields)
#wanted.info()
#wanted.head()

#wanted.dtypes
#sum((wanted['FIRST_REL_DATE'] != wanted['FIRST_REL_DATE_NEW']) & wanted['FIRST_REL_DATE_NEW'].notna()) # 51
#wanted[(wanted['FIRST_REL_DATE'] != wanted['FIRST_REL_DATE_NEW']) & wanted['FIRST_REL_DATE_NEW'].notna()].head()

wanted.loc[ wanted['FIRST_REL_DATE_NEW'].notna(),'FIRST_REL_DATE'] = wanted['FIRST_REL_DATE_NEW']
wanted.loc[ wanted['LATEST_REL_DATE_NEW'].notna(),'LATEST_REL_DATE'] = wanted['LATEST_REL_DATE_NEW']
wanted.loc[ wanted['LATEST_RECALL_NEW'].notna(),'LATEST_RECALL_DATE'] = wanted['LATEST_RECALL_NEW']

wanted.head()

wanted['TERMINATION_ELIGIBLE_DATE'] = wanted['FIRST_REL_DATE'] + pd.offsets.DateOffset(years=3)
wanted.loc[wanted['CUSTODY_TYPE_DESCRIPTION'] == 'DPP', 'TERMINATION_ELIGIBLE_DATE'] = wanted['FIRST_REL_DATE'] + pd.offsets.DateOffset(years=2)

# Set expected automatic termination date

auto_cond1 = (wanted['CURRENT_STATUS'] == 'Released') & (wanted['TERMINATION_ELIGIBLE_DATE'] >= wanted['LATEST_REL_DATE'])
auto_cond2 = (wanted['CURRENT_STATUS'] == 'Released') & (wanted['TERMINATION_ELIGIBLE_DATE'] < wanted['LATEST_REL_DATE'])

wanted.loc[auto_cond1, 'AUTO_TERMINATION_DATE'] = wanted['TERMINATION_ELIGIBLE_DATE'] + pd.offsets.DateOffset(years = 2)
wanted.loc[auto_cond2, 'AUTO_TERMINATION_DATE'] = wanted['LATEST_REL_DATE'] + pd.offsets.DateOffset(years = 2)

wanted['AUTO_TERMINATION_10DEC2024'] = wanted['CURRENT_STATUS']
wanted.loc[(wanted['AUTO_TERMINATION_DATE'] <= pd.Timestamp(2024,12,30)) & (wanted['CURRENT_STATUS'] == 'Released'),'AUTO_TERMINATION_10DEC2024'] = 'Immediate termination'
wanted.loc[(wanted['AUTO_TERMINATION_DATE'] > pd.Timestamp(2024,12,30)) & (wanted['CURRENT_STATUS'] == 'Released'),'AUTO_TERMINATION_10DEC2024'] = wanted['AUTO_TERMINATION_DATE'].dt.strftime('%B, %Y')

# Active Reviews

ipp_active_gpp = pd.read_excel('raw-data/ipp-active-GPP_27_12_2024.xlsx')
strip_blanks(ipp_active_gpp)

ipp_active_gpp.head()
ipp_active_gpp['REVIEW_STATUS_DESCRIPTION'].value_counts(dropna=False)
# ipp_active_gpp = ipp_active_gpp[ipp_active_gpp['REVIEW_STATUS_DESCRIPTION'].isin(['Active - Referred','Active','Active - REREFERRED'])]

ipp_active_gpp[ipp_active_gpp.duplicated('PRISON_NUMBER',keep=False)].head()

ipp_active_gpp = prepareMatch.prepareMatch(ipp_active_gpp)

skinned_wanted = wanted[~exclusion_condition][['COMMON_ID','DOS']]
len(skinned_wanted)

query4 = """SELECT a.REVIEW_DATE AS GPP_ACTIVE_REVIEW_DATE,
                   a.REVIEW_STATUS_DESCRIPTION AS GPP_ACTIVE_REVIEW_STATUS,
                   a.CURRENT_TARGET_DATE AS GPP_ACTIVE_CURRENT_TARGET_DATE, 
                  b.*
            FROM skinned_wanted AS b 
            LEFT JOIN ipp_active_gpp AS a

            ON      
                    (  (b.COMMON_ID = a.NOMS_ID OR
                        b.COMMON_ID = a.NOMS_TRIM OR
                        b.COMMON_ID = a.NOMS_START OR
                        b.COMMON_ID = a.NOMS_END OR
                        b.COMMON_ID = a.PRISON_NUMBER OR
                        b.COMMON_ID = a.PN_TRIM OR
                        b.COMMON_ID = a.PN_START OR
                        b.COMMON_ID = a.PN_END 
                        ) AND b.COMMON_ID IS NOT NULL
                     )
                     """
matched4 = duckdb.sql(query4).df()
matched4.shape #5439

matched4 = matched4.drop_duplicates(['COMMON_ID','DOS'])
matched4.head()

#wanted = wanted.drop(['GPP_ACTIVE_REVIEW_DATE_x','GPP_ACTIVE_REVIEW_STATUS_x','GPP_ACTIVE_CURRENT_TARGET_DATE_x','GPP_ACTIVE_REVIEW_DATE_y','GPP_ACTIVE_REVIEW_STATUS_y','GPP_ACTIVE_CURRENT_TARGET_DATE_y'],axis=1)

wanted = pd.merge(wanted, matched4, how='left', left_on=['COMMON_ID','DOS'], right_on=['COMMON_ID','DOS'])
len(wanted)
wanted.head()
# TERMINATION REVIEWS

ipp_term_reviews = pd.read_excel('raw-data/ipp-termination-reviews_27_12_2024.xlsx')
strip_blanks(ipp_term_reviews)
# ipp_term_reviews.head()
# ipp_term_reviews['REVIEW_STATUS_DESCRIPTION'].value_counts(dropna=False)

ipp_term_reviews = prepareMatch.prepareMatch(ipp_term_reviews)

ipp_term_reviews.head()
#ipp_term_reviews['REVIEW_RESULT_DESCRIPTION'].value_counts(dropna=False)
#ipp_term_reviews['TITLE'].value_counts(dropna=False)

# term_cond1 = ipp_term_reviews['REVIEW_RESULT_DESCRIPTION'].str.contains('Termina', case=False)
# ipp_term_reviews[term_cond1]['REVIEW_RESULT_DESCRIPTION'].value_counts(dropna=False)

# ipp_term_reviews = ipp_term_reviews[term_cond1]
# ipp_term_reviews = ipp_term_reviews[ipp_term_reviews['REVIEW_RESULT_DESCRIPTION'] != 'Termination - offender opted out/req postponement']

skinned_wanted = wanted[~exclusion_condition][['COMMON_ID','DOS']]
len(skinned_wanted)

query5 = """SELECT a.REVIEW_DATE AS TERMINATION_REVIEW_DATE,
                   a.REVIEW_RESULT_DESCRIPTION AS TERMINATION_REVIEW_RESULT,
                   a.REVIEW_STATUS_DESCRIPTION AS TREMINATION_REVIEW_STATUS,
                   a.REVIEW_TYPE_DESCRIPTION AS TERMINATION_REVIEW_TYPE, 
                   a.REVIEW_ID,
                   a.TITLE,
                  b.*
            FROM skinned_wanted AS b 
            LEFT JOIN ipp_term_reviews AS a

            ON      
                    (  (b.COMMON_ID = a.NOMS_ID OR
                        b.COMMON_ID = a.NOMS_TRIM OR
                        b.COMMON_ID = a.NOMS_START OR
                        b.COMMON_ID = a.NOMS_END OR
                        b.COMMON_ID = a.PRISON_NUMBER OR
                        b.COMMON_ID = a.PN_TRIM OR
                        b.COMMON_ID = a.PN_START OR
                        b.COMMON_ID = a.PN_END 
                        ) AND b.COMMON_ID IS NOT NULL
                     )
                     """
matched5 = duckdb.sql(query5).df()
matched5.shape # 5219,5236,5326

matched5 = matched5.sort_values(['COMMON_ID','REVIEW_ID'],ascending=[True,False])
matched5[matched5.duplicated('COMMON_ID',keep=False)].head()
matched5 = matched5.drop_duplicates(['COMMON_ID','DOS'])

matched5.head()

wanted = wanted.drop(['TERMINATION_REVIEW_DATE','TERMINATION_REVIEW_RESULT','TREMINATION_REVIEW_STATUS','TERMINATION_REVIEW_TYPE','REVIEW_ID'],axis=1)

wanted = pd.merge(wanted, matched5, how='left', left_on=['COMMON_ID','DOS'], right_on=['COMMON_ID','DOS'])
len(wanted)
wanted.head()
# save
#wanted.to_excel("output-data/wanted_new.xlsx")
#wanted.to_parquet("output-data/wanted_new.parquet")



