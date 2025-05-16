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

        # Import master list
master_term_dec = pd.read_excel("raw-data/ipp_daniel.xlsx",sheet_name='Terminated or Deceased')
master_rel = pd.read_excel("raw-data/ipp_daniel.xlsx",sheet_name='Released')
master_rec = pd.read_excel("raw-data/ipp_daniel.xlsx",sheet_name='Recalled')
master_unr = pd.read_excel("raw-data/ipp_daniel.xlsx",sheet_name='Unreleased')
master_oth = pd.read_excel("raw-data/ipp_daniel.xlsx",sheet_name='Others')

master = pd.concat([master_term_dec,master_rel,master_rec,master_unr,master_oth],axis=0)
# master = pd.read_excel("raw-data/IPP_Termination_Master_List_17_1_2024.xlsx")

master = master.drop_duplicates(['COMMON_ID','DOS'])
len(master) # 8065
master.head()

# master.dtypes

# master['CURRENT_STATUS'].value_counts(dropna=False)
#master['CURRENT_STATUS'] = master['CURRENT_STATUS'].str.title()
#master.loc[master['CURRENT_STATUS'] == 'Ipp Licence Terminated', 'CURRENT_STATUS'] = 'Terminated'

# --------------------------------------------------------------------------------------------
# 1. Identify Deceased and terminated cases
# --------------------------------------------------------------------------------------------

master['AUTO_TERMINATED'].value_counts(dropna=False)
master.loc[ master['AUTO_TERMINATED'].isin(['Yes','Yes_pending']), 'CURRENT_STATUS'] = 'Terminated'


sum(exclusion_condition) # 2924

wanted = master.copy()
exclusion_condition = wanted['CURRENT_STATUS'].isin(['Terminated','Deceased'])
len(wanted) # 8065

wanted['CURRENT_STATUS'].value_counts(dropna=False)

# IMPORT RELEASES AND RECALLS DATA

    # releases and recalls
releases = pd.read_excel("raw-data/isp-releases-up-to-30-12-2024.xls")
strip_blanks(releases)
releases['RELEASE_TYPE_DESCRIPTION'].value_counts(dropna=False)
releases = releases[~releases['RELEASE_TYPE_DESCRIPTION'].isin(['Not Applicable','Not Specified'])]

recalls = pd.read_excel("raw-data/isp-recalls-up-to-30-12-2024.xls")
strip_blanks(recalls)

#len(releases) # 19283
#len(recalls) # 10650
#releases.info()
#recalls.head()

#releases['NOMS_ID'].isna().sum() # 1184
#releases['FILE_REFERENCE'].isna().sum() # 1
# releases[releases['FILE_REFERENCE'].isna()]
# releases.loc[releases['FILE_REFERENCE'].isna(),'FILE_REFERENCE'] = releases['PRISON_NUMBER']
#releases['PRISON_NUMBER'].isna().sum() # 0

#recalls['NOMS_ID'].isna().sum() # 141
#recalls['FILE_REFERENCE'].isna().sum() # 0
#recalls['PRISON_NUMBER'].isna().sum() # 0

# RELEASES
#all_ipp_dpp = prepareMatch.prepareMatch(all_ipp_dpp)
# all_ipp_dpp.head()

skinned_sent = wanted[~exclusion_condition][['FILE_REFERENCE','COMMON_ID','DOS','CUSTODY_TYPE_DESCRIPTION','FIRST_REL_DATE','LATEST_REL_DATE','LATEST_RECALL_DATE','CURRENT_STATUS']]

skinned_sent = skinned_sent.rename(columns={'DOS':'DOS_SENT','CUSTODY_TYPE_DESCRIPTION':'CUSTODY_TYPE_SENT',
                                           'FIRST_REL_DATE':'FIRST_REL_DATE_OLD',
                                           'LATEST_REL_DATE':'LATEST_REL_DATE_OLD',
                                           'LATEST_RECALL_DATE':'LATEST_RECALL_DATE_OLD',
                                           'CURRENT_STATUS':'CURRENT_STATUS_OLD'})
# skinned_sent.head()

# releases.dtypes
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
    
