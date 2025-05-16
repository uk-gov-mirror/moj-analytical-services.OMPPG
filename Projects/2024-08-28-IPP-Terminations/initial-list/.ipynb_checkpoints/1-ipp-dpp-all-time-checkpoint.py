""" 
GOAL: ATTEMPT PRODUCE ALL IPPs/DPPs BY PPUD AS AT 16 AUGUST 2024

By Eric Nyame, 28/08/2024
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
# import openMatch
# importlib.reload(openMatch)
import TimeDiffs
# import tariff_groups

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

# IMPORT RELEASES AND RECALLS DATA

    # import sentence data
#all_ipp_dpp = pd.read_excel("raw-data/All-IPP-DPP-Cases 16-08-2024.xlsx")
#all_ipp_dpp.columns = all_ipp_dpp.columns.str.upper()

#all_ipp_dpp.info()
#all_ipp_dpp[retain].head()

#(all_ipp_dpp.duplicated(['FILE_REFERENCE','DOS'])).sum() # 0, good
#all_ipp_dpp['CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False) # DPP, IPP
#len(all_ipp_dpp) # 8114

#all_ipp_dpp['NOMS_ID'].isna().sum() # 232
#all_ipp_dpp['FILE_REFERENCE'].isna().sum() # 1
#all_ipp_dpp[all_ipp_dpp['FILE_REFERENCE'].isna()]
# all_ipp_dpp.loc[all_ipp_dpp['FILE_REFERENCE'].isna(),'FILE_REFERENCE'] = all_ipp_dpp['PRISON_NUMBER']

    # releases and recalls
releases = pd.read_excel("raw-data/ipp-dpp-releases-up-to-29-08-2024.xls")
strip_blanks(releases)
recalls = pd.read_excel("raw-data/ipp-dpp-recalls-up-to-29-08-2024.xls")
strip_blanks(recalls)

#len(releases) # 10754
#len(recalls) # 7181
#releases.info()
#recalls.head()

#releases['NOMS_ID'].isna().sum() # 93
#releases['FILE_REFERENCE'].isna().sum() # 1
# releases[releases['FILE_REFERENCE'].isna()]
# releases.loc[releases['FILE_REFERENCE'].isna(),'FILE_REFERENCE'] = releases['PRISON_NUMBER']
#releases['PRISON_NUMBER'].isna().sum() # 0

#recalls['NOMS_ID'].isna().sum() # 25
#recalls['FILE_REFERENCE'].isna().sum() # 0
#recalls['PRISON_NUMBER'].isna().sum() # 0

# RELEASES
#all_ipp_dpp = prepareMatch.prepareMatch(all_ipp_dpp)
# all_ipp_dpp.head()
skinned_sent = all_ipp_dpp[['FILE_REFERENCE','COMMON_ID','DOS','CUSTODY_TYPE_DESCRIPTION']]
skinned_sent = skinned_sent.rename(columns={'DOS':'DOS_SENT','CUSTODY_TYPE_DESCRIPTION':'CUSTODY_TYPE_SENT'})
# skinned_sent.head()

dateColsToChange =['LATEST_RELEASE_DATE']

        # Check wrong dates
    
check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(releases,col)],axis = 0,ignore_index=True)

check1= check1[dateColsToChange + [col for col in releases.columns if col not in dateColsToChange]]
check1.shape # 4 cases, out of bounds years
check1

# Make two corrections to dates
for column in dateColsToChange:
    releases[column] = releases[column].astype(str).str.replace("8201-05-08 00:00:00", "2018-01-31 00:00:00") # replaces entire cell value,else set regex = True
    releases[column] = releases[column].astype(str).str.replace("6201-07-09 00:00:00", "2011-06-09 00:00:00") # replaces entire cell value,else set regex = True
    # releases[column] = releases[column].astype(str).str.replace("14/09/2997", "14/09/2007") # replaces substring

    # Rerun check1 and see if if check1 is empty, then convert all datetime columns to datetime
    
#check1 =pd.DataFrame()
#for col in dateColsToChange:
    #check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(releases,col)],axis = 0,ignore_index=True)

#check1.shape # if zero, proceed

    # change certain columns to pandas datetime type
# releases[releases['PRISON_NUMBER']=='XF5015']

for column in dateColsToChange:
    releases[column] = pd.to_datetime(releases[column])
    
#releases.info()
#skinned_sent.info()

# duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

releases = prepareMatch.prepareMatch(releases)
#releases.head()

query = """SELECT a.*, 
                  b.*
            FROM releases AS a 
            INNER JOIN skinned_sent AS b

            ON      
                    (  (b.COMMON_ID = a.NOMS_ID OR
                        b.COMMON_ID = a.NOMS_TRIM OR
                        b.COMMON_ID = a.NOMS_START OR
                        b.COMMON_ID = a.NOMS_END OR
                        b.COMMON_ID = a.PRISON_NUMBER OR
                        b.COMMON_ID = a.PN_TRIM OR
                        b.COMMON_ID = a.PN_START OR
                        b.COMMON_ID = a.PN_END
                        ) AND b.COMMON_ID IS NOT NULL
                     ) OR
                     (  (b.FILE_REFERENCE = a.FILE_REFERENCE) AND 
                        b.FILE_REFERENCE IS NOT NULL
                     )
                     """

matched = duckdb.sql(query).df()
matched.shape #10871

releases = matched.copy()
#len(releases) # 10871
#releases.head()
#(releases['DOS'].isna()).sum() #0
#(releases['DOS_SENT'].isna()).sum() #0

#releases[releases['FILE_REFERENCE']=='W35234']

    # wrong release dates
#(releases['DOS_SENT'].dt.year < 2005).sum() # same person, a duplicate of an existing case so delete
#releases[releases['DOS_SENT'].dt.year < 2005]
#releases[releases['COMMON_ID']=='A3533AP']

#(releases['DOS'].dt.year < 2005).sum() # one case, a duplicate of an existing case so delete
#releases[releases['DOS'].dt.year < 2005]

releases = releases[releases['DOS_SENT'].dt.year >= 2005]

#(releases['DOS'].dt.year > 2014).sum() # 0 as expected
#(releases['DOS_SENT'].dt.year > 2014).sum() # 0 as expected
#len(releases) # 10866

#(releases['DOS'].isna()).sum() #0, no missing date of sentence
#(releases['FILE_REFERENCE'].isna()).sum() # 0, no missing file reference

# DETERMINE FIRST AND LATEST RELEASES
#(releases['RELEASE_DATE'] <= releases['DOS']).sum() # 510, these should be removed
#(releases['RELEASE_DATE'] <= releases['DOS_SENT']).sum() # 518

releases = releases[releases['RELEASE_DATE'] > releases['DOS_SENT']]
# len(releases) # 10349
    
    # First release date must be based on DOS as well
releases['FIRST_REL_DATE'] = releases.groupby(['COMMON_ID','DOS_SENT'])['RELEASE_DATE'].transform(lambda x: x.min())

    # Latest release date must be based on File reference only
#releases['RELEASE_DATE'].dt.year.value_counts(dropna=False).sort_index()
releases['LATEST_REL_DATE'] = releases.groupby('COMMON_ID')['RELEASE_DATE'].transform(lambda x: x.max())
#releases.head()

    # Deduplicate
#len(releases) # 10347
releases = releases.sort_values(['COMMON_ID','DOS_SENT'],na_position='first')
releases = releases.drop_duplicates(['COMMON_ID','DOS_SENT'],keep='last')
#len(releases) # 5749
#releases.head()

# Determine latest recall
recalls = prepareMatch.prepareMatch(recalls)
#recalls.head()

query2 = """SELECT a.*, 
                  b.*
            FROM recalls AS a 
            INNER JOIN skinned_sent AS b

            ON      
                    (  (b.COMMON_ID = a.NOMS_ID OR
                        b.COMMON_ID = a.NOMS_TRIM OR
                        b.COMMON_ID = a.NOMS_START OR
                        b.COMMON_ID = a.NOMS_END OR
                        b.COMMON_ID = a.PRISON_NUMBER OR
                        b.COMMON_ID = a.PN_TRIM OR
                        b.COMMON_ID = a.PN_START OR
                        b.COMMON_ID = a.PN_END
                        ) AND b.COMMON_ID IS NOT NULL
                     ) OR
                     (  (b.FILE_REFERENCE = a.FILE_REFERENCE) AND 
                        b.FILE_REFERENCE IS NOT NULL
                     )
                     """

matched2 = duckdb.sql(query2).df()
#matched2.shape

recalls = matched2.copy()

#len(recalls) # 7179
#(recalls['DOS'].isna()).sum() #0
#(recalls['DOS_SENT'].isna()).sum() #0

#(recalls['DOS_SENT'].dt.year < 2005).sum() # 0 cases, delete
#recalls[recalls['DOS_SENT'].dt.year < 2005]

recalls = recalls[recalls['DOS_SENT'].dt.year >= 2005]

#(recalls['LICENCE_REVOKE_DATE'] <= recalls['DOS_SENT']).sum() # 679

recalls = recalls[recalls['LICENCE_REVOKE_DATE'] > recalls['DOS_SENT']] # keep correct recalls
#len(recalls) # 6498

recalls['LATEST_RECALL'] = recalls.groupby('COMMON_ID')['LICENCE_REVOKE_DATE'].transform(lambda x: x.max())
#recalls.head()

 # Deduplicate
recalls = recalls.sort_values(['COMMON_ID','DOS_SENT'], na_position='first')
recalls = recalls.drop_duplicates(['COMMON_ID','DOS_SENT'],keep='last')
#len(recalls) # 3428

## Combine recall and release dates

recalls['LATEST_RECALL'] = recalls['LATEST_RECALL'].dt.normalize()

skinned_rec = recalls[['COMMON_ID','LATEST_RECALL']]

#releases.info()
#recalls.info()

combined = pd.merge(releases,skinned_rec,how='left', on ='COMMON_ID')
#combined.head()

 # Deduplicate
combined = combined.sort_values(['COMMON_ID','DOS_SENT'],na_position='first')
combined = combined.drop_duplicates(['COMMON_ID','DOS_SENT'],keep='last')
#len(combined) # 5749

#(combined['LATEST_REL_DATE'].isna()).sum() #0

combined['RECALLED_OR_RELEASED'] = 'released'
combined.loc[combined['LATEST_RECALL'] > combined['LATEST_REL_DATE'],'RECALLED_OR_RELEASED'] = 'recalled'

retain = ['COMMON_ID', 'FAMILY_NAME', 'DOS_SENT','RECALLED_OR_RELEASED','FIRST_REL_DATE','LATEST_REL_DATE','LATEST_RECALL','NOMS_ID', 'STATUS_DESCRIPTION', 'PRISON_NUMBER']

combined = combined[retain + [col for col in combined.columns if col not in retain]]

# combined['DOS_COUNT'] = combined.groupby('FILE_REFERENCE')['DOS_SENT'].transform(lambda x: x.nunique())

combined = combined.sort_values(['COMMON_ID','DOS_SENT'],na_position='first')
#combined.head(50)

# combined[combined['DOS_COUNT']>1].head(50)

combined_last = combined.drop_duplicates(['COMMON_ID','DOS_SENT'],keep='last').copy()
# combined_last[combined_last['DOS_COUNT']>1].head(50)

#combined_last.head()

# Bring in release details
# Bring in latest status (combined data)
skinned_combined = combined_last[['COMMON_ID','DOS_SENT','RECALLED_OR_RELEASED','FIRST_REL_DATE','LATEST_REL_DATE','LATEST_RECALL','RELEASE_TYPE_DESCRIPTION']]

skinned_combined = skinned_combined.rename(columns={'COMMON_ID':'COMMON_ID_2'})

#skinned_combined.head()

all_ipp_dpp_2 = pd.merge(all_ipp_dpp, skinned_combined, how='left', left_on=['COMMON_ID','DOS'], right_on=['COMMON_ID_2','DOS_SENT'])

retain = ['COMMON_ID', 'FAMILY_NAME', 'DOS','RECALLED_OR_RELEASED','FIRST_REL_DATE','LATEST_REL_DATE','LATEST_RECALL','NOMS_ID', 'STATUS_DESCRIPTION', 'PRISON_NUMBER']

all_ipp_dpp_2 = all_ipp_dpp_2[retain + [col for col in all_ipp_dpp_2.columns if col not in retain]]
#all_ipp_dpp['FILE_REFERENCE'] = all_ipp_dpp['FILE_REFERENCE'].astype(str)

all_ipp_dpp_2 = all_ipp_dpp_2.sort_values(['COMMON_ID','DOS'])
all_ipp_dpp_2 = all_ipp_dpp_2.drop_duplicates(['COMMON_ID','DOS'],keep='last')
len(all_ipp_dpp_2) # 8089
# all_ipp_dpp_2.head()

# all_ipp_dpp_2[all_ipp_dpp_2['FILE_REFERENCE']=='W35234']
# releases[releases['FILE_REFERENCE']=='W35234']

all_ipp_dpp_2['SENTENCED_AGE'] = np.where(all_ipp_dpp_2['DOS'] > all_ipp_dpp_2['DOB'],
                                         all_ipp_dpp_2.apply(lambda x: TimeDiffs.year_diff(x['DOB'],x['DOS']),axis=1),
                                        np.nan)

all_ipp_dpp_2['SENTENCED_AGE'] = all_ipp_dpp_2['SENTENCED_AGE'].astype(int)

# update
# all_ipp_dpp_2['RECALLED_OR_RELEASED'].value_counts(dropna=False)
all_ipp_dpp_2.loc[all_ipp_dpp_2['RECALLED_OR_RELEASED'].isna(),'RECALLED_OR_RELEASED'] ='unreleased'

# Current status
all_ipp_dpp_2['CURRENT_STATUS'] = all_ipp_dpp_2['RECALLED_OR_RELEASED']

# all_ipp_dpp_2.pivot_table(index=['CURRENT_STATUS','STATUS_DESCRIPTION'],aggfunc='size')
             
all_ipp_dpp_2['STATUS_DESCRIPTION'].value_counts(dropna=False)
#all_ipp_dpp_2.head()

all_ipp_dpp_2.loc[all_ipp_dpp_2['STATUS_DESCRIPTION'].isin(["Unlawfully at Large","Absconded"]),'CURRENT_STATUS'] = 'ual'

all_ipp_dpp_2.loc[all_ipp_dpp_2['STATUS_DESCRIPTION'].isin(["In Hospital",
                                                        "In Trial Leave Hospital",
                                                        "In Hospital (but duplicate of MHCS record)",
                                                        "In Hospital - Duplicate MH Record"]),'CURRENT_STATUS'] = 'hospital'

all_ipp_dpp_2.loc[all_ipp_dpp_2['STATUS_DESCRIPTION'].str.contains('Archived',case=False),'CURRENT_STATUS'] = 'archived'

all_ipp_dpp_2.loc[all_ipp_dpp_2['STATUS_DESCRIPTION'].isin(["Archived - quashed",
                                                        "Archived - sentence decreased",
                                                        "Disposed - Court",
                                                        "Disposed - Appeal"]),'CURRENT_STATUS'] = 'quashed'

all_ipp_dpp_2.loc[all_ipp_dpp_2['CANCELLED QUASHED REVIEW?'].notna(),'CURRENT_STATUS'] = 'quashed'

all_ipp_dpp_2.loc[all_ipp_dpp_2['INACTIVE TERMINATION REVIEW STATUS AS OF 04/10/24'] == 'Cancelled - Quashed','CURRENT_STATUS'] = 'quashed'

all_ipp_dpp_2.loc[all_ipp_dpp_2['STATUS_DESCRIPTION'].isin(["Removed Under TERs",
                                                       "Deported - 1",
                                                       "Repatriated",
                                                       "Extradited","CD - Deported"]),'CURRENT_STATUS'] = 'deported'

all_ipp_dpp_2.loc[all_ipp_dpp_2['INACTIVE TERMINATION REVIEW STATUS AS OF 04/10/24'] == 'Completed - Deported','CURRENT_STATUS'] = 'deported'

all_ipp_dpp_2.loc[all_ipp_dpp_2['INACTIVE TERMINATION REVIEW STATUS AS OF 04/10/24'] == 'Removed Under TERs','CURRENT_STATUS'] = 'deported'

all_ipp_dpp_2.loc[all_ipp_dpp_2['RELEASE_TYPE_DESCRIPTION'] == 'Deportation','CURRENT_STATUS'] = 'deported'

all_ipp_dpp_2.loc[all_ipp_dpp_2['LICENCE TERMINATED? (AS AT 21/08/24)'].notna(),'CURRENT_STATUS'] = 'terminated'

all_ipp_dpp_2.loc[all_ipp_dpp_2['STATUS_DESCRIPTION'] == 'IPP/DPP Licence Terminated','CURRENT_STATUS'] = 'terminated'

all_ipp_dpp_2.loc[all_ipp_dpp_2['RELEASE_TYPE_DESCRIPTION'] == 'Compassionate','CURRENT_STATUS'] = 'Compassionate'

all_ipp_dpp_2.loc[all_ipp_dpp_2['INACTIVE TERMINATION REVIEW STATUS AS OF 04/10/24'] == 'Deceased','CURRENT_STATUS'] = 'deceased'

all_ipp_dpp_2.loc[all_ipp_dpp_2['RELEASE_TYPE_DESCRIPTION'] == 'Death','CURRENT_STATUS'] = 'deceased'

all_ipp_dpp_2.loc[all_ipp_dpp_2['STATUS_DESCRIPTION'].str.contains('deceased',case=False),'CURRENT_STATUS'] = 'deceased'

all_ipp_dpp_2.loc[all_ipp_dpp_2['DECEASED REVIEW STATUS'].notna(),'CURRENT_STATUS'] = 'deceased'

# all_ipp_dpp_2['CURRENT_STATUS'].value_counts(dropna=False)

# all_ipp_dpp_2['DECEASED REVIEW STATUS'].notna().sum() # 508
# all_ipp_dpp_2.head()

# all_ipp_dpp_2.pivot_table(index=['NOTES','CURRENT_STATUS'],aggfunc='size').reset_index()
# len(all_ipp_dpp_2) # 8114

all_ipp_dpp_2.dtypes

del all_ipp_dpp_2['FILE_REFERENCE_2']
del all_ipp_dpp_2['COMMON_ID_2']

# ANY LIFE SENTENCE
isp_sentence = pd.read_excel('raw-data/isps-sentence-29-08-2024.xls')
strip_blanks(isp_sentence)
#isp_sentence.head()
#isp_sentence.info()

#(isp_sentence['FILE_REFERENCE'].isna()).sum() # 7
isp_sentence.loc[isp_sentence['FILE_REFERENCE'].isna(),'FILE_REFERENCE'] = isp_sentence['PRISON_NUMBER']

lifer_cond = ~(isp_sentence['CUSTODY_TYPE_DESCRIPTION'].isin(['DPP','IPP']))
isp_sentence['LIFER'] = 0
isp_sentence.loc[lifer_cond,'LIFER'] = 1

isp_sentence['LONGEST_TARIFF_EXIPRY_DATE'] = isp_sentence.groupby('FILE_REFERENCE')['TARIFF_EXPIRY_DATE'].transform('max')
isp_sentence['LIFE_SENTENCE'] = isp_sentence.groupby('FILE_REFERENCE')['LIFER'].transform('sum')

isp_sentence['ALL_SENTENCES'] = isp_sentence['FILE_REFERENCE'].map(
                                        isp_sentence.groupby('FILE_REFERENCE')['CUSTODY_TYPE_DESCRIPTION'].unique())

isp_sentence['ALL_SENTENCES'] = isp_sentence['ALL_SENTENCES'].apply(lambda x:', '.join(x))

ipp_sentence = isp_sentence[~lifer_cond].copy()
# ipp_sentence[ipp_sentence['LIFE_SENTENCE'] > 0].head()

ipp_sentence['HAS_LIFE_SENTENCE'] = False
ipp_sentence.loc[ipp_sentence['LIFE_SENTENCE'] > 0,'HAS_LIFE_SENTENCE'] = True
ipp_sentence[ipp_sentence['LIFE_SENTENCE'] > 0].head()

len(ipp_sentence) # 8125

sentence_skinned = ipp_sentence[['FILE_REFERENCE','DOS','LONGEST_TARIFF_EXIPRY_DATE','ALL_SENTENCES','HAS_LIFE_SENTENCE']]
sentence_skinned = sentence_skinned.rename(columns={'FILE_REFERENCE':'FILE_REFERENCE_2','DOS':'DOS_2'})
sentence_skinned.head()

all_ipp_dpp_2['FILE_REFERENCE'] = all_ipp_dpp_2['FILE_REFERENCE'].astype(str)
sentence_skinned['FILE_REFERENCE_2'] = sentence_skinned['FILE_REFERENCE_2'].astype(str)

all_ipp_dpp_2 = pd.merge(all_ipp_dpp_2,sentence_skinned, how='left', left_on='FILE_REFERENCE', right_on='FILE_REFERENCE_2')                                                                                                                       
all_ipp_dpp_2 = all_ipp_dpp_2.drop(['DOS_SENT','FILE_REFERENCE_2','DOS_2'],axis=1)
all_ipp_dpp_2.head()

all_ipp_dpp_2 = all_ipp_dpp_2.sort_values(['COMMON_ID','DOS'],na_position='first')
all_ipp_dpp_2 = all_ipp_dpp_2.drop_duplicates(['COMMON_ID','DOS'],keep='last')

all_ipp_dpp_2['FILE_REFERENCE'] = all_ipp_dpp_2['FILE_REFERENCE'] .astype(str)
all_ipp_dpp_2['PRISON_NUMBER'] = all_ipp_dpp_2['PRISON_NUMBER'] .astype(str)
all_ipp_dpp_2['ACTIVE TERMINATION REVIEW? (AS AT 19/08/24)'] = all_ipp_dpp_2['ACTIVE TERMINATION REVIEW? (AS AT 19/08/24)'].astype(str)
all_ipp_dpp_2['CRO_PNC'] = all_ipp_dpp_2['CRO_PNC'].astype(str)
all_ipp_dpp_2['COMMON_ID'] = all_ipp_dpp_2['COMMON_ID'].astype(str)

all_ipp_dpp_2.to_parquet('output-data/all_ipp_dpp_2.parquet')

# duplicates for counting

                                                                                                         
len(all_ipp_dpp_2) # 8089


