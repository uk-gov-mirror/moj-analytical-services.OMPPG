""" 
GOAL: 
Total HMP cohort broken down by:
    1. Date of sentence
    2. Current age
    3. Age at sentencing
    4. Age at time of the offence (I understand that this will depend on whether the correct PPUD field has been utilised, but the field is not mandatory)
    5. HMP halfway date
    6. Tariff expiry date
    7. Whether they have already had a hm tariff review and whether they have had any subsequent reviews
    8. If they have had a review already, what was the outcome
    9. HMP cases which pre-date the legislative change (change came into effect on 18 February 2021 – how many have already had a review under the old legislation
    10. Cases who have joined the cohort since the legislative change

By Eric Nyame, 14/02/2024
"""
#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys # for adding folders to the search path
import duckdb
import importlib

import re

from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
from my_log import my_log
from Out_of_bounds_dates import date_out_of_bounds
import prepareMatch 
importlib.reload(prepareMatch)

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


#----------------------------------Import PPUD data

cstt_Reviews = pd.read_excel("s3://alpha-omppg/Ad hoc/2024 02 14 HMP Tariff Review/HMP Tariff Reviews As At 14Feb2024.xls")
cstt_Reviews.info()
del_cols = ['ACTUAL_REFERRAL_DATE', 'CRO_PNC', 'CURRENT_TARGET_DATE','DATE_CHECKED_BY_PB', 'GENDER', 'INDEX_OFFENCE_DESCRIPTION',
        'NATIONALITY_DESCRIPTION', 'NEXT_REVIEW_DATE', 'NO_OF_APPLICATIONS','NOMS_REGION_DESCRIPTION', 'ORGINAL_TARGET_DATE',
       'PROBATION_AREA_DESCRIPTION','REASON_FOR_FURTHER_REVIEW_DESCRIPTION','REVIEW_RECOMMENDATION_DESCRIPTION',
       'SIFT_RESULT_DESCRIPTION', 'MAND_DOCS_OASYS','SUBSEQUENT_OUTCOME_DESCRIPTION', 'SUBSEQUENT_OUTCOME_ACTUAL']

cstt_Reviews.drop(del_cols, axis = 1,inplace = True)
cstt_Reviews.columns
keep_mask = ['FILE_REFERENCE','FAMILY_NAME','REVIEW_REASON_DESCRIPTION','REVIEW_RESULT_DESCRIPTION','REVIEW_STATUS_DESCRIPTION','REVIEW_DATE']

cstt_Reviews = cstt_Reviews[keep_mask + [col for col in cstt_Reviews.columns if col not in keep_mask]]
cstt_Reviews.info()
cstt_Reviews.head(20)

cstt_Reviews.sort_values(by=['FILE_REFERENCE','REVIEW_DATE'], inplace = True)

#----------------------------------Determine proper completed reviews

cstt_Reviews.groupby('REVIEW_RESULT_DESCRIPTION')['REVIEW_STATUS_DESCRIPTION'].value_counts(dropna=False).to_frame()

cstt_Reviews['COMPLETED'] = np.where(cstt_Reviews['REVIEW_STATUS_DESCRIPTION'] =='Completed',1,0)
cstt_Reviews['REDUCED'] = np.where(
                                    (cstt_Reviews['REVIEW_RESULT_DESCRIPTION'] =='Tariff Reduced [*]') & 
                                    (cstt_Reviews['COMPLETED'] == 1),
                                   1,0
                                  )
cstt_Reviews['UNCHANGED'] = np.where(
                                        (cstt_Reviews['REVIEW_RESULT_DESCRIPTION'].isin(['Tariff Unchanged [*]','Not Applicable'])) & 
                                        (cstt_Reviews['COMPLETED'] == 1),
                                        1,0
                                    )
cstt_Reviews['ACTIVE'] = np.where(cstt_Reviews['REVIEW_STATUS_DESCRIPTION'] =='Active',1,0)
cstt_Reviews['TO_KEEP'] = cstt_Reviews['REDUCED'] + cstt_Reviews['UNCHANGED'] + cstt_Reviews['ACTIVE']


cstt_Reviews_2 = cstt_Reviews[cstt_Reviews['TO_KEEP'] == 1]

keep_mask = ['FILE_REFERENCE','FAMILY_NAME','COMPLETED','REDUCED','UNCHANGED','REVIEW_RESULT_DESCRIPTION','REVIEW_STATUS_DESCRIPTION','REVIEW_DATE']
cstt_Reviews_2 = cstt_Reviews_2[keep_mask + [col for col in cstt_Reviews_2.columns if col not in keep_mask]]
cstt_Reviews_2.sort_values(by=['FILE_REFERENCE','REVIEW_DATE'], inplace = True)
cstt_Reviews_2.head()

#----------------------------------View duplicated cases

cstt_Reviews_2[cstt_Reviews_2.duplicated(subset='REVIEW_ID',keep=False)] # None, good
cstt_Reviews_2[cstt_Reviews_2.duplicated(subset='FILE_REFERENCE',keep=False)]


#---------------------------------- Count completed, reduced, unchanged and active per person

cstt_Reviews_2['n_COMPLETED'] = cstt_Reviews_2.groupby('FILE_REFERENCE')['COMPLETED'].transform('sum')
cstt_Reviews_2['n_REDUCED'] = cstt_Reviews_2.groupby('FILE_REFERENCE')['REDUCED'].transform('sum')
cstt_Reviews_2['n_UNCHANGED'] = cstt_Reviews_2.groupby('FILE_REFERENCE')['UNCHANGED'].transform('sum')
cstt_Reviews_2['n_ACTIVE'] = cstt_Reviews_2.groupby('FILE_REFERENCE')['ACTIVE'].transform('sum')

keep_mask = ['FILE_REFERENCE','FAMILY_NAME','n_COMPLETED','n_REDUCED','n_UNCHANGED','n_ACTIVE','REVIEW_RESULT_DESCRIPTION','REVIEW_STATUS_DESCRIPTION','REVIEW_DATE']
cstt_Reviews_2 = cstt_Reviews_2[keep_mask + [col for col in cstt_Reviews_2.columns if col not in keep_mask]]

cstt_Reviews_2.head(20)

#---------------------------------- Deduplicate and keep the latest review

cstt_Reviews_2.sort_values(by=['FILE_REFERENCE','REVIEW_DATE'],ascending = [True,False], inplace = True)

cstt_Reviews_2.drop_duplicates(subset='FILE_REFERENCE', keep ='first', inplace = True)

cstt_Reviews_2[cstt_Reviews_2['FILE_REFERENCE'] == 'A15763']

cstt_Reviews_2.info()

# Temporarily save
cstt_Reviews_2.to_pickle('cstt_Reviews_final.pkl')
