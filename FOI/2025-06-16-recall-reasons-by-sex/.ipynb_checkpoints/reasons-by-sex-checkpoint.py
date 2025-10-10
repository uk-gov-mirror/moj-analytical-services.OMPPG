""" 
Please provide your OMSQ fitted by those convicted of sexual offences. The detials I require are similar to those found the following documents published on gov.uk.
- Prison releases 2024 [Table_3_A_1]
All ages and sexes,filtered by sex offenders only.
- Prison recalls 2024 [Table_5_A_10]
All ages and sexes,filtered by sex offenders only.

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

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
import prepareMatch
#importlib.reload(prepareMatch)
import openMatch
# importlib.reload(openMatch)
import TimeDiffs
import tariff_groups

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
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #
        
#---------------------------------- globals are already set


years = list(range(2022,2025))
quarters =[f"q{i}" for i in range(1,5)]

#---------------------------------- Import data

# some of the files are SAS and others are Parquet, so try to import each

def conCatReasonDatasets(years,quarters):
    
    reasons = pd.DataFrame() # start with an empty dataframe

    for year in years:
        
        for quarter in quarters:

            quart_reas = pd.DataFrame() # Reset appending file

            try: # Try to import SAS file first
                quart_reas = pd.read_sas(f"s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_{year}{quarter}.sas7bdat", encoding='latin1')
                quart_reas.columns = quart_reas.columns.str.upper()
                quart_reas = quart_reas.drop(columns =['DOS','RTC_DATE','DOB','REPORT_RECD_BY_UNIT_TARGET','PB_DECISION_AFTER_BREACH_ACTUAL'])
                                             
                print(f"Loaded SAS file for {year}{quarter}")

            except Exception as e:# If no SAS file, import parquet version

                print(f"Failed to load SAS file for {year}{quarter}, error: {e}")

                try:
                    quart_reas = pd.read_parquet(f"s3://alpha-omppg/Recalls/final_data/recall_reasons/recall_reasons_{year}{quarter}.parquet")
                    quart_reas.columns = quart_reas.columns.str.upper()
                    quart_reas = quart_reas.drop(columns =['DOS','RTC_DATE','DOB','REPORT_RECD_BY_UNIT_TARGET','PB_DECISION_AFTER_BREACH_ACTUAL'])
                    print(f"Loaded Parquet file for {year}{quarter}")

                except Exception as e:
                    print(f"Failed to load parquet file for {year}{quarter}, error: {e}")

            reasons = pd.concat([reasons,quart_reas],axis=0)

    return reasons

reasons_0 = conCatReasonDatasets(years,quarters)
reasons = reasons_0.copy()

strip_blanks(reasons)

"""
len(reasons) # 170548
reasons['LICENCE_REVOKE_DATE'].dt.year.value_counts(dropna=False).sort_index()
"""

# placeholder for summaries
reasons['COMMON'] = 1

# Add a recall 'YEAR' column in the form 'Month to Month year'-------------------------------------------

reasons['YEAR'] = reasons['LICENCE_REVOKE_DATE'].dt.year

"""
reasons.head()
reasons.tail()

