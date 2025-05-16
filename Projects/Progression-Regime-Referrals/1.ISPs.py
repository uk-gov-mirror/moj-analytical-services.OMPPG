""" 
GOAL: PRODUCE ISP and EDS referrals for Progression Regime. 
By Eric Nyame, 17/05/2024
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
import Out_of_bounds_dates
import prepareMatch
import openMatch
import TimeDiffs
import tariff_groups
importlib.reload(tariff_groups)
#----------------------------------Set display options

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
#----------------------------------SOme global variables are from 4 Releases_to_Recall program

month = str(3).zfill(2) # pads a signle number with a leading zero, like '9' -> 09'
day = 31

year = 2025
quarter = 1
#----------------------------------Import NOMIS data

pop = pd.read_csv(f"s3://alpha-omppg/data-central/PR_referrals/DAO_{year}_{month}_{day}.csv")
pop.columns = pop.columns.str.upper()
pop['SENTENCESTATUS'].value_counts()

pop.head()
sentences_to_keep = ['(7) Recall','(6) Life','(5) IPP','(9) Unknown']

pop = pop[pop['SENTENCESTATUS'].isin(sentences_to_keep)]

colKeep = ['AGE','AGEGROUP','COURT_DESC','CRO_NO','DOB','ESTAB','ETHNIC_GROUP_LONG','EXTRDATE','F2052_START','F2052_STATUS','FIRST_MOVEMENT_DATE',
           'FORENAME1','IEP','IMPRISONMENT_STATUS_SHORT','LOCATION','MAIN_OFFENCE_CODE','MAIN_OFFENCE_DESCRIPTION','NATIONALITY_LONG','NOMIS_NO',
           'PNCID_NO','SEC_CAT_LONG','SURNAME','FIRST_SENTENCED','IMPRISONMENT_STATUS_CATEGORY','JISL_DAYS','PRISONGENDER','PRISONNAME','PRISONPGDREGION',
           'PRISONPROBATIONREGION','OFFENDER_GENDER','PED','OFFENCEGROUP','SECCATSUMMARY','HOME_COUNTY','SENTENCE_LENGTH_DAYS','SENTENCE_LENGTH_YEARS',
           'JISL_MONTHS','SED','INDEFINITE_SENTENCE','JISL_YEARS','SENTENCE_LENGTH_BANDED','FNPSTATUS','PREDOMINANTFUNCTION','PRISONEDREGION','ORIGINDISTRICT',
           'ORIGINREGION','COURTNPSREGION','SENTENCESTATUS','SENTENCESTATUSCUSTOM']

pop = pop[colKeep]

pop.head()
pop.info()
#----------------------------------Datetime columns appearing as object type - change

dateColsToChange =['DOB','EXTRDATE','F2052_START','FIRST_MOVEMENT_DATE','FIRST_SENTENCED']

    # change certain columns to pandas datetime type

for column in dateColsToChange:
    pop[column] = pd.to_datetime(pop[column], dayfirst = True)
    
    # Failing which
check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(pop,col)],axis = 0,ignore_index=True)

check1= check1[dateColsToChange + [col for col in pop.columns if col not in dateColsToChange]]
check1.shape # 0
check1

   # Make corrections to dates
for column in dateColsToChange:
    pop.loc[pop[column].astype(str).str.contains('2424'), column] = pop[column].str.replace('2424','2024', regex=True)

# Check again
check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(pop,col)],axis = 0,ignore_index=True)

check1= check1[dateColsToChange + [col for col in pop.columns if col not in dateColsToChange]]
check1.shape # 0

    # change certain columns to pandas datetime type

for column in dateColsToChange:
    pop[column] = pd.to_datetime(pop[column], dayfirst = True)

pop.info()

strip_blanks(pop)

pop = pop.rename(columns ={"ADULT_YP" : "ADULTYPJUVFLAG","AGE" : "AGE","AGEGROUP" : "AGEBAND","BOOKING_CODE" : "LIDS_ID","DOB" : "DATEOFBIRTH",
"ESTAB" : "PRISONCODE","ETHNIC_GROUP_LONG" : "ETHNICITY","ETHNIC_GROUP_SHORT" : "ETHNICITYCODE","EXTRDATE" : "EXTRACTDATE","F2052_START" : "F2052START",
"F2052_STATUS" : "F2052_STATUS","FORENAME1" : "FORENAME","FORENAME2" : "FORENAME2","IEP" : "IEP","IMPRISONMENT_STATUS_LONG" : "IMPRISONMENTSTATUSLONG",
"IMPRISONMENT_STATUS_SHORT" : "IMPRISONMENTSTATUSSHORT","IRCFLAG" : "IRC","LOCATION" : "CELLLOCATION","MAIN_OFFENCE_DESCRIPTION" : "OFFENCE",
"NATIONALITY_LONG" : "NATIONALITYNAME","NATIONALITY_SHORT" : "NATIONALITYCODE","NOMIS_NO" : "NOMIS_ID","MAIN_OFFENCE_DESCRIPTION" : "OFFENCE",
"OFFENCE_GROUP" : "OFFENCEGROUP","PRISON" : "PRISONNAME","PRISONREGION" : "PRISONREGION","SEC_CAT_LONG" : "SEC_CAT_LONG","SEC_CAT_SHORT" : "SECURITYCATEGORY",
"SURNAME" : "SURNAME","SEX" : "GENDER","CUSTYPE" : "CUSTYPE","NATGROUP" : "FNPSTATUS"})

pop['INITIAL'] = pop['FORENAME'].str[0].str.upper()

pop['SENTENCESTATUS'].value_counts(dropna=False)

#---------------------------------- Open condtions

openPrisons = pd.read_excel("~/OMPPG/Supporting-Data/Open-Prisons.xls")
openPrisons.columns = openPrisons.columns.str.upper()
# openPrisons.info()

    # Change bad dates and set datetimes dtype
for col_name in openPrisons.select_dtypes(include='object').columns:
    openPrisons[col_name] = openPrisons[col_name].astype(str).str.replace('9999', f'{pd.Timestamp.max.year - 1}')
        
openPrisons['END'] = pd.to_datetime(openPrisons['END'],dayfirst=True)
openPrisons['TYPEEND'] = pd.to_datetime(openPrisons['TYPEEND'],dayfirst=True)

strip_blanks(openPrisons)
openPrisons = openPrisons.drop_duplicates()
openPrisons.info()

    #Create location variable to identify open conditions in closed prisons*/

pop['LOCATION'] = [x.split('-')[1] if isinstance(x, str) and len(x.split('-')) >= 2 else x for x in pop['CELLLOCATION']]
pop['WING'] = [x.split('-')[2] if isinstance(x, str) and len(x.split('-')) >= 3 else x for x in pop['CELLLOCATION']]

def prog_regime(df):
    
    data = df.copy()
    
    pr1 = (data['PRISONCODE'] == 'WII') & (data['LOCATION'].isin(['A','O','S']))
    pr2 = (data['PRISONCODE'] == 'HMI') & (data['LOCATION'].isin(['G']))
    pr3 = (data['PRISONCODE'] == 'EEI') & (data['LOCATION'].isin(['I','K']))
    pr4 = (data['PRISONCODE'] == 'BCI') & (data['LOCATION'].isin(['C'])) & (data['WING'].isin(['3','4']))
    
    
    data.loc[pr1,'PROGRESSION_REGIME'] = 'Y'
    data.loc[~pr1 & pr2,'PROGRESSION_REGIME'] = 'Y'
    data.loc[~pr1 & ~pr2 & pr3,'PROGRESSION_REGIME'] = 'Y'
    data.loc[~pr1 & ~pr2 & ~pr3 & pr4,'PROGRESSION_REGIME'] = 'Y'
    data.loc[~pr1 & ~pr2 & ~pr3 & ~pr4,'PROGRESSION_REGIME'] = 'N'
            
    return data

pop = prog_regime(pop)
pop.info()

#pop[(pop['PRISONCODE'] == 'WII') & (pop['LOCATION'].isin(['A','O','S']))]['PROGRESSION_REGIME'].unique()
#pop[(pop['PRISONCODE'] == 'EEI') & (pop['LOCATION'].isin(['I','K']))]['PROGRESSION_REGIME'].unique()

# match
pop.info()
pop.head()

duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query = """SELECT a.*, 
                  b.OPEN, 
                  b.OPEN_TYPE
                  
            FROM pop AS a LEFT JOIN openPrisons AS b
            
            ON  a.PRISONCODE = b.PRISONCODE AND
            (a.LOCATION = b.LOCATION or b.LOCATION = 'All') AND
            a.EXTRACTDATE >= b.START AND
            a.EXTRACTDATE <= b.END"""
openMatched = duckdb.sql(query).df()
openMatched.shape # 22572, 21856,21584, 20839

# Create conditions variable
openMatched['CONDITIONS'] = 'Closed'
openMatched.loc[openMatched['OPEN'] =='Yes','CONDITIONS'] = 'Open'
openMatched.loc[openMatched['OPEN_TYPE'].isna(),'CONDITIONS'] = 'Closed'

openMatched = openMatched.drop(['LOCATION','OPEN','WING'], axis = 1)

openMatched.info()

#---------------------------------- Temporary Save or continue to next
# openMatched.to_parquet(f"openMatched.parquet")
