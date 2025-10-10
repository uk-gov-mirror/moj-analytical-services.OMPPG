""" 
GOAL: Sentence bands for determinate cases referred to the Parole Board. 
By Eric Nyame, 02/05/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
import Out_of_bounds_dates # from my_log import my_log
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

#----------------------------------Referral data

recalls = pd.read_excel("s3://alpha-omppg/data-central/recalls/recalls-2022-31-March-2025.xlsx")

strip_blanks(recalls)

"""
len(recalls)
sum(recalls.duplicated('REVIEW_ID',keep=False)) # 6 duplicate Review IDs
sum(recalls.duplicated(['REVIEW_ID','ACTUAL'],keep=False)) # 6 duplicate Review IDs
recalls[recalls.duplicated(['REVIEW_ID','ACTUAL'],keep=False)]

sum(recalls.duplicated('PRISON_NUMBER',keep=False)) # 8

recalls[recalls.duplicated('PRISON_NUMBER',keep=False)].head(5)

"""

#----------------Concatenate NOMIS data over the period

nomisDataNameList = ['DAO_2025_03_31.csv']

def concatDatasets():
    
    pop = pd.DataFrame()
    
    for dataName in nomisDataNameList:
        
        inputData = pd.read_csv(f's3://alpha-omppg/isp-population/raw/{dataName}')
        
        inputData.columns = inputData.columns.str.upper()
        
        pop = pd.concat([pop,inputData],ignore_index=True)
        
    return pop

pop = concatDatasets()

"""
len(pop)
pop.head()
pop.columns
"""
pop["SENTENCESTATUS"].unique()
pop["INDEFINITE_SENTENCE"].unique()
pop = pop[(pop["SENTENCESTATUS"] == '(7) Recall') &
          (pop["INDEFINITE_SENTENCE"] == 'N')]

len(pop) # 11254

# ----------------- Deduplicate the concatenated NOMIS datasets

pop.columns = pop.columns.str.upper()

colsToKeep = ['NOMIS_NO', 'SURNAME', 'FORENAME1', 'EXTRDATE', 'AGE',  'AGEGROUP',  'CRO_NO',  'DATE_OF_RELEASE',  'DOB',  'DRUG_OFFENCES',  'ESTAB',  'ETHNIC_GROUP_LONG','F2052_START',  'F2052_STATUS',  'FIRST_CONVICTED',  'FIRST_SENTENCED',  'HARASSMENT_OFFENCES',  'IEP',  'IMPRISONMENT_STATUS_CATEGORY',  'INDEFINITE_SENTENCE',  'JISL_DAYS',  'JISL_MONTHS',  'JISL_YEARS',  'LOCATION',  'MAIN_OFFENCE_CODE',  'MAIN_OFFENCE_DESCRIPTION',  'MAIN_OFFENCE_STATUTE',  'NATIONALITY_LONG', 'OFFENDER_GENDER',  'PED',  'PNCID_NO',  'PRISONNAME',  'RACIALLY_AGGRAVATED',  'RELEASE_NAME_LONG',  'RELIGIOUSLY_AGGRAVATED',  'RISK_TO_CHILDREN',  'SEC_CAT_ASSESSMENT_DATE',  'SEC_CAT_LONG',  'SED',  'SENTENCE_LENGTH_BANDED',  'SENTENCE_LENGTH_DAYS',  'SENTENCE_LENGTH_MONTHS',  'SENTENCE_LENGTH_YEARS',  'SENTENCE_START_TO_END_DAYS',  'SEX_OFFENDER_REGISTER',  'SEXUAL','VICTIM_OFFENCES',  'VIOLENT',  'PRISONGENDER',  'PRISONPGDREGION',  'FNPSTATUS',  'PREDOMINANTFUNCTION',  'PRISONPROBATIONREGION',  'PRISONEDREGION',  'OFFENCEGROUP',  'SENTENCESTATUS',  'REMAND',  'SENTENCED',  'IMPRISONMENT_STATUS_SHORT',  'SENTENCESTATUSCUSTOM',  'PCOSO'
]

pop = pop[colsToKeep]
pop.head()

"""
len(pop) #
"""

# --------Remme columns to avoid clash later

pop = pop.rename(columns = {'NOMIS_NO':'NOMIS_ID','SED':'SED_NOMIS'})

"""
pop.head()

pop.pivot_table(index=['SENTENCE_LENGTH_BANDED','SENTENCESTATUS'],aggfunc='size')

"""

#---------------------------------- Match datasets
recalls.head()
recalls = prepareMatch.prepareMatch(recalls)

query = """SELECT DISTINCT a.*, 
                           b.RECALL_TYPE_DESCRIPTION,
                           b.CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION,
                           b.PART_TOTAL_IN_DAYS,
                           b.FILE_REFERENCE,
                           b.LICENCE_REVOKE_DATE,
                           b.RTC_DATE,
                           b.RELEASE_BEFORE_RECALL,
                           b.RESCIND_FLAG,
                           b.SED,
                           b.DOS
                           
                            
                    FROM pop AS a LEFT JOIN recalls AS b
                    
                    ON 
                      (a.NOMIS_ID = b.NOMS_ID OR
                       a.NOMIS_ID = b.NOMS_TRIM OR
                       a.NOMIS_ID = b.NOMS_START OR
                       a.NOMIS_ID = b.NOMS_END OR
                       a.NOMIS_ID = b.PRISON_NUMBER OR
                       a.NOMIS_ID = b.PN_TRIM OR
                       a.NOMIS_ID = b.PN_START OR
                       a.NOMIS_ID = b.PN_END)
                       """

matched = duckdb.sql(query).df()
len(matched)

matched.head()
matched2 = matched[~matched["LICENCE_REVOKE_DATE"].isna()]

matched2 = matched2.sort_values(by = ["NOMIS_ID","LICENCE_REVOKE_DATE"],ascending=[True,False])
matched2 = matched2.drop_duplicates("NOMIS_ID")

"""
matched2.shape # 10855
matched2.head()
"""
# ----------------- Datetime type for some columns
matched2.info()    
matched2['SED_NOMIS'] = pd.to_datetime(matched2['SED_NOMIS'],dayfirst=True)
matched['FIRST_SENTENCED'] = pd.to_datetime(matched2['FIRST_SENTENCED'], dayfirst=True)


# --------------- Rate quality of matches
    
sedMatched = (matched2['NOMIS_ID'].notna()) & (matched2['SED'] == matched2['SED_NOMIS']) # SED matched
dosMatched = (matched2['NOMIS_ID'].notna()) & (matched2['DOS'] == matched2['FIRST_SENTENCED']) # DOS matched

matchedCondList = [sedMatched, dosMatched]

matchedRatingsList = [2,1]

matched2['MATCH'] = np.select(matchedCondList, matchedRatingsList,default = 0)

matched2 = matched2.sort_values(by=['NOMIS_ID','MATCH'])

# Standard Recalls Only
matched3 = matched2[~matched2['RECALL_TYPE_DESCRIPTION'].str.contains('14|28|Indeterminate',case=False)]

matched3['RECALL_TYPE_DESCRIPTION'].value_counts(dropna=False)

matched2.to_excel('matched.xlsx',index=False)
