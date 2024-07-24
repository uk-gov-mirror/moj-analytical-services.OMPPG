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

Offences_up_to_2018 = pd.read_excel("s3://alpha-omppg/Mental Health/2023/Raw Data/Offence_up_to_2018.xls")
Offences_2019_to_2023 = pd.read_excel("s3://alpha-omppg/Mental Health/2023/Raw Data/Offence_2019_to_2023.xls")

offences = pd.concat([Offences_up_to_2018,Offences_2019_to_2023],ignore_index=True)

offences = offences.replace("–","-",regex=True)

offences.info()

# We will deduplicate the offences after the match 

    # offences = offences.sort_values(by=['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER'])

    # offences[offences.duplicated(['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER','OFFENCE_DESCRIPTION'],keep=False)] # don't worry about these yet

to_delete = (offences['OFFENCE_DESCRIPTION'].isna()) | (offences['OFFENCE_DESCRIPTION'].isin([pd,'Not Specified','Not Applicable']))
to_delete.sum() # 198

offences = offences[~to_delete].copy()

offences['FILE_REFERENCE'] = offences['FILE_REFERENCE'].astype(str)
offences['PRISON_NUMBER'] = offences['PRISON_NUMBER'].astype(str)


query = """SELECT a.*, 
                  b.OFFENCE_DESCRIPTION, 
                  b.OFFENCE_GROUP_DESCRIPTION,
                  b.COURT_OFFENCE_TEXT
                  
            FROM pop AS a LEFT JOIN offences AS b
            
            ON  (
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) OR
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)
                ) AND
                (a.DATE_OF_HOSPITAL_ORDER = b.DATE_OF_HOSPITAL_ORDER AND a.DATE_OF_HOSPITAL_ORDER IS NOT NULL) AND
                (a.AUTHORITY_FOR_DETENTION_DESCRIPTION = b.AUTHORITY_FOR_DETENTION_DESCRIPTION AND a.AUTHORITY_FOR_DETENTION_DESCRIPTION IS NOT NULL) """

pop_off = duckdb.sql(query).df()
len(pop_off) # 12808

    # keep non-missing
non_missing_offence_1 =  pop_off[~pop_off['OFFENCE_DESCRIPTION'].isna()]

    # Resolve missing offence cases
missing_offence_1 = pop_off[pop_off['OFFENCE_DESCRIPTION'].isna()]
len(missing_offence_1) # 23

missing_offence_1

missing_offence_1[missing_offence_1['FILE_REFERENCE']=='127010'][['FILE_REFERENCE','PRISON_NUMBER','DATE_OF_HOSPITAL_ORDER','AUTHORITY_FOR_DETENTION_DESCRIPTION']]
offences[offences['FILE_REFERENCE']=='127010'][['FILE_REFERENCE','PRISON_NUMBER','DATE_OF_HOSPITAL_ORDER','AUTHORITY_FOR_DETENTION_DESCRIPTION','OFFENCE_DESCRIPTION']]

    # relax authority for detention

missing_offence_1 = missing_offence_1.drop(['OFFENCE_DESCRIPTION',  'OFFENCE_GROUP_DESCRIPTION','COURT_OFFENCE_TEXT'], axis=1)

query2 = """SELECT a.*, 
                  b.OFFENCE_DESCRIPTION, 
                  b.OFFENCE_GROUP_DESCRIPTION,
                  b.COURT_OFFENCE_TEXT
                  
            FROM missing_offence_1 AS a LEFT JOIN offences AS b
            
            ON  (
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) OR
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)
                ) AND
                (a.DATE_OF_HOSPITAL_ORDER = b.DATE_OF_HOSPITAL_ORDER AND a.DATE_OF_HOSPITAL_ORDER IS NOT NULL) """

pop_off2 = duckdb.sql(query2).df()
len(pop_off2) # 30

# keep non-missing
non_missing_offence_2 = pop_off2[~pop_off2['OFFENCE_DESCRIPTION'].isna()]

    # Resolve missing offence cases
missing_offence_2 = pop_off2[pop_off2['OFFENCE_DESCRIPTION'].isna()]
len(missing_offence_2) # 9

missing_offence_2

missing_offence_2[missing_offence_2['FILE_REFERENCE']=='2/16792'][['FILE_REFERENCE','PRISON_NUMBER','DATE_OF_HOSPITAL_ORDER','DATE_RECEIVED_IN_MHU','AUTHORITY_FOR_DETENTION_DESCRIPTION']]
offences[offences['FILE_REFERENCE']=='2/16792'][['FILE_REFERENCE','PRISON_NUMBER','DATE_OF_HOSPITAL_ORDER','DATE_RECEIVED_IN_MHU','AUTHORITY_FOR_DETENTION_DESCRIPTION','OFFENCE_DESCRIPTION','COURT_OFFENCE_TEXT']]

    # relax date of hospital order

missing_offence_2 = missing_offence_2.drop(['OFFENCE_DESCRIPTION',  'OFFENCE_GROUP_DESCRIPTION','COURT_OFFENCE_TEXT'], axis=1)
    
query3 = """SELECT a.*, 
                  b.OFFENCE_DESCRIPTION, 
                  b.OFFENCE_GROUP_DESCRIPTION,
                  b.COURT_OFFENCE_TEXT
                  
            FROM missing_offence_2 AS a LEFT JOIN offences AS b
            
            ON  (
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) OR
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)
                ) """

