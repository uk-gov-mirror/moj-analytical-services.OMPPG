""" 
GOAL: PRODUCE RECALL TABLES FOR OMSQ.
By Eric Nyame, 17/04/2024
"""

import pandas as pd
import numpy as np
import sys
import duckdb
# print(duckdb.__version__)
# import importlib

from itables import show

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
import prepareMatch
# importlib.reload(prepareMatch)
import openMatch
#importlib.reload(openMatch)
import TimeDiffs
import tariff_groups
#importlib.reload(tariff_groups)

# Set display options

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.set_option('display.max_colwidth', None)

# Ensures no wrapping of cell contents - run it separately

# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x) #
        
%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Get last final recall data for the last 5 quarters----------------------------------------------------------------------
                      
rec1 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2024q1.parquet')
rec2 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2024q2.parquet')
rec3 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2024q3.parquet')
rec4 = pd.read_parquet('s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2024q4.parquet')

# uppercase the headers
for df in [rec1,rec2,rec3,rec4]:
    df.columns = df.columns.str.upper()

# Concatenate all DataFrames into one------------------------------------------------------------------

recalls = pd.concat([rec1,rec2,rec3,rec4], ignore_index=True)
len(recalls) # 37573
recalls.head()

del rec1,rec2,rec3,rec4

def sentence(df):
    
    conditions = [
        (df['CUSTODYTYPE'] == 'Determinate') & (df['SENTENCETYPE'].isna()),
        (df['CUSTODYTYPE'] == 'Determinate') & (df['SENTENCETYPE'] == 'Other'),
        (df['CUSTODYTYPE'] == 'Determinate') & (df['SENTENCETYPE'] == 'Under 12 months'),
        (df['CUSTODYTYPE'] == 'IPP') & (df['SENTENCETYPE'].isna()),
        (df['CUSTODYTYPE'] == 'IPP') & (df['SENTENCETYPE'] == 'Other'),
        (df['CUSTODYTYPE'] == 'IPP') & (df['SENTENCETYPE'] == 'Under 12 months'),
        (df['CUSTODYTYPE'] == 'Life') & (df['SENTENCETYPE'].isna()),
        (df['CUSTODYTYPE'] == 'Life') & (df['SENTENCETYPE'] == 'Other'),
        (df['CUSTODYTYPE'] == 'Life') & (df['SENTENCETYPE'] == 'Under 12 months')
    ]

    choices = [
        'Missing',
        'Determinate 12 months or more',
        'Determinate less than 12 months',
        'Missing',
        'IPP',
        'IPP',
        'Missing',
        'Life sentence',
        'Life sentence'
    ]
    
    df['SENTENCE'] = np.nan # set initially to nans
    df['SENTENCE'] = np.select(conditions, choices, default=df['SENTENCE'])

sentence(recalls)

recalls['SENTENCE'].unique()

ipp_recalls = recalls[recalls['SENTENCE'] == 'IPP']

ipp_recalls_FO = ipp_recalls[ipp_recalls['FURTHER_CHARGE'] == 100]


ipp_recalls['FURTHER_CHARGE'].value_counts(dropna=False)
ipp_recalls_FO['FURTHER_CHARGE'].value_counts(dropna=False)

# Index offences
isp1 = pd.read_sas("s3://alpha-omppg/isp-population/final/isp_pop_2023q4.sas7bdat",encoding='latin1')
isp2 = pd.read_parquet("s3://alpha-omppg/isp-population/final/isp_pop_2024q1.parquet")
isp3 = pd.read_parquet("s3://alpha-omppg/isp-population/final/isp_pop_2024q2.parquet")
isp4 = pd.read_parquet("s3://alpha-omppg/isp-population/final/isp_pop_2024q3.parquet")
isp5 = pd.read_parquet("s3://alpha-omppg/isp-population/final/isp_pop_2024q4.parquet")
isp6 = pd.read_parquet("s3://alpha-omppg/isp-population/final/isp_pop_2025q1.parquet")

isp1.columns = isp1.columns.str.upper()

isp1 = isp1[['NOMIS_ID', 'SURNAME', 'FORENAME', 'OFFENCEGROUP','EXTRACTDATE']]

isp = pd.concat([isp1,isp2,isp3,isp4,isp5,isp6],ignore_index=True)

del isp1,isp2,isp3,isp4,isp5,isp6

isp = isp[['NOMIS_ID', 'SURNAME', 'FORENAME', 'ISP_STATUS','OFFENCEGROUP','EXTRACTDATE']]

isp['EXTRACTDATE'].value_counts()

ipp = isp[isp['ISP_STATUS'].str.contains('IPP',case=False,na=False)]

ipp = ipp.sort_values(['NOMIS_ID','EXTRACTDATE'],ascending=[True,False])
ipp = ipp.drop_duplicates('NOMIS_ID')

len(ipp)


ipp_recalls_FO = prepareMatch.prepareMatch(ipp_recalls_FO)

#---------------------------------- Match to A&O Dataset on either NOMIS number, Prison Number or Name and DOB

query3 = """SELECT DISTINCT a.*, 
                            b.*
                            
                    FROM ipp_recalls_FO AS b LEFT JOIN ipp AS a
                    
                    ON 
                      (a.NOMIS_ID = b.NOMS_ID OR
                       a.NOMIS_ID = b.NOMS_TRIM OR
                       a.NOMIS_ID = b.NOMS_START OR
                       a.NOMIS_ID = b.NOMS_END OR
                       a.NOMIS_ID = b.PRISON_NUMBER OR
                       a.NOMIS_ID = b.PN_TRIM OR
                       a.NOMIS_ID = b.PN_START OR
                       a.NOMIS_ID = b.PN_END)"""

matched = duckdb.sql(query3).df()
matched.shape # 170 as expected

matched.pivot_table(index='OFFENCEGROUP',columns='ISP_STATUS',aggfunc='size',dropna=False,fill_value=0).reset_index()

matched[matched['OFFENCEGROUP'].isna()]

matched[matched['OFFENCEGROUP'].isna()].pivot_table(index=['NOMS_ID','FAMILY_NAME','INDEX_OFFENCE_DESCRIPTION'],aggfunc='size',fill_value=0).reset_index()

matched[matched['OFFENCEGROUP'].isna()]
ipp['OFFENCEGROUP'].value_counts()


ipp.pivot_table(index='OFFENCEGROUP',columns='ISP_STATUS',aggfunc='size',fill_value=0).reset_index()



ipp_recalls['INDEX_OFFENCE_DESCRIPTION'].value_counts(dropna=False)
