# Question

# Please could you provide the number of people serving an IPP sentence in prison who have, at any point during their IPP sentence, 
# resided in secure hospital, but are presently residing in prison.

# Libraries
import pandas as pd
import numpy as np
import duckdb
import s3fs
# import sys # for adding folders to the search path

pd.options.display.max_columns = None
pd.options.display.max_rows = None
# pd.options.display.precision = 2
# pd.set_option('max_colwidth',None)

# Root directory for Recalls data
# rootDir = "s3://alpha-omppg/FOI"

# Add macro folder to namespace to import custom modules and their functions
# sys.path.append('/home/jovyan/OMPPG/Macro Library')
# sys.path.append('/home/jovyan/OMPPG/Recalls/Reference Data/Recalls Lookup') # for recall lookups
#sys.path.append('/home/jovyan/.local/bin')

# Import Restricted Patients data
Restricted_P_Ever = pd.read_excel("s3://alpha-omppg/FOI/2023 06 06 IPPs Once Restricted Patients/Restricted patients ever as at 05June2023.xls")

Restricted_P_Ever.head()
Restricted_P_Ever.dtypes

# Check the years of hospital orders
Restricted_P_Ever["DATE_OF_HOSPITAL_ORDER"].dt.year.value_counts(dropna = False).sort_index()

# Date of hospital order should not be greater than prison snapshot date
Restricted_P_Ever = Restricted_P_Ever[~(Restricted_P_Ever["DATE_OF_HOSPITAL_ORDER"] > "2023-03-31")]
Restricted_P_Ever["DATE_OF_HOSPITAL_ORDER"].max()

# Check the custody types
Restricted_P_Ever["DA_CUSTODY_TYPE_DESCRIPTION"].value_counts(dropna = False)

# Bring in prison data
Mar23 = pd.read_sas("s3://alpha-omppg/ISP Population/Final Datasets/isp_pop_2023q2.sas7bdat", encoding='latin1')
Mar23.columns = [i.upper() for i in Mar23.columns] # uppercase the columns
Mar23.head()
Mar23.dtypes

# Keep only IPPs
Mar23_b  = Mar23[Mar23["ISP_STATUS"].str.contains("IPP",case = False, regex = False)].copy()
Mar23_b["ISP_STATUS"].value_counts(dropna=False)
len(Mar23_b)
#2916

# Retain some vars in the pop data
Mar23_b = Mar23_b[["NOMIS_ID","SURNAME","DOS","TARIFF_EXPIRY_DATE","DATEOFBIRTH","OFFENCE","PRISONNAME",
                  "AGE","ETHNICGROUP","EXTRACTDATE","FORENAME","GENDER","OFFENCEGROUP","PRISON_NUMBER",
                  "PROBATION_SERVICE_DESCRIPTION","TARIFF_PAST","ISP_STATUS"]]

# Merge with Restricted patients data
keep_from_right = ['NOMS_ID','DA_CUSTODY_TYPE_DESCRIPTION',
                   'AUTHORITY_FOR_DETENTION_DESCRIPTION','DATE_OF_HOSPITAL_ORDER']

Mar23_b = pd.merge(Mar23_b, Restricted_P_Ever[keep_from_right],
                   left_on='NOMIS_ID',right_on="NOMS_ID", how ='left')

# Could have inner joined to save next step
Mar23_b = Mar23_b[Mar23_b["NOMS_ID"].notnull()]

# Hospital order must be after date of sentence
Mar23_b = Mar23_b[Mar23_b["DATE_OF_HOSPITAL_ORDER"] >= Mar23_b["DOS"]]

# Rank to place more higher priority on IPP cases in restricted patients
# if there are multiple matches

IPP_Mask = Mar23_b["DA_CUSTODY_TYPE_DESCRIPTION"].isin(["IPP","DPP"])
IPP_Mask.value_counts()
Mar23_b["Rank"] = np.where(IPP_Mask,1,2)

# Deduplicate by descending hospital order and ascending Rank
Mar23_b.sort_values(by = ["DATE_OF_HOSPITAL_ORDER","Rank"],ascending=[False,True], inplace=True)
Mar23_b.head()
Mar23_b.drop_duplicates("NOMS_ID", inplace=True)
len(Mar23_b)
#219

# Save to Amazon
Mar23_b.to_excel("s3://alpha-omppg/FOI/2023 06 06 IPPs Once Restricted Patients/IPPs_Prisoners_Once_RPs.xlsx")
