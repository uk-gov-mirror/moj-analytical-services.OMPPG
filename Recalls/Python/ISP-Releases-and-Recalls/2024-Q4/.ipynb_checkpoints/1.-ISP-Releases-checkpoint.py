""" 
GOAL: PRODUCE RELEASES OF ISPS FOR OMSQ. A BY-PRODUCT IS FIRST RELEASES OF ISPS
By Eric Nyame, 05/02/2024
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
#importlib.reload(openMatch)
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
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #
        
#----------------------------------Set globals

year = 2024
quarter = 3

#----------------------------------Import NOMIS data

disch20132015 = pd.read_csv(f's3://alpha-omppg/isp_releases/NOMIS/discharges20132015.csv')
disch20132015.info()
disch20132015.head()

disch20132015.columns = disch20132015.columns.str.upper()

strip_blanks(disch20132015)

    # Data type changes
disch20132015['DATEDIS'] = pd.to_datetime(disch20132015['DATEDIS'],dayfirst = True)
disch20132015['DOB'] = pd.to_datetime(disch20132015['DOB'], dayfirst = True)

#----------------------------------Import PPUD data

releases = pd.read_excel(f's3://alpha-omppg/isp_releases/PPUD/PPUD_Releases_{year}Q{quarter}.xls')
releases_2010 = pd.read_excel(f's3://alpha-omppg/isp_releases/PPUD/Releases 2010.xls')
releases_2011 = pd.read_excel(f's3://alpha-omppg/isp_releases/PPUD/Releases 2011.xls')
releases_2012 = pd.read_excel(f's3://alpha-omppg/isp_releases/PPUD/Releases 2012.xls')

    # Check colums - mostly to correct datetime columns appearing as objects
releases.info() # 2042,20081

strip_blanks(releases)

    # Convert columns that should be datetime to datetime
releases.select_dtypes(include=['object']).dtypes # find datetime column showing as an object column

dateColsToChange =['LATEST_RELEASE_DATE']

check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(releases,col)],axis = 0,ignore_index=True)

check1= check1[dateColsToChange + [col for col in releases.columns if col not in dateColsToChange]]
check1.shape # 5 cases, out of bounds years
check1

# Make two corrections to dates
for column in dateColsToChange:
    releases[column] = releases[column].astype(str).str.replace("8201-05-08 00:00:00", "2018-01-31 00:00:00") # replaces entire cell value,else set regex = True
    releases[column] = releases[column].astype(str).str.replace("6201-07-09 00:00:00", "2011-06-09 00:00:00") # replaces entire cell value,else set regex = True
    # releases[column] = releases[column].astype(str).str.replace("14/09/2997", "14/09/2007") # replaces substring

    # Rerun check1 and see if if check1 is empty, then convert all datetime columns to datetime
    
check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(releases,col)],axis = 0,ignore_index=True)

check1.shape # if zero, proceed

    # change certain columns to pandas datetime type
# releases[releases['PRISON_NUMBER']=='XF5015']

for column in dateColsToChange:
    releases[column] = pd.to_datetime(releases[column])

releases.select_dtypes(include=['datetime64']).dtypes
releases.info()

    # check the three other ppud files and verify data types

# for i in range(2010,2013):
    # print(f'releases_{i} = releases_{i}.convert_dtypes()')
          
strip_blanks(releases_2010)
strip_blanks(releases_2011)
strip_blanks(releases_2012)

releases_2010.info()
releases_2011.info()
releases_2012.info()
    
#---------------------------------- Remove Test cases
    # Check 'test' cases and remove
releases[releases['FAMILY_NAME'].astype(str).str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

releases[releases['FIRST_NAMES'].astype(str).str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

Test_Case_Mask =  (   (releases['FAMILY_NAME'].astype(str).str.contains('Test',case = False,na = False)) |
                      (releases['FIRST_NAMES'].astype(str).str.contains('Test',case = False,na = False))
                  ) & (releases['FILE_REFERENCE'] != 'T18122')

# releases[Test_Case_Mask][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 24 cases

releases = releases[~Test_Case_Mask]

releases.shape  # 20413,20055

    # Check 'case' cases and remove
releases[releases['FAMILY_NAME'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 6

releases[releases['FIRST_NAMES'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 6

    # Check 'digit' cases - these are normally good and shoulbe untouched
releases[releases['FAMILY_NAME'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 
releases[releases['FIRST_NAMES'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 

#---------------------------------- Drop duplicates
releases.shape # 20055
releases = releases.drop_duplicates()
releases.shape

#---------------------------------- Release date must not be before dos

    # check range of years for release date and dos
#releases['RELEASE_DATE'].dt.year.value_counts(dropna = False).sort_index()
#releases['DOS'].dt.year.value_counts(dropna = False).sort_index() # some missing data

    # note some entries with missing DOS
#releases[releases['DOS'].isna()].head()[['FILE_REFERENCE','FAMILY_NAME','DOS','RELEASE_DATE']]

    # remove release dates less than dos, excluding missing dos and release cases

releases = releases[(releases['RELEASE_DATE'] >= releases['DOS']) |
                    (releases['DOS'].isna()) |
                    (releases['RELEASE_DATE'].isna())
                   ]
releases.shape # 20413, 20055

#---------------------------------- Matching PPUD AND NOMIS

    # prepare match
releases2 = prepareMatch.prepareMatch(releases)

    # check its effect on missing prison numbers and 
releases2[(releases2.PRISON_NUMBER.isna()) | (releases2.NOMS_ID.isna())].head()
releases2.info()

    # drop the length variables
releases2.drop(['PN_LENGTH','NOMS_LENGTH'],axis=1,inplace = True)

    # before join, check missing release dates. None missing is helpful
releases2['RELEASE_DATE'].isna().sum() #0
disch20132015['DATEDIS'].isna().sum() #0

    # the sql query fucntion
def query_year(df1,df2,year):
    
    df1a = df1[df1['RELEASE_DATE'].dt.year == year]
    
    df2a = df2[df2['DATEDIS'].dt.year == year]
    
    query = f"""SELECT DISTINCT a.*, 
                   b.CESTAB,
                   b.CESTCODE,
                   b.DISCODE,
                   B.DATEDIS,
                   b.NOMIS_NO, 
                   b.SURNAME AS SURNAME_DIS, 
                   b.DOB AS DOB_DIS, 
                   b.INIT AS INIT_DIS
            FROM df1a AS a LEFT JOIN df2a AS b 
            ON  ( (datediff('day',a.RELEASE_DATE,b.DATEDIS) <= 14) OR 
                  (datediff('day',b.DATEDIS,a.RELEASE_DATE) <= 14) 
                ) AND
                ( (
                    (a.NOMS_ID = b.NOMIS_NO OR
                     a.NOMS_TRIM = b.NOMIS_NO OR
                     a.NOMS_START = b.NOMIS_NO OR
                     a.NOMS_END = b.NOMIS_NO
                     ) AND b.NOMIS_NO IS NOT NULL
                  ) OR
                  (
                      (a.FAMILY_NAME = b.SURNAME) and 
                      (a.DOB = b.DOB) and 
                      (a.INIT = b.INIT)
                  )
                )
                """
    result = duckdb.sql(query).df()
    return result

    # execute the matches
relsMatched2013 = query_year(releases2,disch20132015,2013)
relsMatched2014 = query_year(releases2,disch20132015,2014)
relsMatched2015 = query_year(releases2,disch20132015,2015)

    # replace 2013-2015 with the matched datasets
releases_extra = releases2[(releases2['RELEASE_DATE'].dt.year < 2013) | 
                           (releases2['RELEASE_DATE'].dt.year > 2015)].copy()

releases_extra.shape # 170,053,16700,16282

releases_matched = pd.concat([releases_extra,relsMatched2013,relsMatched2014,relsMatched2015],
                             axis = 0,
                             ignore_index=True) # 

releases_matched.shape # 20453,20095, 19675

#---------------------------------- Rate quality of the match

def calculate_match(row):
    
    condition_a = pd.notna(row['NOMIS_NO']) and (
        row['NOMIS_NO'] in [row['NOMS_ID'], row['NOMS_TRIM'], row['NOMS_START'], row['NOMS_END']]
    )
    
    # Check for FAMILY_NAME, DOB, INIT not missing and equals their counterparts
    condition_b = (
        pd.notna(row['FAMILY_NAME']) and row['FAMILY_NAME'] == row['SURNAME_DIS'] and
        pd.notna(row['DOB']) and row['DOB'] == row['DOB_DIS'] and
        pd.notna(row['INIT']) and row['INIT'] == row['INIT_DIS']
    )
    
    if condition_a and condition_b:
        return 3
    elif condition_a:
        return 3
    elif condition_b:
        return 1
    else:
        return 0

    # Create Match column by applying the function to each row
releases_matched['MATCH'] = releases_matched.apply(calculate_match, axis=1)

releases_matched.shape

# releases_matched['MATCH'].value_counts(dropna = False)

    # check the match worked
releases_matched[releases_matched['MATCH'] ==2].head(10)[['NOMIS_NO','NOMS_ID','NOMS_TRIM','NOMS_END',
                           'FAMILY_NAME','SURNAME_DIS','DOB','DOB_DIS',
                           'INIT','INIT_DIS','MATCH']]

    # Drop some columns
releases_matched = releases_matched.drop(columns=['NOMIS_NO', 'SURNAME_DIS', 'DOB_DIS', 'INIT_DIS'])

#---------------------------------- Create some variables

    # Calculate the absolute difference in days between RELEASE_DATE and DATEDIS
releases_matched['DATEDIF'] = (releases_matched['RELEASE_DATE'] - releases_matched['DATEDIS']).dt.days.abs()

# releases_matched[~releases_matched['DATEDIS'].isna()].head()

# releases_matched[releases_matched['DATEDIS'].isna()].head()[['FILE_REFERENCE','RELEASE_DATE','DATEDIS','DATEDIF']]

    # Create UNIQUEREF by concatenate PRISON_NUMBER and RELEASE_DATE 
releases_matched['UNIQUEREF'] = releases_matched['PRISON_NUMBER'].astype(str) + releases_matched['RELEASE_DATE'].astype(str)

# releases_matched[releases_matched['PRISON_NUMBER'].isna()].head()[['FILE_REFERENCE','PRISON_NUMBER','RELEASE_DATE','UNIQUEREF']]

#---------------------------------- De-duplicate
releases_matched.sort_values(by=['UNIQUEREF','MATCH','DATEDIF'],ascending = [True,False,True], inplace = True)

    # Check cases where DATEDIF is smaller but MATCH is lower - if non skip
releases_matched[~releases_matched['DATEDIS'].isna()][releases_matched[~releases_matched['DATEDIS'].isna()].duplicated(subset='UNIQUEREF',keep=False)][['NOMS_ID','FAMILY_NAME','UNIQUEREF','MATCH','DATEDIF','RELEASE_DATE','DATEDIS']]

        # Find the row with the highest MATCH for each ID
#highest_match_df = releases_matched.loc[releases_matched.groupby('UNIQUEREF')['MATCH'].idxmax()][['UNIQUEREF','DATEDIF']]
#highest_match_df = highest_match_df[~highest_match_df['DATEDIF'].isna()]
#len(highest_match_df)

        # Calculate the overall minimum DATEDIF for each ID
#overall_min_datedif = releases_matched.groupby('UNIQUEREF')['DATEDIF'].transform('min')
#overall_min_datedif = overall_min_datedif[pd.notna(overall_min_datedif)]

        # Find IDs where the selected highest MATCH row does not have the lowest DATEDIF
#ids_to_keep = highest_match_df[highest_match_df['DATEDIF'] != overall_min_datedif[highest_match_df.index]]['UNIQUEREF']
#len(ids_to_keep)

        # Filter the original DataFrame to keep all rows for these IDs
#check1 = releases_matched[releases_matched['UNIQUEREF'].isin(ids_to_keep)]
#len(check1)

#check1[check1.duplicated(subset='UNIQUEREF',keep=False)][['NOMS_ID','FAMILY_NAME','UNIQUEREF','MATCH','DATEDIF','RELEASE_DATE','DATEDIS']]

        # Make some corrections if check1 is not empty

# releases_matched.loc[[17801,17832,17835,16590],'MATCH'] = 3
    
    # Now carry on with deduplication
    
releases_matched.sort_values(by=['UNIQUEREF','MATCH','DATEDIF'],ascending = [True,False,True], inplace = True)

releases_matched =releases_matched.drop_duplicates(subset='UNIQUEREF', keep ='first')
releases_matched.shape # 20308,19952, 19539

#---------------------------------- Filter and add some variables 
    # Create three masks/
discode_mask = ~(releases_matched['DISCODE'].isin(['DD', 'DL', 'FR', 'XX']))

released_from_mask = ~(releases_matched['RELEASED_FROM_DESCRIPTION'].str.contains("N Irish|LASCH|SCOTLAND", na=False))

dates_mask = (
    (releases_matched['RELEASE_DATE'] >= releases_matched['TARIFF_EXPIRY_DATE']) | 
    releases_matched['TARIFF_EXPIRY_DATE'].isna() | 
    releases_matched['TARIFF_EXPIRY_DATE'].dt.year.eq(1900) | 
    (releases_matched['TARIFF_EXPIRY_DATE'] < releases_matched['DOS'])
)

    # Combine conditions and filter the DataFrame
Releases_final = releases_matched[discode_mask & released_from_mask & dates_mask].copy()

Releases_final.shape # 20165,19811,19399

    # Add 'I' to end of releasing establishment name for matching to Open prison data*
Releases_final['CESTCODE2'] = np.where(pd.notna(Releases_final['CESTCODE']),
                                       Releases_final['CESTCODE'] +"I",
                                       np.nan)

Releases_final = Releases_final.drop(columns=['CESTCODE'])

Releases_final = Releases_final.rename(columns={'CESTCODE2': 'CESTCODE'})

Releases_final = Releases_final.drop(columns=['MATCH','UNIQUEREF'])

#---------------------------------- Identify previous and next release dates

    # Sort the DataFrame by PRISON_NUMBER and RELEASE_DATE in ascending order
Releases_final = Releases_final.sort_values(by=['PRISON_NUMBER', 'RELEASE_DATE'])

# Create the NEXT_RELEASE_DATE column by shifting RELEASE_DATE up by one within each PRISON_NUMBER group
Releases_final['NEXT_RELEASE_DATE'] = Releases_final.groupby('PRISON_NUMBER')['RELEASE_DATE'].shift(-1)

Releases_final['LAST_RELEASE_DATE'] = Releases_final.groupby('PRISON_NUMBER')['RELEASE_DATE'].shift(1)

# Releases_final.head(50)[['PRISON_NUMBER', 'RELEASE_DATE','NEXT_RELEASE_DATE','LAST_RELEASE_DATE']]

#---------------------------------- Add release conditions

Releases_final2 = openMatch.openRelease(Releases_final)
Releases_final2.shape # 20170,19816, 19404

#---------------------------------- Remove pre-2013 releases and replace with published 2010-2012 releases
 
Releases_final2 = Releases_final2[Releases_final2['RELEASE_DATE'].dt.year >= 2013]

Releases_final2 = pd.concat([Releases_final2,releases_2010,releases_2011,releases_2012],
                             axis = 0,
                             ignore_index=True)

Releases_final2 = Releases_final2.drop(['MAPPA_LEVEL_DESCRIPTION','OWNING_CASEWORKER_DESCRIPTION',
                                       'OWNING_TEAM_DESCRIPTION','UAL_FLAG'],axis=1)


Releases_final2 = Releases_final2.rename(columns={'CURRENT_ESTABLISHMENT_DESCRIPTION': 'CURRENT_ESTABLISHMENT',
                                                 'RELEASED_FROM_CATEGORY_ID_DESCRIPTION':'RELEASED_FROM_CATEGORY'})

Releases_final2.info()

Releases_final2.head()

# Some conversions for parquet
Releases_final2['CRO_PNC'] = Releases_final2['CRO_PNC'].astype(str)
Releases_final2['PRISON_NUMBER'] = Releases_final2['PRISON_NUMBER'].astype(str)

#---------------------------------- Temporary Save, delete later
Releases_final2.to_parquet(f"isp_releases_{year}q{quarter}_step1.parquet")

