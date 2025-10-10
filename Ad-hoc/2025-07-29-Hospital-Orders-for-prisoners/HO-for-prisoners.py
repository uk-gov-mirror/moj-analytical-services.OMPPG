""" 
GOAL: Identify offenders with Hospital Orders (37/41) who were transferred from prison initially (48/49).

"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib

import re

from dateutil.relativedelta import relativedelta

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


#----------------------------------  IMPORT OFFENCE DATA - RUN YOUR OWN OFFENCE DATA CAPTURING EVERYTHING;

#pop['FILE_REFERENCE'].to_excel("File_Ref.xlsx",index=False) # used this to check the offence data from Emma

offences = pd.read_excel("s3://alpha-omppg/Ad-hoc/Mental-Health/offences_48_49_37_41.xlsx")
admissions = pd.read_excel("s3://alpha-omppg/Ad-hoc/Mental-Health/HO-admissions-2024.xlsx")

offences = offences.replace("–","-",regex=True)
admissions = admissions.replace("–","-",regex=True)

admissions['AUTHORITY_FOR_DETENTION_DESCRIPTION'].value_counts()

admissions = admissions[admissions['AUTHORITY_FOR_DETENTION_DESCRIPTION'] =='S37/41 - MHA 1983 - Hospital Order']

offences.head()
admissions.head()
len(offences) # 44208

# Keep only s48/49 wiith links to s37/41
offences['AUTHORITY_FOR_DETENTION_DESCRIPTION'].value_counts(dropna=False)

fileReferenceWithHO = offences.loc[offences['AUTHORITY_FOR_DETENTION_DESCRIPTION'] == 'S37/41 - MHA 1983 - Hospital Order', 'FILE_REFERENCE'].unique()

offences = offences[
    offences['FILE_REFERENCE'].isin(fileReferenceWithHO)
]

"""
offences[offences['FILE_REFERENCE'] == 'MHU_406084']
"""
len(offences) # 22950
offences['AUTHORITY_FOR_DETENTION_DESCRIPTION'].value_counts(dropna=False)

offences['FILE_REFERENCE'] = offences['FILE_REFERENCE'].astype(str)

offences = offences.sort_values(by =["FILE_REFERENCE"])

retain_order = ['FILE_REFERENCE', 'FAMILY_NAME', 'DATE_OF_HOSPITAL_ORDER','DATE_RECEIVED_IN_MHU',
                'AUTHORITY_FOR_DETENTION_DESCRIPTION','OFFENCE_DESCRIPTION',
                'OFFENCE_GROUP_DESCRIPTION']

offences = offences[retain_order + [col for col in offences.columns if col not in retain_order]]

offences.head(10)

# We will deduplicate the offences after the match 

admissions['FILE_REFERENCE'] = admissions['FILE_REFERENCE'].astype(str)

query = """SELECT a.*, 
                  b.ACTUAL_DATE,
                  b.APPLICATION_RECEIVED_IN_MHU,
                  b.AUTHORISATION_DATE,
                  b.MOVE_TYPE_DESCRIPTION,
                  b.AUTHORITY_FOR_DETENTION_DESCRIPTION AS ADMIN_AUTH
                  
            FROM offences AS a LEFT JOIN admissions AS b
            
            ON  (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) AND
                    
                (
                    (a.DATE_OF_HOSPITAL_ORDER = b.ACTUAL_DATE AND a.DATE_OF_HOSPITAL_ORDER IS NOT NULL) OR
                    (a.DATE_OF_HOSPITAL_ORDER = b.AUTHORISATION_DATE AND a.DATE_OF_HOSPITAL_ORDER IS NOT NULL) OR 
                    (a.DATE_OF_HOSPITAL_ORDER = b.APPLICATION_RECEIVED_IN_MHU AND a.DATE_OF_HOSPITAL_ORDER IS NOT NULL) OR

                    (a.DATE_RECEIVED_IN_MHU = b.ACTUAL_DATE AND a.DATE_RECEIVED_IN_MHU IS NOT NULL) OR
                    (a.DATE_RECEIVED_IN_MHU = b.AUTHORISATION_DATE AND a.DATE_RECEIVED_IN_MHU IS NOT NULL) OR
                    (a.DATE_RECEIVED_IN_MHU = b.APPLICATION_RECEIVED_IN_MHU AND a.DATE_RECEIVED_IN_MHU IS NOT NULL)
                ) """

matched = duckdb.sql(query).df()
len(matched) # 22950 no duplicates

fileReferenceWithActual = matched.loc[~matched['ACTUAL_DATE'].isna(), 'FILE_REFERENCE'].unique()

matched = matched[
    matched['FILE_REFERENCE'].isin(fileReferenceWithActual)
]

len(matched) # 791 no duplicates

"""
matched[matched['FILE_REFERENCE'] == 'MHU_406084']
matched[matched['FILE_REFERENCE'] == '3/8587']
"""

# Keep only s37/41/41 with links to 48/49
matched['AUTHORITY_FOR_DETENTION_DESCRIPTION'].value_counts(dropna=False)

fileReferenceWith48 = matched.loc[matched['AUTHORITY_FOR_DETENTION_DESCRIPTION'].str.contains('48'), 'FILE_REFERENCE'].unique()

with_48_49 = matched[
    matched['FILE_REFERENCE'].isin(fileReferenceWith48)
]

len(with_48_49) # 610

with_48_49 = with_48_49.sort_values(by =["FILE_REFERENCE"])

with_48_49.head(10)

retain_order = ['FILE_REFERENCE', 'FAMILY_NAME', 'DATE_OF_HOSPITAL_ORDER','DATE_RECEIVED_IN_MHU',
                'ACTUAL_DATE','AUTHORISATION_DATE','APPLICATION_RECEIVED_IN_MHU',
                'AUTHORITY_FOR_DETENTION_DESCRIPTION','OFFENCE_DESCRIPTION',
                'OFFENCE_GROUP_DESCRIPTION']

with_48_49 = with_48_49[retain_order + [col for col in with_48_49.columns if col not in retain_order]]

"""
with_48_49[with_48_49['FILE_REFERENCE'] == 'MHU_406084']
"""
with_48_49.head(10)

keep48s = with_48_49[with_48_49['AUTHORITY_FOR_DETENTION_DESCRIPTION'].str.contains('48')]
keep37s = with_48_49[with_48_49['AUTHORITY_FOR_DETENTION_DESCRIPTION'].str.contains('37')]

len(keep48s) # 344
len(keep37s) # 266

keep48s = keep48s.rename(columns={'DATE_OF_HOSPITAL_ORDER':'AUTH_48_DOHO',
                         'DATE_RECEIVED_IN_MHU':'AUTH_48_DRIM',
                         'AUTHORITY_FOR_DETENTION_DESCRIPTION':'AUTH_48',
                                 'OFFENCE_DESCRIPTION':'AUTH_48_OFFENCE'})

query2 = """SELECT a.*, 
                  b.AUTH_48,
                  b.AUTH_48_DOHO,
                  b.AUTH_48_DRIM,
                  b.AUTH_48_OFFENCE
                  
            FROM keep37s AS a LEFT JOIN keep48s AS b
            
            ON  (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) AND 
            (a.OFFENCE_DESCRIPTION = b.AUTH_48_OFFENCE) """

matched2 = duckdb.sql(query2).df()
len(matched2) # 276 more than 84

matched2['AUTH_48'].value_counts(dropna=False)

"""
matched2[matched2['FILE_REFERENCE'] == 'MHU_406084']
"""
matched2 = matched2[~matched2['AUTH_48'].isna()]

len(matched2) # 127

retain_order = ['FILE_REFERENCE', 'FAMILY_NAME', 'AUTH_48_DOHO','DATE_OF_HOSPITAL_ORDER','AUTH_48_DRIM','DATE_RECEIVED_IN_MHU',
                'ACTUAL_DATE','AUTHORISATION_DATE','APPLICATION_RECEIVED_IN_MHU',
                'AUTH_48','AUTHORITY_FOR_DETENTION_DESCRIPTION','AUTH_48_OFFENCE','OFFENCE_DESCRIPTION',
                'OFFENCE_GROUP_DESCRIPTION']

matched2 = matched2[retain_order + [col for col in matched2.columns if col not in retain_order]]

matched2

matched2.to_excel("adminWith48s.xlsx")
