""" 
GOAL: ATTEMPT PRODUCE ALL IPPs/DPPs BY PPUD AS AT 16 AUGUST 2024

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
import prepareMatch
#importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
import TimeDiffs
# import tariff_groups

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


# --------------------------------------------------------------------------------------------
# 2 Identify offenders who have not been released from IPP sentence
    # For these, ensure there is an active termination check review (check review to be opened if not) 

# --------------------------------------------------------------------------------------------
sum( wanted["FIRST_REL_DATE"].isna() ) # 2210
wanted[wanted["FIRST_REL_DATE"].isna()]['CURRENT_STATUS'].value_counts(dropna=False)

#unreleased = wanted[wanted["FIRST_REL_DATE"].isna()]
#unreleased = unreleased[unreleased['CURRENT_STATUS'].isin(['Unreleased','Hospital','Ual',np.nan])]
#unreleased['LOCATION'] = 
#unreleased['CURRENT_STATUS'].value_counts(dropna=False)

unrel_cond = wanted["FIRST_REL_DATE"].isna() & wanted['CURRENT_STATUS'].isin(['Unreleased','Hospital','Ual',np.nan])
wanted['LOCATION'] = ''
wanted.loc[unrel_cond,'LOCATION'] = 'Unreleased'
wanted['LOCATION'].value_counts(dropna=False)

# --------------------------------------------------------------------------------------------
# 2 Identify offenders who have been released and are in custody and check 
    # they have an active/active referred GPP/ISP Recall review (no termination reviews required going forward) 
    # Offenders in custody but before the 2/3 year eligibility point will still need to be identified so that a PB Termination review can be opened in case they are re-released before this date
# --------------------------------------------------------------------------------------------
sum( wanted["FIRST_REL_DATE"].notna() ) # 5855
wanted[wanted["FIRST_REL_DATE"].notna()]['CURRENT_STATUS'].value_counts(dropna=False)

rec_cond = wanted["FIRST_REL_DATE"].notna() & wanted['CURRENT_STATUS'].isin(['Recalled','Hospital'])
wanted.loc[rec_cond,'LOCATION'] = 'Recalled'
wanted['LOCATION'].value_counts(dropna=False)

wanted.head()
wanted['ACTIVE_GPP_REVIEW?'] = ''
wanted.loc[rec_cond & wanted['GPP_ACTIVE_REVIEW_DATE'].notna(),'ACTIVE_GPP_REVIEW?'] = 'Y'
wanted.loc[rec_cond & wanted['GPP_ACTIVE_REVIEW_DATE'].isna(),'ACTIVE_GPP_REVIEW?'] = 'N'

wanted['ACTIVE_GPP_REVIEW?'].value_counts(dropna=False)
sum(rec_cond & wanted['GPP_ACTIVE_REVIEW_DATE'].notna())

# --------------------------------------------------------------------------------------------
# 3 Identify offenders who have been released 2 (DPP) /3 (IPP) or more years ago and have not had a previous termination review – a PB Termination review will need to be created 
# --------------------------------------------------------------------------------------------

wanted['2/3_YR_POINT_PAST?'] = ''
wanted.loc[wanted['TERMINATION_ELIGIBLE_DATE'] <= pd.Timestamp(2024,12,30),'2/3_YR_POINT_PAST?'] = 'Y'
wanted.loc[wanted['TERMINATION_ELIGIBLE_DATE'] > pd.Timestamp(2024,12,30),'2/3_YR_POINT_PAST?'] = 'N'

wanted['TERMINATION_REVIEW_EVER?'] = ''
wanted.loc[wanted['TERMINATION_REVIEW_DATE'].notna(),'TERMINATION_REVIEW_EVER?'] = 'Y'

# --------------------------------------------------------------------------------------------
# 4 Identify offenders to set up an auto termination review for offenders at the 4 year (DPP) 5 years (IPP) anniversary
# --------------------------------------------------------------------------------------------

wanted['4/5_YR_POINT'] = wanted['FIRST_REL_DATE'] + pd.offsets.DateOffset(years=5)
wanted.loc[wanted['CUSTODY_TYPE_DESCRIPTION'] == 'DPP', '4/5_YR_POINT'] = wanted['FIRST_REL_DATE'] + pd.offsets.DateOffset(years=4)

wanted['4/5_YR_POINT_PAST?'] = ''
wanted.loc[wanted['4/5_YR_POINT'] <= pd.Timestamp(2024,12,30),'4/5_YR_POINT_PAST?'] = 'Y'
wanted.loc[wanted['4/5_YR_POINT'] > pd.Timestamp(2024,12,30),'4/5_YR_POINT_PAST?'] = 'N'
# --------------------------------------------------------------------------------------------
# 5 Identify offenders who have been released more than 4 years (DPP) or 5 years (IPP) ago, and open an auto termination review at the two-year anniversary of the last release date
# --------------------------------------------------------------------------------------------
    # Auto Term date?
    

# ADJUSTMENTS
wanted['RELEASE_TYPE_DESCRIPTION'] = wanted['RELEASE_TYPE_DESCRIPTION_NEW']
del wanted['RELEASE_TYPE_DESCRIPTION_NEW']

#wanted = wanted.rename(columns ={'TERMINATION_REVIEW':'TERMINATION_REVIEW_EVER','ACTIVE_GPP_RECALLED':'ACTIVE_GPP_REVIEW'})

retain =['COMMON_ID','FILE_REFERENCE','FAMILY_NAME','DOS','FIRST_REL_DATE','LATEST_REL_DATE','LATEST_RECALL_DATE','CURRENT_STATUS','RELEASE_TYPE_DESCRIPTION','TERMINATION_ELIGIBLE_DATE','2/3_YR_POINT_PAST?','AUTO_TERMINATION_DATE','AUTO_TERMINATED','AUTO_TERMINATION_10DEC2024','LOCATION','ACTIVE_GPP_REVIEW?','TERMINATION_REVIEW_EVER?','4/5_YR_POINT','4/5_YR_POINT_PAST?','LONGEST_TARIFF_EXIPRY_DATE','ALL_ISP_SENTENCES','HAS_LIFE_SENTENCE','NOMS_ID','STATUS_DESCRIPTION','PRISON_NUMBER','Referred to PB','Active Termination Review','CRO_PNC','CUSTODY_TYPE_DESCRIPTION','DOB','ETHNICITY_DESCRIPTION','FIRST_NAMES','GENDER','INDEX_OFFENCE_DESCRIPTION','OFFENDER_ID','NATIONALITY_DESCRIPTION','IS FIRST RELEASE BEFORE DOS?','ON IPP DASHBOARD? 21/08/2024','ACTIVE TERMINATION REVIEW? (AS AT 19/08/24)','LICENCE TERMINATED? (AS AT 21/08/24)','CANCELLED QUASHED REVIEW?','DECEASED REVIEW STATUS','NOTES','SENTENCED_AGE','GPP_ACTIVE_REVIEW_DATE','GPP_ACTIVE_REVIEW_STATUS','GPP_ACTIVE_CURRENT_TARGET_DATE','TERMINATION_REVIEW_DATE','TERMINATION_REVIEW_RESULT','TREMINATION_REVIEW_STATUS','TERMINATION_REVIEW_TYPE','REVIEW_ID','CRN','NOMS_No','Prison_No','Name','DoB_probation','Tier','Conviction_Dt_where_recorded','Sentence_Date_','Conviction_or_Sentence_Date','Convicted_or_Sentenced_under_18','Length_(months)','Length_2','Tariff_Date','First_Release_Date_1','Full_Years_since_First_Release','Two_Years_from_First_Release_(<18_@_sent/conv)','Three_Years_from_First_Release','Five_Years_from_First_Release','Latest_Release_Date_1','Full_years_since_Latest_Release','2_Years_since_Latest_Release','Point_of_Earliest_Possible_Auto-Termination','Point_of_earliest_requirement_for_consideration_of_revocation','Earliest_point_of_action_required','Division','Cluster','LDU','Police_Force','Team','OM','MAPPA_Cat','MAPPA_Level','Surname','Forename']

wanted = wanted[retain]
# save

wanted.to_excel("output-data/wanted_daniel.xlsx")
wanted['LONGEST_TARIFF_EXIPRY_DATE'] = wanted['LONGEST_TARIFF_EXIPRY_DATE'].astype('str')
wanted.to_parquet("output-data/wanted_daniel.parquet")