pop_off3 = duckdb.sql(query3).df()
len(pop_off3) # 29

# keep non-missing
non_missing_offence_3 = pop_off3[~pop_off3['OFFENCE_DESCRIPTION'].isna()]

    # Resolve missing offence cases
missing_offence_3 = pop_off3[pop_off3['OFFENCE_DESCRIPTION'].isna()]
len(missing_offence_3) # 0


# ----------------- Put together sorted missing offences

resolved_missing_offence = pd.concat([non_missing_offence_1,non_missing_offence_2,non_missing_offence_3],ignore_index=True)
    
retain_order = ['FILE_REFERENCE', 'FAMILY_NAME', 'DATE_OF_HOSPITAL_ORDER','AUTHORITY_FOR_DETENTION_DESCRIPTION','OFFENCE_DESCRIPTION','OFFENCE_GROUP_DESCRIPTION','COURT_OFFENCE_TEXT']

resolved_missing_offence = resolved_missing_offence[retain_order + [col for col in resolved_missing_offence.columns if col not in retain_order]]

resolved_missing_offence['OFFENCE_DESCRIPTION'].isna().sum()
len(resolved_missing_offence) # 12835

    # Add reference for offence

ref_offences = pd.read_excel("s3://alpha-omppg/Mental Health/Reference/Reference.xls", sheet_name="Offences_use")
ref_offences = ref_offences.replace("–","-", regex = True)

ref_offences['INDEX_OFFENCE_DESCRIPTION'] = ref_offences['INDEX_OFFENCE_DESCRIPTION'].astype(str).str.upper().str.strip()

resolved_missing_offence['OFFENCE_DESCRIPTION'] = resolved_missing_offence['OFFENCE_DESCRIPTION'].astype(str).str.upper().str.strip()

query4 = """SELECT a.*, 
                  b.*
                  
            FROM resolved_missing_offence AS a LEFT JOIN ref_offences AS b
            
            ON  a.OFFENCE_DESCRIPTION = b.INDEX_OFFENCE_DESCRIPTION  AND a.OFFENCE_DESCRIPTION IS NOT NULL """

resolved_missing_offence = duckdb.sql(query4).df()
len(resolved_missing_offence) # 12835

resolved_missing_offence.head()

resolved_missing_offence[resolved_missing_offence['offencegrp_new'].isna()].head() # only 1

resolved_missing_offence[resolved_missing_offence['FILE_REFERENCE']=='2/16609']

resolved_missing_offence = resolved_missing_offence[~(resolved_missing_offence['OFFENCE_DESCRIPTION'] == 'SEC 40 CONVICTIONS DURING ORIGINAL SENTENCE')]

# -------- Deduplicate

    #----------------------------------  Unique offence per person

# resolved_missing_offence.groupby(['COURT_OFFENCE_TEXT','OFFENCE_DESCRIPTION','OFFENCE_GROUP_DESCRIPTION']).size().reset_index(name='count').to_excel("Offence_ref_PPUD.xlsx", index=False) 

resolved_missing_offence = resolved_missing_offence.sort_values(by=['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER','OFFENCE_DESCRIPTION'])

resolved_missing_offence[resolved_missing_offence.duplicated(subset =['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER','OFFENCE_DESCRIPTION'], keep=False)].head(10)

unique_offence_description = resolved_missing_offence.drop_duplicates(subset = ['FILE_REFERENCE','OFFENCE_DESCRIPTION'],ignore_index = True).copy()

len(unique_offence_description) # 12077

#----------------------------------  Unique offene group per person

resolved_missing_offence = resolved_missing_offence.sort_values(by=['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER','OFFENCE_GROUP_DESCRIPTION'])

resolved_missing_offence[resolved_missing_offence.duplicated(subset =['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER','OFFENCE_GROUP_DESCRIPTION'], keep=False)].head(10)

unique_offence_group = resolved_missing_offence.drop_duplicates(subset = ['FILE_REFERENCE','OFFENCE_GROUP_DESCRIPTION'],ignore_index = True).copy()

len(unique_offence_group) # 10785

#----------------------------------  MOST SERIOUS OFFENCE

resolved_missing_offence = resolved_missing_offence.sort_values(['FILE_REFERENCE', 'Rank', 'OFFID'])

most_ser = resolved_missing_offence.drop_duplicates(['FILE_REFERENCE'], keep = 'first').copy()

len(most_ser)

# ---------------------------Export prepared datasets

unique_offence_group.to_parquet(f"s3://alpha-omppg/Mental Health/2023/Parquet Data/offence_groups_prepared_{year}.parquet")

most_ser.to_parquet(f"s3://alpha-omppg/Mental Health/2023/Parquet Data/population_with_one_offence_prepared_{year}.parquet")

#--------------  breakdown all offences

    # Table 3
pd.crosstab([most_ser['GENDER'],most_ser['offencegrp_new']],most_ser['STATUS'], margins = True, margins_name = 'Total').to_excel("Tables/Table_3.xlsx")

pd.crosstab([unique_offence_group['GENDER'],unique_offence_group['offencegrp_new']],unique_offence_group['STATUS'], margins = True, margins_name = 'Total').to_excel("Tables/Table_3b.xlsx")