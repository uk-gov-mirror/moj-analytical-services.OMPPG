""" 
GOAL: PRODUCE UAL DATA FOR OMSQ.
By Eric Nyame, 15/04/2024
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


        # Period variables
quarter = 4 # 1:Jan-Mar, 2:Apr-Jun, 3:Jul-Sep, 4:Oct-Dec
year = 2023 # Enter the year being run in 4 digit format

ual = pd.read_excel(f's3://alpha-omppg/UAL/PPUD/PPUD_UAL_{year}Q{quarter}.xlsx')

ual = ual.replace("–","-",regex=True) # replace long dashes with normal dashes
ual.shape # 2416

ual =ual[~ual['LICENCE_REVOKE_DATE'].isna()]
ual.shape

    # Convert columns that should be datetime to datetime
ual.info()

#---------------------------------- Remove Test cases
    # Check 'test' cases and remove
ual[ual['FAMILY_NAME'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

ual[ual['FIRST_NAMES'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

Test_Case_Mask =  (   (ual['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (ual['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (ual['FILE_REFERENCE'] != 'T18122')

# ual[Test_Case_Mask][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 3 cases

ual = ual[~Test_Case_Mask]
ual.shape # 7153

#---------------------------------- Drop duplicates
ual.shape
ual = ual.drop_duplicates()

CustodyRef = pd.read_excel('s3://alpha-omppg/Recalls/Reference Data/Recalls Lookup.xls',sheet_name='CustodyType')
AreaRef = pd.read_excel('s3://alpha-omppg/Recalls/Reference Data/Recalls Lookup.xls',sheet_name='PS')
RecallRef = pd.read_excel('s3://alpha-omppg/Recalls/Reference Data/Recalls Lookup.xls',sheet_name='RecallType')
OffenceRef2 = pd.read_excel('s3://alpha-omppg/Recalls/Reference Data/Recalls Lookup.xls',sheet_name='Offences_OMSQ')
OffenceRef = pd.read_excel('s3://alpha-omppg/Recalls/Reference Data/Recalls Lookup.xls',sheet_name='Offences')
PrisonerRef = pd.read_excel('s3://alpha-omppg/Recalls/Reference Data/Recalls Lookup.xls',sheet_name='Prisoners')

CustodyRef.columns = CustodyRef.columns.str.upper() 
AreaRef.columns = AreaRef.columns.str.upper()
RecallRef.columns = RecallRef.columns.str.upper()
OffenceRef2.columns = OffenceRef2.columns.str.upper()
OffenceRef.columns = OffenceRef.columns.str.upper()
PrisonerRef.columns = PrisonerRef.columns.str.upper()

CustodyRef = CustodyRef.replace("–","-",regex=True) # replace long dashes with normal dashes
AreaRef = AreaRef.replace("–","-",regex=True) # replace long dashes with normal dashes
RecallRef = RecallRef.replace("–","-",regex=True) # replace long dashes with normal dashes

strip_blanks(CustodyRef)
strip_blanks(AreaRef)
strip_blanks(RecallRef)

RecallRef['RECALL_TYPE_DESCRIPTION'].isna().sum() #0

# Create datasets of prisoners that will be corrected for manual checking*/

query = """ SELECT a.*, b.PROBATION_AREA_DESCRIPTION as PROBATION_AREA_DESCRIPTION_NEW
            FROM ual AS a JOIN PrisonerRef AS b ON a.PRISON_NUMBER = b.PRISON_NUMBER"""

check_prisoner_UAL = duckdb.sql(query).df()
check_prisoner_UAL.shape # 0


# Compute additional UAL variables*/

    # Filter out rows based on PROBATION_AREA_DESCRIPTION
ual = ual[~ual['PROBATION_AREA_DESCRIPTION'].isin(['Scotland', 'Northern Ireland'])]
ual.shape

    # Replace custody type if it's 'Not Applicable'
ual.loc[ual['CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION'] == 'Not Applicable', 'CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION'] = ual['CUSTODY_TYPE_DESCRIPTION']

    # Update gender based on specific condition
ual.loc[ual['GENDER'] == 'F ( Was M )', 'GENDER'] = 'F'
ual.loc[ual['GENDER'] == 'M ( Was F )', 'GENDER'] = 'M'


# Create a new reference by concatenating strings, assuming 'dob' is formatted correctly for concatenation
ual['NEWREF'] = ual['FAMILY_NAME'].str.replace(" ", "", regex=True) + \
                ual['PRISON_NUMBER'].str.replace(" ", "", regex=True) + \
                ual['DOB'].astype(str)

    # Define year and quarter variables

from pandas.tseries.offsets import QuarterEnd

def calculate_dates(year, quarter):
    current_quarter_start = pd.Timestamp(year, quarter * 3 - 2, 1)
    if quarter == 4:
        next_quarter_start = pd.Timestamp(year + 1, 1, 1)
        recall_cutoff = pd.Timestamp(year + 1, 4, 1) - QuarterEnd(1)
    elif quarter == 3:
        next_quarter_start = pd.Timestamp(year, 10, 1)
        recall_cutoff = pd.Timestamp(year + 1, 1, 1) - QuarterEnd(1)
    else:
        next_quarter_start = pd.Timestamp(year, quarter * 3 + 1, 1)
        recall_cutoff = pd.Timestamp(year, (quarter + 2) * 3 + 1) - QuarterEnd(1)
    return current_quarter_start, next_quarter_start, recall_cutoff

ual['STARTQTR'], ual['STARTNEXTQTR'], ual['RECALLCUTOFF'] = calculate_dates(year, quarter)
ual.head()

# Calculate date differences and classify the duration
ual['DATEDIF'] = ual.apply(lambda x: TimeDiffs.month_diff(x['LICENCE_REVOKE_DATE'],x['RECALLCUTOFF']),axis=1)
ual['DATEDIF'].isna().sum()
(ual['DATEDIF'] < 0).sum()

# Map DATEDIF to categories
bins = [-np.inf, 6, 12, 24, 60, 120, np.inf]
labels = ['a Up to and including 6 months', 'b More than 6 months - 1 year', 'c More than 1 year - 2 years',
          'd More than 2 years - 5 years', 'e More than 5 years - 10 years', 'f More than 10 years']

ual['HOWLONG'] = pd.cut(ual['DATEDIF'], bins=bins, labels=labels, right=False)
ual.tail()

# Set SUP_BODY based on the substring checks and date conditions

prob_trust_date = pd.Timestamp('2014-06-01')

conditions = [
    (ual['PROBATION_AREA_DESCRIPTION'].str[:3] == 'NPS') & (ual['LICENCE_REVOKE_DATE'] >= prob_trust_date),
    (ual['PROBATION_AREA_DESCRIPTION'].str[:2] == 'PS') & (ual['LICENCE_REVOKE_DATE'] >= prob_trust_date),
     (ual['PROBATION_AREA_DESCRIPTION'].str[:3] == 'NSD') & (ual['LICENCE_REVOKE_DATE'] >= prob_trust_date),
    (ual['PROBATION_AREA_DESCRIPTION'].str[:3] == 'CRC') & (ual['LICENCE_REVOKE_DATE'] >= prob_trust_date)
]

choices = ['b. NPS','b. PS', 'b. NPS', 'c. CRC']

default = 'a. Probation Trust'
ual['SUP_BODY'] = np.select(conditions, choices, default=default)

ual.loc[ual['PROBATION_AREA_DESCRIPTION'].str.contains('NPS', case=False) & (ual['LICENCE_REVOKE_DATE'] >= prob_trust_date), 'SUP_BODY'] = 'b. NPS'
ual.loc[ual['PROBATION_AREA_DESCRIPTION'].str.contains('CRC', case=False) & (ual['LICENCE_REVOKE_DATE'] >= prob_trust_date), 'SUP_BODY'] = 'c. CRC'

# Create dataset with Probation Trust cases after they stopped existing*/

ual[(ual['HOWLONG'] =='a Up to and including 6 months') & (ual['SUP_BODY']=='a. Probation Trust')] #0

# duplicates
ual[ual.duplicated(['PRISON_NUMBER'],keep=False)] #0

# Create a new dataset of unmatched codes from UAL dataset*/

query = """SELECT a.PRISON_NUMBER, a.INDEX_OFFENCE_DESCRIPTION, b.OFFENCEGRP, b.OFFENCESUBGROUP, 
                a.CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION, c.CUSTODYTYPE, C.CUSTODYTYPE2,
                a.PROBATION_AREA_DESCRIPTION, d.PROB_AREA,
                a.RECALL_TYPE_DESCRIPTION, e.TARGETTYPE, e.SENTENCETYPE,f.OFFENCEGRP_NEW,f.OFFENCESUBGROUP_NEW
                
            FROM ual AS A LEFT JOIN OffenceRef AS b
                ON (a.INDEX_OFFENCE_DESCRIPTION = b.INDEX_OFFENCE_DESCRIPTION)
                LEFT JOIN CustodyRef AS c
                ON (a.CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION = c.CUSTODY_TYPE_AT_RECALL)
                LEFT JOIN AreaRef AS d
                ON (a.PROBATION_AREA_DESCRIPTION = d.PROBATION_AREA_DESCRIPTION)
                LEFT JOIN RecallRef AS e
                ON (a.RECALL_TYPE_DESCRIPTION = e.RECALL_TYPE_DESCRIPTION)
                LEFT JOIN OffenceRef2 AS f
                ON a.INDEX_OFFENCE_DESCRIPTION = f.INDEX_OFFENCE_DESCRIPTION
            WHERE 
                   f.OFFENCEGRP_NEW IS NULL
                OR c.CUSTODYTYPE IS NULL
                OR c.CUSTODYTYPE2 IS NULL
                OR d.PROB_AREA IS NULL
                OR e.TARGETTYPE IS NULL
                OR e.SENTENCETYPE IS NULL
                 """
ual_unmatched_codes = duckdb.sql(query).df()
ual_unmatched_codes.shape

# ADD INFORMATION FROM REFERENCE LISTS TO UAL DATASET*/
query = """SELECT a.*, 
                b.OFFENCEGRP, 
                b.OFFENCESUBGROUP, 
                c.CUSTODYTYPE, 
                c.CUSTODYTYPE2, 
                d.PROB_AREA, 
                e.TARGETTYPE, 
                e.SENTENCETYPE,
                f.OFFENCEGRP_NEW,
                f.OFFENCESUBGROUP_NEW
            FROM ual AS a 
                LEFT JOIN OffenceRef AS b
                ON (a.INDEX_OFFENCE_DESCRIPTION = b.INDEX_OFFENCE_DESCRIPTION)
                LEFT JOIN CustodyRef AS c
                ON (a.CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION = c.CUSTODY_TYPE_AT_RECALL)
                LEFT JOIN AreaRef AS d
                ON (a.PROBATION_AREA_DESCRIPTION = d.PROBATION_AREA_DESCRIPTION)
                LEFT JOIN RecallRef AS e
                ON (a.RECALL_TYPE_DESCRIPTION = e.RECALL_TYPE_DESCRIPTION)
                LEFT JOIN OffenceRef2 AS f
                ON TRIM(UPPER(a.INDEX_OFFENCE_DESCRIPTION)) = TRIM(UPPER(f.INDEX_OFFENCE_DESCRIPTION));
"""
ual_matched = duckdb.sql(query).df()
ual_matched.shape

ual_matched = ual_matched.drop_duplicates(subset='PRISON_NUMBER', keep ='first')

# Save on Amazon to continue

ual_matched.to_parquet(f"s3://alpha-omppg/UAL/Final Data/Parquet/ual_final_{year}q{quarter}.parquet",index=False)