#releases.dtypes

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
                        b.COMMON_ID = a.PN_END OR
                        b.COMMON_ID = a.CRO_PNC
                        ) AND b.COMMON_ID IS NOT NULL
                     ) OR
                     (  (b.FILE_REFERENCE = a.FILE_REFERENCE) AND 
                        b.FILE_REFERENCE IS NOT NULL
                     )
                     """

matched = duckdb.sql(query).df()
matched.shape # 6798

releases_2 = matched.copy()
#len(releases_2) # 6798
#releases_2.head()
#sum(releases_2['DOS'].isna())#0
#(releases_2['DOS_SENT'].isna()).sum() #0

    # wrong release dates
#(releases_2['DOS_SENT'].dt.year < 2005).sum() # 0

#(releases_2['DOS'].dt.year < 2005).sum() # 11 cases, possibly with concurrent life sentences
#releases_2[releases_2['DOS'].dt.year < 2005]

#(releases_2['DOS'].isna()).sum() #0, no missing date of sentence

# DETERMINE FIRST AND LATEST releases_2
#(releases_2['RELEASE_DATE'] <= releases_2['DOS']).sum() # 0
#(releases_2['RELEASE_DATE'] <= releases_2['DOS_SENT']).sum() # 15

releases_2 = releases_2[releases_2['RELEASE_DATE'] > releases_2['DOS_SENT']]
# len(releases_2) # 6786
    
    # First release date must be based on DOS as well
# skinned_sent.head()

releases_2['FIRST_REL_DATE'] = releases_2.groupby(['COMMON_ID','DOS_SENT'])['RELEASE_DATE'].transform(lambda x: x.min())

    # Latest release date must be based on File reference only
#releases_2['RELEASE_DATE'].dt.year.value_counts(dropna=False).sort_index()
releases_2['LATEST_REL_DATE'] = releases_2.groupby('COMMON_ID')['RELEASE_DATE'].transform(lambda x: x.max())
#releases_2.head()

    # Deduplicate
#len(releases_2) # 10347
releases_2 = releases_2.sort_values(['COMMON_ID','DOS_SENT'])
releases_2 = releases_2.drop_duplicates(['COMMON_ID','DOS_SENT'])
#len(releases_2) # 3194

    # use new first rel
#releases_2.loc[releases_2['FIRST_REL_DATE_OLD'].isna(),'FIRST_REL_DATE_OLD'] = releases_2['FIRST_REL_DATE']
#sum(releases_2['FIRST_REL_DATE'] != releases_2['FIRST_REL_DATE_OLD']) # 3 How?
#releases_2[releases_2['FIRST_REL_DATE'] != releases_2['FIRST_REL_DATE_OLD']].head()

    # use the latest rel
#releases_2.loc[releases_2['LATEST_REL_DATE_OLD'].isna(),'LATEST_REL_DATE_OLD'] = releases_2['LATEST_REL_DATE']
#sum(releases_2['LATEST_REL_DATE'] != releases_2['LATEST_REL_DATE_OLD']) # 161
#releases_2[releases_2['LATEST_REL_DATE'] != releases_2['LATEST_REL_DATE_OLD']].head()

releases_2 = releases_2.drop(['FIRST_REL_DATE_OLD','LATEST_REL_DATE_OLD'],axis=1)

#releases_2.head()

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
                        b.COMMON_ID = a.PN_END OR
                        b.COMMON_ID = a.CRO_PNC
                        ) AND b.COMMON_ID IS NOT NULL
                     ) OR
                     (  (b.FILE_REFERENCE = a.FILE_REFERENCE) AND 
                        b.FILE_REFERENCE IS NOT NULL
                     )
                     """

matched2 = duckdb.sql(query2).df()
#matched2.shape

recalls_2 = matched2.copy()

#len(recalls_2) # 5362
#(recalls_2['DOS'].isna()).sum() #0
#(recalls_2['DOS_SENT'].isna()).sum() #0

#(recalls_2['DOS_SENT'].dt.year < 2005).sum() # 0 cases, delete
#recalls_2[recalls_2['DOS_SENT'].dt.year < 2005]

#(recalls_2['LICENCE_REVOKE_DATE'] <= recalls_2['DOS_SENT']).sum() # 679
recalls_2.info()

