""" 
GOAL: IDENTIFY DPP CASES IN THE PROBATION CASELOAD DATA PROBATION STATISTICS TEAM.
By Eric Nyame, 18/04/2024
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
# import prepareMatch
# importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
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

# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x) #


        # PPUD extract details
quarter = 1 # 1:Jan-Mar, 2:Apr-Jun, 3:Jul-Sep, 4:Oct-Dec
year = 2024 # Enter the year being run in 4 digit format

# import data
in_community = pd.read_excel(f's3://alpha-omppg/Ad hoc/2024 DPPs in community verification/IPPs_in_community_30Jun23.xlsx')
ispPPUD = pd.read_excel(f's3://alpha-omppg/ISP Population/PPUD/{year}Q{quarter}/PPUD_ISP_{year}Q{quarter}.xls')

# remove long dashes
in_community = in_community.replace("–","-",regex=True) # replace long dashes with normal dashes
ispPPUD = ispPPUD.replace("–","-",regex=True) # replace long dashes with normal dashes

# check lengths
in_community.shape,ispPPUD.shape #((3098, 21), (24913, 32))

# remove long blanks
strip_blanks(in_community)
strip_blanks(ispPPUD)

# rearrange columns
retain_community = ['NOMS_No','Surname', 'Forename1','Birthdt']
retain_ppud = ['NOMS_ID','FAMILY_NAME', 'FIRST_NAMES','DOB']

in_community = in_community[retain_community + [col for col in in_community.columns if col not in retain_community]]
ispPPUD = ispPPUD[retain_ppud + [col for col in ispPPUD.columns if col not in retain_ppud]]

# view them
in_community.head()
ispPPUD.head()

# Upprcase column names
ispPPUD['FAMILY_NAME'] = ispPPUD['FAMILY_NAME'].str.upper()
ispPPUD['FIRST_NAMES'] = ispPPUD['FIRST_NAMES'].str.upper()

in_community.columns = in_community.columns.str.upper()

# keep IPPs only for matching
ispPPUD['CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)
ipp = ispPPUD[ispPPUD['CUSTODY_TYPE_DESCRIPTION'].isin(['DPP','IPP'])].copy()

# Match

query = """SELECT a.*, 
                b.FAMILY_NAME,
                b.FIRST_NAMES,
                b.FILE_REFERENCE AS FILE_REFERENCE_TERM,
                b.NOMS_ID,
                b.DOB AS PPPUD_DOB,
                b.DOS,
                b.CUSTODY_TYPE_DESCRIPTION,
                b.LATEST_RELEASE_DATE AS PPUD_LATEST_RELEASE_DATE
                
                FROM in_community AS a LEFT JOIN ipp AS b
                ON (a.NOMS_NO = b.NOMS_ID AND a.NOMS_NO IS NOT NULL) OR
                (
                    a.SURNAME = b.FAMILY_NAME AND
                    a.BIRTHDT = b.DOB AND a.BIRTHDT IS NOT NULL AND
                    (
                        (a.FORENAME1 LIKE '%' || b.FIRST_NAMES || '%') OR (b.FIRST_NAMES LIKE '%' || a.FORENAME1 || '%')
                    )
                )"""

enhanced_community = duckdb.sql(query).df()
enhanced_community.shape # 3115, originally 3098

# rearrange
retain_enhanced_community = ['NOMS_NO','NOMS_ID','SURNAME', 'FAMILY_NAME','FORENAME1','FIRST_NAMES','BIRTHDT','PPPUD_DOB','CUSTODY_TYPE_DESCRIPTION','COMMENDT','DOS']
enhanced_community = enhanced_community[retain_enhanced_community + [col for col in enhanced_community.columns if col not in retain_enhanced_community]]

enhanced_community.head()

# Deduplicate 
in_community.duplicated([]'CRN').sum() # 0

enhanced_community = enhanced_community.drop_duplicates(subset =['CRN','CUSTODY_TYPE_DESCRIPTION'])
enhanced_community.shape # 3100, orginally 3098, so 2 duplicates.

# sort data
enhanced_community = enhanced_community.sort_values('CRN')

# find duplicated cases where there is excess match
enhanced_community[enhanced_community.duplicated('CRN',keep=False)]

# check dodgy matches which are matches without NOMIS ID being equal
dodgy = (enhanced_community['NOMS_ID'] != enhanced_community['NOMS_NO']) & (enhanced_community['FAMILY_NAME'].notna())

dodgy.sum() # 139
enhanced_community[dodgy].head()

# Create match type
enhanced_community['MATCH_TYPE'] = 'No Match'
enhanced_community.loc[(enhanced_community['NOMS_ID'] == enhanced_community['NOMS_NO']),'MATCH_TYPE'] = 'NOMIS_ID'
enhanced_community.loc[dodgy,'MATCH_TYPE'] = 'Surname,forename,Dob'

enhanced_community['MATCH_TYPE'].value_counts(dropna=False)

# identify those with IPP and DPP sentences
enhanced_community.duplicated('CRN').sum()

enhanced_community['DUAL_SENTENCE'] = 'No'
enhanced_community.loc[enhanced_community.duplicated('CRN',keep=False),'DUAL_SENTENCE'] = 'Yes'
enhanced_community.loc[enhanced_community['MATCH_TYPE'] == 'No Match','DUAL_SENTENCE'] = np.nan

# rearrange
retain_enhanced_community = ['NOMS_NO','NOMS_ID','SURNAME', 'FAMILY_NAME','FORENAME1','FIRST_NAMES','BIRTHDT','PPPUD_DOB','CUSTODY_TYPE_DESCRIPTION','COMMENDT','DOS','MATCH_TYPE','DUAL_SENTENCE']
enhanced_community = enhanced_community[retain_enhanced_community + [col for col in enhanced_community.columns if col not in retain_enhanced_community]]

# summary
enhanced_community['MATCH_TYPE'].value_counts(dropna=False)
enhanced_community['DUAL_SENTENCE'].value_counts(dropna=False)

# Save and send
enhanced_community.to_excel("PPUD_added.xlsx",index=False)