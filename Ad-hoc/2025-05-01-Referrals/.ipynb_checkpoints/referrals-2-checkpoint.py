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

referrals = pd.read_excel("s3://alpha-omppg/data-central/PR_referrals/referrals_June2024_May2025.xls")

strip_blanks(referrals)

"""
len(referrals) # 5043
sum(referrals['REVIEW_ID'].isna()) # 0
sum(referrals.duplicated('REVIEW_ID',keep=False)) # 6 duplicate Review IDs
sum(referrals.duplicated(['REVIEW_ID','ACTUAL'],keep=False)) # 6 duplicate Review IDs
referrals[referrals.duplicated(['REVIEW_ID','ACTUAL'],keep=False)]

sum(referrals.duplicated('PRISON_NUMBER',keep=False)) # 8

referrals[referrals.duplicated('PRISON_NUMBER',keep=False)].head(5)

"""

#----------------Concatenate NOMIS data over the period

nomisDataNameList = ['DAO_2024_03_31.csv',
                     'DAO_2024_06_30.csv',
                     'DAO_2024_09_30.csv',
                     'DAO_2024_12_31.csv',
                     'DAO_2025_03_31.csv',
                     'DAO_2025_04_30.csv']

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

"""

# ----------------- Deduplicate the concatenated NOMIS datasets

pop.columns = pop.columns.str.upper()

colsToKeep =['NOMIS_NO','FIRST_SENTENCED','FIRST_CONVICTED','SED','SENTENCE_LENGTH_BANDED',
             'EXTRDATE','SENTENCESTATUS','SURNAME']

pop = pop[colsToKeep]

sum(pop.duplicated(['NOMIS_NO','SED'],keep=False)) #454156

pop = pop.drop_duplicates(['NOMIS_NO','SED']) # remove duplicates

"""
len(pop) # 192830
"""

# --------Remme columns to avoid clash later

pop = pop.rename(columns = {'NOMIS_NO':'NOMIS_ID','SED':'SED_NOMIS'})

"""
pop.head()

pop['EXTRDATE'].value_counts()
pop.pivot_table(index=['SENTENCE_LENGTH_BANDED','SENTENCESTATUS'],aggfunc='size')

"""

#---------------------------------- Match datasets

referrals = prepareMatch.prepareMatch(referrals)

query = """SELECT DISTINCT b.*, 
                           a.*
                            
                    FROM referrals AS b LEFT JOIN pop AS a
                    
                    ON 
                      (a.NOMIS_ID = b.NOMS_ID OR
                       a.NOMIS_ID = b.NOMS_TRIM OR
                       a.NOMIS_ID = b.NOMS_START OR
                       a.NOMIS_ID = b.NOMS_END OR
                       a.NOMIS_ID = b.PRISON_NUMBER OR
                       a.NOMIS_ID = b.PN_TRIM OR
                       a.NOMIS_ID = b.PN_START OR
                       a.NOMIS_ID = b.PN_END)"""

matched = duckdb.sql(query).df()

"""
matched.shape #8014, there are multiple mathces

"""
# ----------------- Datetime type for some columns
matched.info()    
matched['SED_NOMIS'] = pd.to_datetime(matched['SED_NOMIS'],dayfirst=True)
matched['FIRST_SENTENCED'] = pd.to_datetime(matched['FIRST_SENTENCED'], dayfirst=True)


# --------------- Rate quality of matches
    
sedMatched = (matched['NOMIS_ID'].notna()) & (matched['SED'] == matched['SED_NOMIS']) # SED matched
dosMatched = (matched['NOMIS_ID'].notna()) & (matched['DOS'] == matched['FIRST_SENTENCED']) # DOS matched
nomisIDmatched = matched['NOMIS_ID'].notna() # NOMIS ID matched

matchedCondList = [sedMatched, dosMatched, nomisIDmatched]

matchedRatingsList = [3,2,1]

matched['MATCH'] = np.select(matchedCondList, matchedRatingsList,default = 0)

matched = matched.sort_values(by=['PRISON_NUMBER','MATCH'])
"""
sum(matched.duplicated('REVIEW_ID',keep=False)) #5339

colsToSee = ['NOMIS_ID','SURNAME','DOS','FIRST_SENTENCED','SED','SED_NOMIS','MATCH','SENTENCE_LENGTH_BANDED']

matched[matched.duplicated('REVIEW_ID',keep=False)][colsToSee].head(10)

matched[colsToSee].head(10)

"""
# ----------------Deduplicate

matched2 = matched.sort_values(by=['PRISON_NUMBER','REVIEW_ID','MATCH'],ascending = [True,True,False])

matched2 = matched2.drop_duplicates(subset=['PRISON_NUMBER','REVIEW_ID'], keep ='first').copy()

"""
matched2.loc[matched2['NOMIS_ID']=='A0461AC'][colsToSee] # match should be 3

matched2.shape # 5040, 3 duplicates removed

matched2['MATCH'].value_counts()
"""

# - ------Determine sentences under 4 years

ppudDaysToSED = (matched2['SED'] - matched2['DOS']).dt.days
nomisDaysToSED = (matched2['SED_NOMIS'] - matched2['FIRST_SENTENCED']).dt.days

matched2['ppud < 4yrs'] = np.where(ppudDaysToSED < 1461,"Yes","") # less than 4 years

matched2['nomis < 4yrs'] = np.where(nomisDaysToSED < 1461,"Yes","") # less than 4 years

"""
matched2.head()
matched2['ppud < 4yrs'].value_counts(dropna=False)
matched2['SENTENCE_LENGTH_BANDED'].value_counts(dropna=False)
"""

under4yrsList = ['Less than 6 months','6 months','More than 6 months to less than 12 months','12 months to less than 4 years']

matched2['FINAL'] = 'No'
matched2.loc[matched2['SENTENCE_LENGTH_BANDED'].isin(under4yrsList), 'FINAL'] = 'Yes'
matched2.loc[matched2['SENTENCE_LENGTH_BANDED'].isna(), 'FINAL'] = pd.NA

"""
matched2.head()

matched2['FINAL'].value_counts(dropna=False)

matched2.groupby(['FINAL','SENTENCE_LENGTH_BANDED'],dropna=False).agg('size')
"""
# --------drop some unneeded columns

matched2 = matched2.drop(columns =['FIRST_CONVICTED','EXTRDATE','SENTENCESTATUS'])


# --------------keep a copy

matched2.to_excel('matched.xlsx',index=False)