recalls_2 = recalls_2[recalls_2['LICENCE_REVOKE_DATE'] > recalls_2['DOS_SENT']] # keep correct recalls_2
#len(recalls_2) # 5351

recalls_2['LATEST_RECALL'] = recalls_2.groupby('COMMON_ID')['LICENCE_REVOKE_DATE'].transform(lambda x: x.max())
#recalls_2.head()

 # Deduplicate
recalls_2 = recalls_2.sort_values(['COMMON_ID','DOS_SENT'])
recalls_2 = recalls_2.drop_duplicates(['COMMON_ID','DOS_SENT'])
#len(recalls_2) # 2591

## Combine recall and release dates

recalls_2['LATEST_RECALL'] = recalls_2['LATEST_RECALL'].dt.normalize()
recalls_2.head()

    # use the latest rec
#recalls_2.loc[recalls_2['LATEST_RECALL_DATE_OLD'].isna(),'LATEST_RECALL_DATE_OLD'] = recalls_2['LATEST_RECALL']
#sum(recalls_2['LATEST_RECALL'] != recalls_2['LATEST_RECALL_DATE_OLD']) # 21
#recalls_2[recalls_2['LATEST_RECALL'] != recalls_2['LATEST_RECALL_DATE_OLD']].head()

skinned_rec = recalls_2[['COMMON_ID','LATEST_RECALL']]

#releases_2.info()
#recalls_2.info()

combined = pd.merge(releases_2,skinned_rec,how='left', on ='COMMON_ID')
#combined.head()

 # Deduplicate
combined = combined.sort_values(['COMMON_ID','DOS_SENT'])
combined = combined.drop_duplicates(['COMMON_ID','DOS_SENT'])
#len(combined) # 3194,3210, 5749

combined['CURRENT_STATUS'] = combined['CURRENT_STATUS_OLD']

#(combined['LATEST_REL_DATE'].isna()).sum() #0

combined['RECALLED_OR_RELEASED'] = 'Released'
combined.loc[combined['LATEST_RECALL'] > combined['LATEST_REL_DATE'],'RECALLED_OR_RELEASED'] = 'Recalled'

retain = ['COMMON_ID', 'FAMILY_NAME', 'DOS_SENT','RECALLED_OR_RELEASED','CURRENT_STATUS','FIRST_REL_DATE','LATEST_REL_DATE','LATEST_RECALL','NOMS_ID', 'STATUS_DESCRIPTION', 'PRISON_NUMBER']

combined = combined[retain + [col for col in combined.columns if col not in retain]]

# combined['DOS_COUNT'] = combined.groupby('FILE_REFERENCE')['DOS_SENT'].transform(lambda x: x.nunique())

combined = combined.sort_values(['COMMON_ID','DOS_SENT'])
combined = combined.drop_duplicates(['COMMON_ID','DOS_SENT']).copy()
#combined.head(50)

combined.pivot_table(index='CURRENT_STATUS',columns='RECALLED_OR_RELEASED',aggfunc='size',dropna=False)

rec_to_rel = (combined['CURRENT_STATUS_OLD'] =='Recalled') & (combined['RECALLED_OR_RELEASED'] =='Released')
rel_to_rec = (combined['CURRENT_STATUS_OLD'] =='Released') & (combined['RECALLED_OR_RELEASED'] =='Recalled')
unrel_to_rel = (combined['CURRENT_STATUS_OLD'] =='Unreleased') & (combined['RECALLED_OR_RELEASED'] =='Released')
unrel_to_rec = (combined['CURRENT_STATUS_OLD'] =='Unreleased') & (combined['RECALLED_OR_RELEASED'] =='Recalled')

rec_to_rel.sum() #144
rel_to_rec.sum()
unrel_to_rel.sum()
unrel_to_rec.sum()

combined.loc[rec_to_rel,'CURRENT_STATUS'] = 'Released'
combined.loc[rel_to_rec,'CURRENT_STATUS'] = 'Recalled'
combined.loc[unrel_to_rel,'CURRENT_STATUS'] = 'Released'
combined.loc[unrel_to_rec,'CURRENT_STATUS'] = 'Recalled'

combined.pivot_table(index='CURRENT_STATUS',columns='RECALLED_OR_RELEASED',aggfunc='size',dropna=False)

