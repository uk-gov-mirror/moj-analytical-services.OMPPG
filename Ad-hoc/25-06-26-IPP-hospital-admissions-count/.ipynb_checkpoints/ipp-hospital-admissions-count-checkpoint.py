""" 
GOAL: PRODUCE ADMISSION AaND RECALL STATISTICS FOR RESTRICTED PATIENT PUBLICATION
By Eric Nyame, 29/02/2024
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
# from my_log import my_log
import Out_of_bounds_dates
# import prepareMatch
# importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
import TimeDiffs

#----------------------------------Set display options

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

# Function to identify where bad datetime value is. Pass in the 

def dateOutOfBoundsColumn(dataset,value): # pass in the out-of-bounds date
    for col in dataset.columns:
        # Convert the column to string and check if any value contains the problematic date substring
        if dataset[col].astype(str).str.contains(value).any():
            hmm = dataset[col].astype(str).str.contains(value)
            cols_to_keep = ['NOMIS_ID','SURNAME','EXTRACTDATE',col]
            display(dataset[hmm][cols_to_keep])
            break

#dateOutOfBoundsColumn(pop,'9999-03-30')

# Function to show table in my preferred way
def show_data(data):
    show(data,
         scrollY="200px", 
         scrollCollapse=True, 
         paging=False,
         buttons=["excelHtml5"])

#************* MAIN ADMISSION CATEGORIES**********************************
"""
s45A/s45B = HOSPTAL DIRECTIONS. Court convicts but directs to hospital. 
       Prison sentence to be served after successful treatment in hospital.
    
s37/s41 = HOSPITAL ORDER with RESTRICTIONS added. 
          Issued by the court. Patient could be unfit or not guilty by insanity.
          Not guilty by isanity does not mean they didn't commit the offence?


s47/s49 =  TRANSFER OF CONVICTED PRISONERS with RESTRICTIONS added
           Secretary of State transfers a CONVICTED prisoner from prison to hospital. 

s48/s49 = TRANSFER OF UNCONVICTED PRISONERS with RESTRICTIONS added.
          Secretary of State transfers an UNSENTENCED prisoner from prison to hospital. 
          This could include remand, immigration detainees, unsentenced prisoners, civil prisoners.
"""
#*********************************************************************

#----------------------------------Set globals

year = 2024
# snapshotDate = pd.Timestamp(2023,12,31)

#--------------- Import the population dataset and replace long dash with normal dash

admissions = pd.read_excel(f"s3://alpha-omppg/Ad-hoc/Mental-Health/restricted_patients_admissions_up_to_Dec2024.xls")
sentence = pd.read_excel(f's3://alpha-omppg/isp-population/PPUD/2024Q4/PPUD_ISP_2024Q4.xls')


admissions.head()
admissions['ACTUAL_DATE'].max()
len(admissions) # 43494

admissions = admissions.replace("–","-", regex = True)
sentence = sentence.replace("–","-", regex = True)

    # check datetime types
admissions.info() # all good

admissions.head()

    # rearrange columns
# admissions.columns

retain_order = ['FILE_REFERENCE', 'FAMILY_NAME', 'ACTUAL_DATE',  'MOVE_TYPE_DESCRIPTION','MOVE_SUB_TYPE_DESCRIPTION',
                'MOVE_SUB_SUB_TYPE_DESCRIPTION','FROM_ESTABLISHMENT_DESCRIPTION','TO_ESTABLISHMENT_DESCRIPTION']

admissions = admissions[retain_order + [col for col in admissions.columns if col not in retain_order]]

admissions.head()
admissions.info()
admissions['TO_ESTABLISHMENT_DESCRIPTION'].value_counts(dropna=False)
#---------------Remove duplicates

admissions[admissions.duplicated(subset=['FILE_REFERENCE','ACTUAL_DATE'],keep = False)].sort_values(['FILE_REFERENCE','ACTUAL_DATE']) # 2 dups

admissions = admissions.drop_duplicates(['FILE_REFERENCE','ACTUAL_DATE'])
len(admissions) # 43445

ipps = sentence[sentence['CUSTODY_TYPE_DESCRIPTION'].isin(['IPP','DPP'])]
ipps['DOS'].min()

ipps = ipps[(ipps['DOS'].dt.year > 2004) &(ipps['DOS'].dt.year < 2016)]
ipps['DOS'].dt.year.value_counts()
ipps.head()
len(ipps) # 8116

query = """SELECT a.*, 
                  b.DOS,
                  b.TARIFF_EXPIRY_DATE,
                  b. CUSTODY_TYPE_DESCRIPTION
                  
            FROM admissions AS a 
            LEFT JOIN ipps AS b
            
            ON  a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE NOT NULL"""

matched = duckdb.sql(query).df()
matched.shape # 43457

matched = matched.sort_values(['FILE_REFERENCE','ACTUAL_DATE','DOS'])

matched[matched.duplicated(['FILE_REFERENCE','ACTUAL_DATE'],keep=False)]

matched = matched.drop_duplicates(['FILE_REFERENCE','ACTUAL_DATE'])
matched.shape # 43445

matched.head()

proper = matched[matched['ACTUAL_DATE'] > matched['DOS']]
len(proper) # 1177

proper.loc[:,'COUNT'] = proper.groupby('FILE_REFERENCE')['ACTUAL_DATE'].transform('count')

proper['COUNT'].max()
proper['COUNT'].value_counts()
proper.head()
proper['CUSTODY_TYPE_DESCRIPTION'].value_counts()
proper[['CUSTODY_TYPE_DESCRIPTION','CUSTODY_TYPE_DESCRIPTION_1']].value_counts()
proper.pivot_table(index=['CUSTODY_TYPE_DESCRIPTION','CUSTODY_TYPE_DESCRIPTION_1'],aggfunc='size')

proper[proper['CUSTODY_TYPE_DESCRIPTION'] != proper['CUSTODY_TYPE_DESCRIPTION_1']][['FILE_REFERENCE','CUSTODY_TYPE_DESCRIPTION','CUSTODY_TYPE_DESCRIPTION_1','COUNT']]

proper.to_excel('Admissions_counts_ipp.xlsx',index=False)