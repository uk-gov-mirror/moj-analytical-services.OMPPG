""" 
GOAL: PRODUCE ISP POP FOR OMSQ. 
By Eric Nyame, 05/02/2024
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
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #
        
#----------------------------------SOme global variables are from 4 Releases_to_Recall program

month = str(6).zfill(2) # pads the number with a leading zero
day = 30
year = 2025
quarter = 2

#----------------------------------Import NOMIS data

pop = pd.read_csv(f's3://alpha-omppg/isp-population/raw/DAO_{year}_{month}_{day}.csv')

pop['EXTRDATE'].value_counts()

pop.head()

# keep only certain sentences
pop['SentenceStatus'].value_counts(dropna=False)

sentences_to_keep = ['(7) Recall','(6) Life','(5) IPP','(9) Unknown','(1) Remand','(8) Non Criminal']

pop = pop[pop['SentenceStatus'].isin(sentences_to_keep)]

pop.columns = pop.columns.str.upper()

colKeep = ['AGE', 'LAST_MOVEMENT_DIRECTION', 'SEXUAL', 'AGEGROUP', 'LAST_MOVEMENT_FROM', 'SURNAME', 'CRO_NO', 'LAST_MOVEMENT_REASON', 'VIOLENT', 'CSRA_LEVEL', 'LAST_MOVEMENT_TO', 'PRISONGENDER', 'DATE_OF_RELEASE', 'LAST_MOVEMENT_TYPE', 'PRISONPGDREGION', 'DOB', 'LOCATION', 'FNPSTATUS', 'DRUG_OFFENCES', 'MAIN_OFFENCE_DESCRIPTION', 'PREDOMINANTFUNCTION', 'ESTAB', 'MAIN_OFFENCE_STATUTE', 'PRISONPROBATIONREGION', 'ETHNIC_GROUP_LONG', 'MARITAL_STATUS_LONG', 'PRISONEDREGION', 'EXTRDATE', 'MATERNITY_ONGOING_OR_INACTIVE', 'SECCATSUMMARY', 'F2052_START', 'MATERNITY_STATUS_LONG', 'OFFENCEGROUP', 'F2052_STATUS', 'NATIONALITY_LONG', 'SENTENCESTATUS', 'SEX_OFFENDER_REGISTER', 'FIRST_CONVICTED', 'NOMIS_NO', 'IMPRISONMENT_STATUS_SHORT', 'FIRST_MOVEMENT_DATE', 'OFFENDER_GENDER', 'FIRST_SENTENCED', 'PNCID_NO', 'FORENAME1', 'PRISONNAME', 'IEP', 'RELIGION_LONG', 'IMPRISONMENT_STATUS_CATEGORY', 'SEC_CAT_ASSESSMENT_DATE', 'INDEFINITE_SENTENCE', 'SEC_CAT_LONG', 'LAST_MOVEMENT_DATE']

pop = pop[colKeep]

pop.info()
#----------------------------------Datetime columns appearing as object type - change

pop.select_dtypes(include=['object']).dtypes # find datetime column showing as an objec

dateColsToChange =['DATE_OF_RELEASE','DOB','EXTRDATE','F2052_START','FIRST_CONVICTED','FIRST_MOVEMENT_DATE','FIRST_SENTENCED','SEC_CAT_ASSESSMENT_DATE','LAST_MOVEMENT_DATE']

check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(pop,col)],axis = 0,ignore_index=True)

check1= check1[dateColsToChange + [col for col in pop.columns if col not in dateColsToChange]]
check1.shape # 0
check1

   # Make corrections to dates
for column in dateColsToChange:
    pop.loc[pop[column].astype(str).str.contains('/2525'), column] = pop[column].str.replace('/2525','/2025', regex=True)

# Check again
check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(pop,col)],axis = 0,ignore_index=True)

check1= check1[dateColsToChange + [col for col in pop.columns if col not in dateColsToChange]]
check1.shape # 0

    # change certain columns to pandas datetime type

for column in dateColsToChange:
    pop[column] = pd.to_datetime(pop[column], dayfirst = True)

pop.select_dtypes(include=['datetime64']).dtypes

strip_blanks(pop)

pop = pop.rename(columns ={"AGEGROUP" : "AGEBAND", "LOCATION" : "CELLLOCATION", "DOB" : "DATEOFBIRTH", 
                           "DATE_OF_RELEASE" : "DATEOFRELEASE","ETHNIC_GROUP_LONG" : "ETHNICGROUP","EXTRDATE" : "EXTRACTDATE",
                           "F2052_START" : "F2052START","FIRST_CONVICTED" : "FIRSTCONVICTED","FIRST_MOVEMENT_DATE" : "FIRSTMOVEMENT",
                           "FIRST_SENTENCED" : "FIRSTSENTENCED","FORENAME1" : "FORENAME","OFFENDER_GENDER" : "GENDER",
                           "IMPRISONMENT_STATUS_SHORT" : "IMPRISONMENTSTATUSSHORT","PREDOMINANTFUNCTION" : "MAINFUNCTION",
                           "MARITAL_STATUS_LONG" : "MARITALSTATUS","MATERNITY_STATUS_LONG" : "MATERNITYSTATUS","NATIONALITY_LONG" : "NATIONALITYNAME",
                           "NOMIS_NO" : "NOMIS_ID","MAIN_OFFENCE_DESCRIPTION" : "OFFENCE","ESTAB" : "PRISONCODE","RELIGION_LONG" : "RELIGION",
                           "SEC_CAT_LONG" : "SECURITYCATEGORY"})

pop['SENTENCESTATUS'].value_counts(dropna=False)

#---------------------------------- Subset

def pop_subset(df):
    
    data = df.copy()
    
    data['INITIAL'] = data['FORENAME'].str[0].str.upper()
    
    vat = data['OFFENCEGROUP'].isin(['(1) VATP','01 Violence against the person'])
    sex = data['OFFENCEGROUP'].isin(['(2) Sex offences','02 Sexual offences'])
    rob = data['OFFENCEGROUP'].isin(['(3) Robbery','03 Robbery'])
    
    data.loc[vat,'OFFGRP4'] = 'VATP'
    data.loc[~vat & sex,'OFFGRP4'] = 'Sex offences'
    data.loc[~vat & ~sex & rob,'OFFGRP4'] = 'Robbery'
    data.loc[~vat & ~sex & ~rob,'OFFGRP4'] = 'Other'

    ofg2sex = data['OFFGRP4'] == 'Sex offences'
    ofg2rob = data['OFFGRP4'].isin(['VATP','Robbery','Other'])
    
    data.loc[ofg2sex,'OFFGRP2'] = 'Sexual'
    data.loc[~ofg2sex & ofg2rob,'OFFGRP2'] = 'non-Sexual'
    
    unknown = data['SENTENCESTATUS'].isin(['', '(9) Unknown'])
    ipp = data['IMPRISONMENTSTATUSSHORT'] == 'ISPPCJ03'
    life = data['IMPRISONMENTSTATUSSHORT'].isin(['LIFE','MLP','SEC93/03'])
    recall = data['IMPRISONMENTSTATUSSHORT'].isin(['LR','LR/EX/ST','LRE/CJ03','LRI/CJ03'])
    
    data.loc[unknown & ipp, 'SENTENCESTATUS'] = '(5) IPP'
    data.loc[unknown & ~ipp & life, 'SENTENCESTATUS'] = '(6) Life'
    data.loc[unknown & ~ipp & ~life & recall, 'SENTENCESTATUS'] = '(7) Recall'
    data.loc[unknown & ~ipp & ~life & ~recall, 'SENTENCESTATUS'] = np.nan
    
    data = data[data['SENTENCESTATUS'].isin(['(5) IPP','(6) Life','(7) Recall'])]
            
    return data

# Check unknown cases before applying function to data
pop['SENTENCESTATUS'].value_counts(dropna=False)

pop[(pop['SENTENCESTATUS'].isin(['', '(9) Unknown'])) &
   (pop['IMPRISONMENTSTATUSSHORT'].isin(['LIFE','MLP','SEC93/03','ISPPCJ03','LR','LR/EX/ST','LRE/CJ03','LRI/CJ03']))]['IMPRISONMENTSTATUSSHORT'].value_counts(dropna=False) # none, so the function only removes unknown cases

pop2 = pop_subset(pop)

pop2.shape # 22029, 22086,21413,21080,20722

pop2['SENTENCESTATUS'].value_counts(dropna=False)

#---------------------------------- Open condtions

openPrisons = pd.read_excel("~/OMPPG/Supporting-Data/Open-Prisons.xls")
openPrisons.columns = openPrisons.columns.str.upper()
openPrisons.info()

    # Change bad dates and set datetimes dtype
for col_name in openPrisons.select_dtypes(include='object').columns:
    openPrisons[col_name] = openPrisons[col_name].astype(str).str.replace('9999', f'{pd.Timestamp.max.year - 1}')
        
openPrisons['END'] = pd.to_datetime(openPrisons['END'],dayfirst=True)
openPrisons['TYPEEND'] = pd.to_datetime(openPrisons['TYPEEND'],dayfirst=True)

strip_blanks(openPrisons)
openPrisons = openPrisons.drop_duplicates()
openPrisons.info()

    #Create location variable to identify open conditions in closed prisons*/

pop2['LOCATION'] = [x.split('-')[1] if isinstance(x, str) and len(x.split('-')) >= 2 else x for x in pop2['CELLLOCATION']]
pop2['WING'] = [x.split('-')[2] if isinstance(x, str) and len(x.split('-')) >= 3 else x for x in pop2['CELLLOCATION']]

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

pop2 = prog_regime(pop2)
pop2.info()

pop2[(pop2['PRISONCODE'] == 'WII') & (pop2['LOCATION'].isin(['A','O','S']))]['PROGRESSION_REGIME'].unique()
pop2[(pop2['PRISONCODE'] == 'EEI') & (pop2['LOCATION'].isin(['I','K']))]['PROGRESSION_REGIME'].unique()

# match
duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query = """SELECT a.*, 
                  b.OPEN, 
                  b.OPEN_TYPE
                  
            FROM pop2 AS a LEFT JOIN openPrisons AS b
            
            ON  a.PRISONCODE = b.PRISONCODE AND
            (a.LOCATION = b.LOCATION or b.LOCATION = 'All') AND
            a.EXTRACTDATE >= b.START AND
            a.EXTRACTDATE <= b.END"""
openMatched = duckdb.sql(query).df()
openMatched.shape # 22029, 22086, 21413, 21080, 20722,20870

# Create conditions variable
openMatched['CONDITIONS'] = 'Closed'
openMatched.loc[openMatched['OPEN'] =='Yes','CONDITIONS'] = 'Open'
openMatched.loc[openMatched['OPEN_TYPE'].isna(),'CONDITIONS'] = 'Closed'

openMatched.info()

openMatched[openMatched['OPEN'] =='Yes']['CONDITIONS'].value_counts(dropna = False)
openMatched[openMatched['OPEN_TYPE'].isna()]['CONDITIONS'].value_counts(dropna = False)

openMatched = openMatched.drop(['LOCATION','OPEN','WING'], axis = 1)

#---------------------------------- Temporary Save, delete later
openMatched.to_parquet(f"openMatched.parquet")
