# QUESTION -
 """ How many DPPs are in hospital?"""

# Models and settings
import pandas as pd
import numpy as np
import duckdb

pd.options.display.max_columns = None
pd.options.display.max_rows = None

# Import MH SAS population data
poPDec22 = pd.read_sas("s3://alpha-omppg/Mental Health/2022/Sas Data/population__prepared.sas7bdat", encoding='latin1')

poPDec22.columns = [i.upper() for i in poPDec22.columns]
poPDec22.dtypes

# Import ISP population data
ispPPUD = pd.read_excel("s3://alpha-omppg/ISP Population/PPUD/2023Q2/PPUD_ISP_2023Q2.xls")
ispPPUD.dtypes

# Check milestone distribution
poPDec22["DA_CUSTODY_TYPE_DESCRIPTION"].value_counts(dropna = False)
poPDec22Nodups = poPDec22.drop_duplicates(["FILE_REFERENCE","FAMILY_NAME","AUTHORITY_FOR_DETENTION_DESCRIPT"])
poPDec22Nodups["DA_CUSTODY_TYPE_DESCRIPTION"].value_counts(dropna = False)

# check DPP cases per isp pop data
ispPPUDNodups = ispPPUD.drop_duplicates(["FILE_REFERENCE","FAMILY_NAME","CUSTODY_TYPE_DESCRIPTION"])

# Match the two datasets
query =  """SELECT a.*, 
                   b.CUSTODY_TYPE_DESCRIPTION
            FROM poPDec22Nodups AS a LEFT JOIN ispPPUDNodups AS b 
            ON  (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) OR
                (a.NOMS_ID = b.NOMS_ID AND a.NOMS_ID IS NOT NULL)"""

augmentedRPPop = duckdb.sql(query).df()
len(poPDec22Nodups)
len(ispPPUDNodups)
len(augmentedRPPop)
len(augmentedRPPop) - len(poPDec22Nodups)

#check duplicates
retain =["FILE_REFERENCE","FAMILY_NAME","AUTHORITY_FOR_DETENTION_DESCRIPT","CUSTODY_TYPE_DESCRIPTION"]
checkDups = augmentedRPPop.duplicated(["FILE_REFERENCE"],keep = False)
augmentedRPPop[checkDups].sort_values(by=["FILE_REFERENCE"])[retain + [i for i in augmentedRPPop if i not in retain]]

augmentedRPPop.drop_duplicates(["FILE_REFERENCE","FAMILY_NAME","CUSTODY_TYPE_DESCRIPTION"],inplace = True)
checkDups = augmentedRPPop.duplicated(["FILE_REFERENCE"],keep = False)
augmentedRPPop[checkDups].sort_values(by=["FILE_REFERENCE"])[retain + [i for i in augmentedRPPop if i not in retain]]

# COUNT
augmentedRPPop.value_counts("CUSTODY_TYPE_DESCRIPTION")