"""
# Sentnces
"""
reasons.pivot_table(index=['SENTENCETYPE','CUSTODYTYPE'],columns='COMMON',aggfunc='size',fill_value=0)
"""

reasons.loc[reasons['CUSTODYTYPE'] == 'IPP','SENTENCETYPE'] = 'IPP'
reasons.loc[reasons['CUSTODYTYPE'] == 'Life','SENTENCETYPE'] = 'Life sentence'
reasons.loc[reasons['SENTENCETYPE'] == 'Other','SENTENCETYPE'] = 'Determinate 12 months or more'
reasons.loc[reasons['SENTENCETYPE'] == 'Under 12 months','SENTENCETYPE'] = 'Determinate less than 12 months'

reasons['SENTENCE'] = reasons['SENTENCETYPE']
reasons['SENTENCE'].unique()

# Change gender values----------------------------------

reasons['GENDER'].unique()
reasons['GENDER'] = reasons['GENDER'].replace({'F': 'Female', 'M': 'Male'}) # change 'F' to 'Female', 'M' to 'Male'

# reason descriptions for some legacy recall reasons

reasons[reasons['LICENCE_REVOKE_DATE'] > pd.Timestamp(2018,6,30)]['REASON_DESC'].value_counts(dropna=False)

legacyRecallReason_format = {
    'b. Poor Behaviour - non-compliance[*]': 'Non-compliance',
    'a. Further Charge[*]': 'Facing further charge',
    'c. Failed to keep in touch[*]': 'Failed to keep in touch',
    'd. Failed to reside[*]': 'Failed to reside',
    'e. Poor Behaviour - Drugs/alcohol[*]': 'Drugs/alcohol',
    'a. HDC - Time violation': 'HDC - Time violation',
    'f. Poor Behaviour - Relationships': 'Poor Behaviour - Relationships',
    'b. HDC - Inability to monitor': 'HDC - Inability to monitor',
    'c. HDC - Failed installation': 'HDC - Failed installation',
    'd. HDC - Equipment Tamper': 'HDC - Equipment Tamper',
    'f. Other[*]': 'Other',
    'g. Other[*]': 'Other',
    'g. Unknown[*]':'Unknown',
    'h. Unknown[*]':'Unknown',
    'Unknown': 'Unknown'
}

reasons['REASON_DESC_2'] = reasons['REASON_DESC'].replace(legacyRecallReason_format)

"""
reasons['REASON_DESC_2'].value_counts(dropna=False)

reasons[reasons['REASON_DESC_2'] == 'Other']['RECALL_REASON_DESCRIPTIONS'].value_counts(dropna=False)

