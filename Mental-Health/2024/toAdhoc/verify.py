""" 
GOAL: PRODUCE RESTRICTED PATIENTS STATISTICS FOR PUBLICATION
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
import prepareMatch
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
         scrollY="500px", 
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

ippsInHospital = pd.read_parquet(f"s3://alpha-omppg/Mental-Health/2024/output/population_prepared_2024.parquet")

"""
ippsInHospital['DA_CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

"""

ippsInHospital = ippsInHospital[ippsInHospital['DA_CUSTODY_TYPE_DESCRIPTION'].isin(['IPP','DPP'])]

recallsPPUD = pd.read_excel(f's3://alpha-omppg/Recalls/PPUD/ISP/PPUD_ISP_Recalls_2024Q4.xls')

strip_blanks(recallsPPUD)

ippsInHospital = pop.drop_duplicates()

recallsPPUD =recallsPPUD.drop_duplicates()

"""
recallsPPUD['LICENCE_REVOKE_DATE'].max()
"""

recallsPPUD['LICENCE_REVOKE_DATE'] = recallsPPUD['LICENCE_REVOKE_DATE'].dt.normalize()

#----------------------------------Match

# duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query = """SELECT a.*, 
                  b.LICENCE_REVOKE_DATE
                  
            FROM ippsInHospital AS a 
            LEFT JOIN recallsPPUD AS b
            
            ON  
                (
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL)
                ) """

matched = duckdb.sql(query).df()
"""
matched.shape # 

matched.head()
"""
matched = matched.sort_values(by=['FILE_REFERENCE','LICENCE_REVOKE_DATE'],ascending = [True,False])

matched = matched.drop_duplicates(subset='FILE_REFERENCE', keep ='first').copy()

"""
len(matched) #233
"""

matched['STATUS'] = 'Recalled'
matched.loc[matched['LICENCE_REVOKE_DATE'].isna(),'STATUS'] = 'Unreleased'

matched['STATUS'].value_counts(dropna=False)


# EVER IN HOSPITAL#######################################################################################

nomis = pd.read_parquet("s3://alpha-omppg/isp-population/final/isp_pop_2024q4.parquet")

"""
nomis['EXTRACTDATE'].value_counts()
"""
nomis = nomis[nomis['ISP_STATUS'].isin(['Unreleased IPP','Recalled IPP'])]

"""
len(nomis)
"""
# nomis.to_excel("ipp_nomis_Dec2024.xlsx",index=False)
ippRPEver = pd.read_excel("ipps_RP_ever.xls")

ippRPEver = prepareMatch.prepareMatch(ippRPEver)

"""
sum(ippRPEver['FILE_REFERENCE'].isna()) # 0
sum(ippRPEver['PRISON_NUMBER'].isna()) # 0
sum(ippRPEver['NOMS_ID'].isna()) # 86

sum(nomis['PRISON_NUMBER'].isna()) # 0
"""

#---------------------------------- Match

query2 = """SELECT DISTINCT a.*, 
                            b.PRISON_NUMBER AS PN
            
                    FROM nomis AS a LEFT JOIN ippRPEver AS b
                   ON  a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL"""


matched2 = duckdb.sql(query2).df()
"""
matched2.shape # 2614
"""

matched2['EVER'] = 1
matched2.loc[matched2['PN'].isna(),'EVER'] = 0

"""
matched2['EVER'].value_counts(dropna=False)
"""
matched2.to_excel('ipp_prison_ever.xlsx',index=False)
