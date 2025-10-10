""" 

"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib
import os

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
        

# Import remission data

remissions = pd.read_excel("remissions.xlsx")
len(remissions) # 534

#remissions = remissions[['Date of receipt','NOMIS ID','PPUD ref','Date of warrant issue']]

# rename some columns
remissions = remissions.rename(columns={'Date of receipt':'DATE_OF_RECEIPT',
                                        'NOMIS ID':'NOMIS_ID',
                                        'PPUD ref':'PPUD_REF',
                                        'Date of warrant issue':'DATE_OF_WARRANT'})

strip_blanks(remissions) # trim fields

# remissions.info()

# remissions = remissions[(remissions['DATE_OF_RECEIPT'].notna()) & (~remissions['NOMIS_ID'].isin(['G23372','MHU_271248']))]

# remissions = remissions[remissions['NOMIS_ID'].notna()]
# len(remissions) # 522

# remissions.head()

# ------------------- Bring in NOMIS data

"""
'DAO_2024_01_31', 'DAO_2024_02_29', 'DAO_2024_03_31' 
"""

daoFileNames = ['DAO_2024_04_30',
 'DAO_2024_05_31', 'DAO_2024_06_30', 'DAO_2024_07_31', 'DAO_2024_08_31', 'DAO_2024_09_30',
 'DAO_2024_10_31', 'DAO_2024_11_30', 'DAO_2024_12_31', 'DAO_2025_01_31', 'DAO_2025_02_28',
 'DAO_2025_03_31', 'DAO_2025_04_30', 'DAO_2025_05_31', 'DAO_2025_06_30', 'DAO_2025_07_31','DAO_2025_08_31','DAO_2025_09_23']

daoColumns =['EXTRDATE','NOMIS_NO','PRISONName','IMPRISONMENT_STATUS_CATEGORY','SEC_CAT_LONG',
'SEC_CAT_ASSESSMENT_DATE','SEC_CAT_NEXT_REVIEW_DATE','PrisonGender','PrisonPGDRegion','PredominantFunction','PrisonProbationRegion','PrisonEDRegion','SecCatSummary','PrisonEasting','PrisonNorthing','SentenceStatus']

""" IGNORE ALL HERE
pop = pd.read_csv('s3://alpha-omppg/isp-population/raw/DAO_2024_04_30.csv', usecols=daoColumns)
pop.columns = pop.columns.str.upper()
pop['EXTRDATE'] = pd.to_datetime(pop['EXTRDATE'],dayfirst=True)
pop.info()
pop.head()
pop.tail()
del pop

finalList = []

notMatched = remissions.copy()

for fileName in daoFileNames:
    print(fileName)
    daoData = pd.read_csv(f"s3://alpha-omppg/isp-population/raw/{fileName}.csv", usecols=daoColumns)
    daoData.columns = daoData.columns.str.upper()
    daoData['EXTRDATE'] = pd.to_datetime(daoData['EXTRDATE'],dayfirst=True)
    
    query = """SELECT a.*,
                      b.NOMIS_NO,
                      b.SEC_CAT_LONG,
                      b.EXTRDATE,
                      b.IMPRISONMENT_STATUS_CATEGORY,
                      b.PREDOMINANTFUNCTION,
                      b.PRISONEDREGION,
                      b.PRISONPGDREGION,
                      b.PRISONEASTING,
                      b.PRISONNORTHING

                FROM notMatched AS a 
                LEFT JOIN daoData AS b

                ON  a.NOMIS_ID = b.NOMIS_NO AND
                a.DATE_OF_RECEIPT <= b.EXTRDATE"""

    matched = duckdb.sql(query).df()
    notMatched = matched[matched['NOMIS_NO'].isna()].copy()
    #print(notMatched.head())
    notMatched = notMatched.drop(columns=['SEC_CAT_LONG','PREDOMINANTFUNCTION','PRISONEDREGION',
                      'PRISONPGDREGION','PRISONEASTING','PRISONNORTHING'])
    
    matched = matched[matched['NOMIS_NO'].notna()].copy()
    if matched.empty:
        finalList.append(matched)
    
    if notMatched.empty:
        break
        
finalData = pd.concat(finalList, ignore_index=True)
list(finalList)
len(finalList)
len(finalData)
finalData.head()
ispPPUD_Matched.shape # 25410, 25326, 25222, 25147, 25052
"""

# HARD CONCATENATION - desperation
pop =pd.DataFrame()

for fileName in daoFileNames:
    print(fileName)
    daoData = pd.read_csv(f"s3://alpha-omppg/isp-population/raw/{fileName}.csv", usecols=daoColumns)
    pop = pd.concat([pop,daoData])

len(pop) # 1,571,216!
# pop.head()
# pop.info()

pop.columns = pop.columns.str.upper() #upper case column names

pop['EXTRDATE'] = pd.to_datetime(pop['EXTRDATE'],dayfirst=True) # ensure pop data is datetime

# the join, on NOMIS ID and date of application being before NOMIS pop date

query = """SELECT a.*,
                  b.NOMIS_NO,
                  b.SEC_CAT_LONG,
                  b.EXTRDATE,
                  b.IMPRISONMENT_STATUS_CATEGORY,
                  b.PREDOMINANTFUNCTION,
                  b.PRISONEDREGION,
                  b.PRISONPGDREGION,
                  b.PRISONEASTING,
                  b.PRISONNORTHING

            FROM remissions AS a 
            LEFT JOIN pop AS b

            ON  a.NOMIS_ID = b.NOMIS_NO AND
            a.DATE_OF_RECEIPT <= b.EXTRDATE"""

matched = duckdb.sql(query).df()
# matched.head()
# len(matched) # 3493

matched2 = matched.copy() # deep copy

sum(matched2['DATE_OF_RECEIPT'] <= matched2['EXTRDATE']) # silly check, but just to be sure receipt date is before pop date for all

matched2 = matched2.sort_values(['NOMIS_ID','DATE_OF_RECEIPT','EXTRDATE']) # sort, automatically pushes missing pop date(EXTRDATE) last in the order to be exclude on dedup

matched2 = matched2.drop_duplicates(['NOMIS_ID','DATE_OF_RECEIPT'])

len(matched2) # 534 as we started with

# days from receipt to pop date. Around 50 is plausible
matched2['RECEIPT_TO_POP_DATE'] = matched2['EXTRDATE'] - matched2['DATE_OF_RECEIPT'] 

# matched2.head()
pop[pop['NOMIS_NO'].isin(['A0659CE','A5415EY'])] # check one long RECEIPT_TO_POP_DATE. Likely MHCS got the application date wrong

# export
matched2.to_excel("matched.xlsx",index=False)

matched[matched['NOMIS_NO'].isin(['A5415EY'])] # check one long RECEIPT_TO_POP_DATE. Likely MHCS got the application date wrong

