""" 
GOAL: CHECK CAADD FILEREFERENCE FROM OFFENCE DATA TO THE POULATION DATA EMMA SENT ME.

BACKGROUND: WHEN EMMA SENT ME THE POPULATION DATASET, FILEREFERENCES HAD BEEN CORRUPTED IN EXCEL WITH SOMETHING LIKE 03/2667 
BECOMING SOMETHING LIKE MARCH.. IN EXCEL.RODUCE OFFENCE BREAKDOWNSRESTRICTED PATIENTS STATISTICS FOR PUBLICATION

By Eric Nyame, 29/02/2024
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

sys.path.append('/home/jovyan/OMPPG/Macro Library')
# from my_log import my_log
import Out_of_bounds_dates
importlib.reload(Out_of_bounds_dates)
import prepareMatch
importlib.reload(prepareMatch)
import openMatch
importlib.reload(openMatch)
import TimeDiffs

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

year = 2023
snapshotDate = pd.Timestamp(2023,12,31)

#--------------- Import offence and Emma's population dataset.

hmpReveiw = pd.read_excel("s3://alpha-omppg/SFO/HMIP_Reviews.xlsx")
hmpReveiw.head()
hmpReveiw.info()

#----------------------------------Datetime columns appearing as object type - change

dateColsToChange =['Date feedback sent']

check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(hmpReveiw,col)],axis = 0,ignore_index=True)

check1= check1[dateColsToChange + [col for col in hmpReveiw.columns if col not in dateColsToChange]]
check1.shape # 0
check1
    # change certain columns to pandas datetime type

for column in dateColsToChange:
    hmpReveiw[column] = pd.to_datetime(hmpReveiw[column], errors='coerce')
    
hmpReveiw['Type of QA '].value_counts(dropna=False)

hmpReveiw =hmpReveiw[~hmpReveiw['Type of QA '].astype(str).str.contains('Resub',case=False)].copy()

hmpReveiw['Type of QA '].value_counts(dropna=False)

hmpReveiw['Quality Assurer'].value_counts(dropna=False)

hmpReveiw['Quality_Assurer2']= "PPG"
hmpReveiw.loc[hmpReveiw['Quality Assurer'].astype(str).str.contains('HMIP',case=False),'Quality_Assurer2'] ='HMIP'

hmpReveiw.cros['Quality Assurer'].value_counts(dropna=False)

pd.crosstab(hmpReveiw['Quality Assurer'],hmpReveiw['Quality_Assurer2'])

# Tabulate
hmpReveiw['Composite rating'] = hmpReveiw['Composite rating'].astype(str).str.strip().str.upper()
hmpReveiw['Composite rating'] = pd.Categorical(hmpReveiw['Composite rating'], ordered=True, categories=['OUTSTANDING','GOOD','REQUIRES IMPROVEMENT','INADEQUATE'])

y_22_23 = (hmpReveiw['Date feedback sent'].dt.normalize() >= pd.Timestamp(2022,4,1)) & (hmpReveiw['Date feedback sent'].dt.normalize() <= pd.Timestamp(2023,3,31))

pd.crosstab(hmpReveiw[y_22_23]['Composite rating'],hmpReveiw[y_22_23]['Quality_Assurer2'])

y_23_24 = (hmpReveiw['Date feedback sent'].dt.normalize() >= pd.Timestamp(2023,4,1)) & (hmpReveiw['Date feedback sent'].dt.normalize() <= pd.Timestamp(2024,3,31))

pd.crosstab(hmpReveiw[y_23_24]['Composite rating'],hmpReveiw[y_23_24]['Quality_Assurer2'])

y_22_24 = (hmpReveiw['Date feedback sent'].dt.normalize() >= pd.Timestamp(2022,4,1)) & (hmpReveiw['Date feedback sent'].dt.normalize() <= pd.Timestamp(2024,3,31))

pd.crosstab(hmpReveiw[y_22_24]['Composite rating'],hmpReveiw[y_22_24]['Quality_Assurer2'])