reasons[reasons['REASON_DESC_2'] == 'Unknown']['RECALL_REASON_DESCRIPTIONS'].value_counts(dropna=False) # NaNs
"""

# Calculate summaries for table 2 - function table_2_func() is in Shared.py

reasons['REASON_DESC'] = reasons['REASON_DESC_2'].copy()

reasons['REASON_DESC'].value_counts()

# Birng publication lookup data
OffenceRef2 = pd.read_excel('s3://alpha-omppg/Recalls/Reference Data/Recalls Lookup.xls',sheet_name='Offences_OMSQ')
OffenceRef = pd.read_excel('s3://alpha-omppg/Recalls/Reference Data/Recalls Lookup.xls',sheet_name='Offences')

OffenceRef2.columns = OffenceRef2.columns.str.upper()
OffenceRef.columns = OffenceRef.columns.str.upper()

sum(reasons['FILE_REFERENCE'].isna()) # none missing

reasons = reasons.sort_values(by=['FILE_REFERENCE','LICENCE_REVOKE_DATE'])
len(reasons)

reasons['ID'] = list(range(1,len(reasons)+1)) # for deduplication

# remove all C0 control chars (except newline/tab if you like)
reasons['INDEX_OFFENCE_DESCRIPTION'] = reasons['INDEX_OFFENCE_DESCRIPTION'].str.replace('\x18', '').str.replace('\x19', '')

# join
query = """SELECT a.*, 
                b.OFFENCEGRP, 
                b.OFFENCESUBGROUP, 
                c.OFFENCEGRP_NEW,
                c.OFFENCESUBGROUP_NEW
            FROM reasons AS a 
                LEFT JOIN OffenceRef AS b
                ON (a.INDEX_OFFENCE_DESCRIPTION = b.INDEX_OFFENCE_DESCRIPTION)
                LEFT JOIN OffenceRef2 AS c
                ON TRIM(UPPER(a.INDEX_OFFENCE_DESCRIPTION)) = TRIM(UPPER(c.INDEX_OFFENCE_DESCRIPTION))"""

# Correct any possible offending timestanmp columns before final match
    
schema_df = duckdb.sql(f"""
                    DESCRIBE SELECT * FROM ({query})
        """).df()

tStampDate = schema_df[schema_df['column_type'].str.contains('TIME')][['column_name','column_type']]
    
info_df = pd.DataFrame({
    'dtype':  reasons.dtypes.astype(str),
})

info_df = info_df.reset_index().rename(columns={'index':'column_name'})
    
pd.merge(tStampDate, info_df, on='column_name')

# RETURN_BY column has mismatched dtype in both datasets - drop it as it's not needed
reasons = reasons.drop(columns='RETURN_BY')

# Proceed with matching
matched = duckdb.sql(query).df()
matched.shape #225940
matched.head()
"""
matched = matched.sort_values('ID')
sum(matched.duplicated(['ID'],keep=False)) # 110784
matched[matched.duplicated(['ID'],keep=False)].head(10)
"""

sum(matched['OFFENCEGRP_NEW'].isna()) # 0 missing offences

matched2 = matched.drop_duplicates(subset='ID', keep ='first')
matched2.shape # 170548
    
"""
matched[matched['OFFENCEGRP_NEW'].isna()][['INDEX_OFFENCE_DESCRIPTION']].drop_duplicates()
"""

# standardise some offence groups
matched2['OFFENCEGRP_NEW'].unique()

matched2.loc[matched2['OFFENCEGRP_NEW']=='Violence Against The Person','OFFENCEGRP_NEW'] = 'Violence against the person'
matched2.loc[matched2['OFFENCEGRP_NEW']=='Sexual Offences','OFFENCEGRP_NEW'] = 'Sexual offences'
matched2.loc[matched2['OFFENCEGRP_NEW']=='Drug Offences','OFFENCEGRP_NEW'] = 'Drug offences'
matched2.loc[matched2['OFFENCEGRP_NEW']=='Fraud offences','OFFENCEGRP_NEW'] = 'Fraud'
matched2.loc[matched2['OFFENCEGRP_NEW']=='Summary Motoring','OFFENCEGRP_NEW'] = 'Summary motoring'
matched2.loc[matched2['OFFENCEGRP_NEW']=='Public Order Offences','OFFENCEGRP_NEW'] = 'Public order offences'
matched2.loc[matched2['OFFENCEGRP_NEW']=='Criminal Damage and Arson','OFFENCEGRP_NEW'] = 'Criminal damage and arson'
matched2.loc[matched2['OFFENCEGRP_NEW']=='Miscellaneous Crimes Against Society','OFFENCEGRP_NEW'] = 'Miscellaneous crimes against society'
matched2.loc[matched2['OFFENCEGRP_NEW'].isna(),'OFFENCEGRP_NEW'] = 'Offence not recorded'

# Correct offence subgroups
matched2['OFFENCESUBGROUP_NEW'].unique()

matched2['OFFENCESUBGROUP_NEW'] = matched2['OFFENCESUBGROUP_NEW'].str.strip()

matched2.loc[matched2['OFFENCESUBGROUP_NEW'].isna(),'OFFENCESUBGROUP_NEW'] = 'Missing'
matched2.loc[matched2['OFFENCESUBGROUP_NEW']=='Stalking and Harassment','OFFENCESUBGROUP_NEW'] = 'Stalking and harassment'
matched2.loc[matched2['OFFENCESUBGROUP_NEW']=='Gross indecency with children','OFFENCESUBGROUP_NEW'] = 'Other sexual offences'

# keep those with sexual offences
sexualOffs = matched2[matched2['OFFENCEGRP_NEW'] == 'Sexual offences']
sexualOffs['OFFENCEGRP_NEW'].value_counts(dropna=False)

# Summarise
matched2['REASON_DESC'].value_counts(dropna=False)

sexualOffs['YEAR'] = sexualOffs['LICENCE_REVOKE_DATE'].dt.year

sexualOffs.pivot_table(index='REASON_DESC',columns='YEAR',aggfunc='size')