# combined_last[combined_last['DOS_COUNT']>1].head(50)

#combined_last.head()

# Bring in release details
# Bring in latest status (combined data)
skinned_combined = combined[['COMMON_ID','CURRENT_STATUS','DOS_SENT','FIRST_REL_DATE','LATEST_REL_DATE','LATEST_RECALL','RELEASE_TYPE_DESCRIPTION']]

# [i+':' + i+'_NEW' for i in skinned_combined.columns]

skinned_combined = skinned_combined.rename(
    columns={'COMMON_ID':'COMMON_ID_2','CURRENT_STATUS':'CURRENT_STATUS_NEW',
             'DOS_SENT':'DOS_SENT_NEW','FIRST_REL_DATE':'FIRST_REL_DATE_NEW',
             'LATEST_REL_DATE':'LATEST_REL_DATE_NEW','LATEST_RECALL':'LATEST_RECALL_NEW',
             'RELEASE_TYPE_DESCRIPTION':'RELEASE_TYPE_DESCRIPTION_NEW'})

#skinned_combined.head()

wanted = pd.merge(wanted, skinned_combined, how='left', left_on=['COMMON_ID','DOS'], right_on=['COMMON_ID_2','DOS_SENT_NEW'])
len(wanted) #8065

status_cond = wanted['CURRENT_STATUS'] != wanted['CURRENT_STATUS_NEW']
wanted.pivot_table(index='CURRENT_STATUS',columns='CURRENT_STATUS_NEW',aggfunc='size',dropna=False)

wanted.loc[wanted['CURRENT_STATUS_NEW'].notna(),'CURRENT_STATUS'] = wanted['CURRENT_STATUS_NEW']

wanted[wanted['CURRENT_STATUS'].isin(['Recalled','Released']) & wanted['CURRENT_STATUS_NEW'].isna()]

# wanted.loc[[5003], 'CURRENT_STATUS'] = 'EPP'

len(wanted) # 8065
# wanted.head()

# ANY LIFE SENTENCE
isp_sentence = pd.read_excel('raw-data/isp-sentence-up-to-31-12-2024.xls')
strip_blanks(isp_sentence)
isp_sentence = prepareMatch.prepareMatch(isp_sentence)
#isp_sentence.head()
#isp_sentence.info()

exclusion_condition = wanted['CURRENT_STATUS'].isin(['Terminated','Deceased'])
skinned_wanted = wanted[~exclusion_condition][['COMMON_ID','DOS']]
len(skinned_wanted) # 5141

query3 = """SELECT a.STATUS_DESCRIPTION AS STATUS_DESCRIPTION_NEW, 
                  b.*
            FROM skinned_wanted AS b 
            LEFT JOIN isp_sentence AS a

            ON      
                    (  (b.COMMON_ID = a.NOMS_ID OR
                        b.COMMON_ID = a.NOMS_TRIM OR
                        b.COMMON_ID = a.NOMS_START OR
                        b.COMMON_ID = a.NOMS_END OR
                        b.COMMON_ID = a.PRISON_NUMBER OR
                        b.COMMON_ID = a.PN_TRIM OR
                        b.COMMON_ID = a.PN_START OR
                        b.COMMON_ID = a.PN_END OR
                        b.COMMON_ID = a.CRO_PNC
                        ) AND b.COMMON_ID IS NOT NULL
                     ) AND a.DOS = b.DOS
                     """
matched3 = duckdb.sql(query3).df()
matched3.shape #5157

matched3 = matched3.drop_duplicates(['COMMON_ID','DOS'])
matched3.head()

wanted = pd.merge(wanted, matched3, how='left', left_on=['COMMON_ID','DOS'], right_on=['COMMON_ID','DOS'])
len(wanted) # 8065

wanted.pivot_table(index='CURRENT_STATUS',columns='STATUS_DESCRIPTION_NEW',aggfunc='size',dropna=False)

wanted.loc[wanted['STATUS_DESCRIPTION_NEW'].str.contains('deceased',case=False,na=False),'CURRENT_STATUS'] = 'Deceased'

wanted.loc[wanted['STATUS_DESCRIPTION_NEW'].str.contains('Terminated',case=False,na=False),'CURRENT_STATUS'] = 'Terminated'





