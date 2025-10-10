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

# remissions = pd.read_csv("remissions.csv")
remissions = pd.read_excel("remissions_actuals.xlsx")
remissions.head()
len(remissions) # 607

sum(remissions.duplicated(['FILE_REFERENCE','ACTUAL_DATE'],keep=False))
remissions[remissions.duplicated(['FILE_REFERENCE','ACTUAL_DATE'],keep=False)]

remissions = remissions.drop([201,602])

"""
originalRemissionFields = ['DATE_OF_RECEIPT', 'Surname', 'FirstName', 'Dateofbirth', 'NOMS_ID',
       'PPUD_REF', 'Prison', 'B4', 'Emergencyrequest', 'NationalRegion',
       'HMPPS region  - England, Private Male/Female, YOI, Immigration, Womens, Wales, and LTHSE',
       'TypeofSection', 'Warrant',  'Comments']
       
remissions = remissions[originalRemissionFields]
remissions.columns = remissions.columns.str.upper()

# rename some columns
remissions = remissions.rename(columns={
    'HMPPS REGION  - ENGLAND, PRIVATE MALE/FEMALE, YOI, IMMIGRATION, WOMENS, WALES, AND LTHSE':'HMPPS REGION',
    'WARRANT':'DATE_OF_WARRANT',
    'COMMENTS':'DATE_OF_REMISSION'
})
"""
remissions.info()

"""
remissions['DATE_OF_RECEIPT'] = pd.to_datetime(remissions['DATE_OF_RECEIPT'],dayfirst=True)

remissions['DATE_OF_WARRANT'] = pd.to_datetime(remissions['DATE_OF_WARRANT'],dayfirst=True,errors='coerce')

remissions['DATE_OF_REMISSION'] = pd.to_datetime(remissions['DATE_OF_REMISSION'],dayfirst=False,errors='coerce') # note false dayfirst
"""

strip_blanks(remissions) # trim fields

# remissions.info()

"""
# Warrant (acceptance) before application?
sum(remissions['DATE_OF_RECEIPT'] > remissions['DATE_OF_WARRANT']) # 3 abnormal cases
remissions[remissions['DATE_OF_RECEIPT'] > remissions['DATE_OF_WARRANT']]

# Three abnormal cases corrected manuall from PPUD checks
sum(remissions['NOMS_ID']=='A4897EP') # 1 case
remissions.loc[remissions['NOMS_ID']=='A4897EP','DATE_OF_RECEIPT']=pd.Timestamp(2024,5,22)

sum(remissions['NOMS_ID']=='A9677EV') # 1 case
remissions.loc[remissions['NOMS_ID']=='A9677EV','DATE_OF_WARRANT']=pd.Timestamp(2024,4,12)

sum(remissions['NOMS_ID']=='A4847AK') # 1 case
remissions.loc[remissions['NOMS_ID']=='A4847AK','DATE_OF_WARRANT']=pd.Timestamp(2025,6,13)
remissions.loc[remissions['NOMS_ID']=='A4847AK','DATE_OF_REMISSION']=pd.Timestamp(2025,6,19)

# Warrant (acceptance) before application?
sum(remissions['DATE_OF_RECEIPT'] > remissions['DATE_OF_REMISSION']) # 0 

# latest date
remissions['ACTUAL_DATE'] = remissions[
                            ["DATE_OF_RECEIPT",
                             "DATE_OF_WARRANT",
                             "DATE_OF_REMISSION"]].max(axis=1)

# remissions.head()

# len(remissions) # 534
"""

# ------------------- Bring in NOMIS data

pop = pd.read_csv(f"s3://alpha-omppg/Projects/2025-09-23-MHCS-Sec-Cat-PGD/DAO_combined_filtered.csv")

len(pop) # 200690
pop.head()
pop.info()
pop.columns = pop.columns.str.upper() #upper case column names

strip_blanks(pop)

pop['EXTRDATE'] = pd.to_datetime(pop['EXTRDATE'],format='mixed',dayfirst=True) # ensure pop data is datetime

# the join, on NOMIS ID and date of application being before NOMIS pop date

sum(remissions['ACTUAL_DATE'].isna()) # 0

query = """SELECT a.*,
                  b.*
            FROM remissions AS a 
            LEFT JOIN pop AS b
            
            ON  a.NOMS_ID = b.NOMIS_NO """

matched = duckdb.sql(query).df()
# matched.head()
# len(matched) # 197055

matched2 = matched.copy() # deep copy

sum(matched2['ACTUAL_DATE'] > matched2['EXTRDATE']) # 64398

# days from actual to pop date. Around 50 is plausible
matched2['ACTUAL_TO_POP_DATE'] = matched2['EXTRDATE'] - matched2['ACTUAL_DATE'] 


sum(remissions.duplicated(subset=['NOMS_ID','ACTUAL_DATE'],keep=False)) # 0 duplicates by the two

matched2 = matched2.sort_values(['NOMS_ID','ACTUAL_DATE','EXTRDATE']) # sort, automatically pushes missing pop date(EXTRDATE) last in the order to be exclude on dedup

matched2 = matched2.drop_duplicates(['NOMS_ID','ACTUAL_DATE'])

len(matched2) # 534 as we started with



# matched2.head()

matched2['ACTUAL_TO_POP_DATE'].max() # 289 days
sum(matched2['ACTUAL_TO_POP_DATE'] > '30 days') # 7
matched2[matched2['ACTUAL_TO_POP_DATE'] > '30 days'][['NOMS_ID','SURNAME','DATE_OF_RECEIPT','DATE_OF_WARRANT','DATE_OF_REMISSION','ACTUAL_DATE','EXTRDATE','ACTUAL_TO_POP_DATE','TYPEOFSECTION']]

# post match corrections from PPUD for two TYPEOFSECTION = 47
sum(remissions['NOMS_ID']=='A7328CA') # 1 case, Actual remission date on PPUD is 27 May 2025
matched2.loc[matched2['NOMS_ID']=='A7328CA','DATE_OF_REMISSION']=pd.Timestamp(2025,5,27)
matched2.loc[matched2['NOMS_ID']=='A7328CA','ACTUAL_DATE']=pd.Timestamp(2025,5,27)
matched2.loc[matched2['NOMS_ID']=='A7328CA','ACTUAL_TO_POP_DATE']= matched2['EXTRDATE'] - matched2['ACTUAL_DATE'] 

sum(remissions['NOMS_ID']=='A3873ET') # 1 case, Actual remission date on PPUD is 26 September 2024
matched2.loc[matched2['NOMS_ID']=='A3873ET','DATE_OF_REMISSION']=pd.Timestamp(2024,9,26)
matched2.loc[matched2['NOMS_ID']=='A3873ET','ACTUAL_DATE']=pd.Timestamp(2024,9,26)
matched2.loc[matched2['NOMS_ID']=='A3873ET','ACTUAL_TO_POP_DATE']= matched2['EXTRDATE'] - matched2['ACTUAL_DATE'] 

# remainin 5 cases with number of days from ACTUAL_DATE to EXTRDATE are 48s who have no sec category

# export
matched2.to_excel("matched.xlsx",index=False)


