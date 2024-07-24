# IMPORT STUFF
import pandas as pd
import numpy as np
import s3fs

# SET COLUMN AND ROW LIMITS
pd.options.display.max_columns = None
pd.options.display.max_rows = None

# READ DATA FROM AMAZON WAREHOUSE
Releases = pd.read_excel("s3://alpha-omppg/Ad hoc/2023 04 30 - Time from Decision to Release/Releases_ISP_EDS.xls")

# CHANGE RELEVANT COLUMNS TO DATETIME TYPE
to_dates = ["DOB","LATEST_RELEASE_DATE","RELEASE_DATE","DOS","TARIFF_EXPIRY_DATE"]
for column in to_dates:
    ''' Returns date string as a date only'''
    Releases[column] = pd.to_datetime(Releases[column],dayfirst=True, errors = 'coerce').dt.normalize()

Releases.head()
Releases.info() # 11441 entries

# DEDUPLICATE ACCROSS ALL COLUMNS

Releases = Releases.drop_duplicates()
Releases.info() # 11441 entries

# TEST CASES 
def checkTestCases(df):
    test_cases = df[(df["FAMILY_NAME"].str.contains("test", case = False,regex = False)) | 
                    (df["FIRST_NAMES"].str.contains("test", case = False,regex = False)) | \
                    (df["PRISON_NUMBER"].str.contains("test", case = False,regex = False))
                   ]
    return test_cases

checkTestCases(Releases)

for column in ["FAMILY_NAME","FIRST_NAMES","PRISON_NUMBER"]:
    Releases = Releases[(~Releases[column].str.contains("test", case = False,na=False,regex = False)) | (Releases["NOMS_ID"] == 'A9432AC')]

    Releases.info() # 11422 entries

# REMOVE NOT SPECIFIEDS AND NON APPLICABLES

Releases["RELEASE_TYPE_DESCRIPTION"].unique()
Releases = Releases[~Releases["RELEASE_TYPE_DESCRIPTION"].isin(['Not Applicable','Not Specified'])]
                              
# FIX SOME RELEASE DATES

Releases.RELEASE_DATE.dt.year.value_counts(dropna = False).sort_index()
Releases[(Releases["RELEASE_DATE"].isna()) |(Releases["RELEASE_DATE"].dt.year > 2023)][["FILE_REFERENCE","FAMILY_NAME","LATEST_RELEASE_DATE","RELEASE_DATE"]]

dates_to_change = ['2203-02-20','2104-07-18']
dates_to_change_to = ['2023-02-20','2014-07-18']

for column in ["RELEASE_DATE","LATEST_RELEASE_DATE"]:
    for i in range(2):
        Releases.loc[Releases[column] == dates_to_change[i],column] = pd.Timestamp(dates_to_change_to[i])

Releases.loc[(Releases["FILE_REFERENCE"] == 'C38163') & (Releases["RELEASE_DATE"].isna()),"RELEASE_DATE"] = pd.Timestamp(year = 2019, month = 3, day = 24)
Releases.loc[(Releases["FILE_REFERENCE"] == 'C38163') & (Releases["LATEST_RELEASE_DATE"].isna()),"LATEST_RELEASE_DATE"] = pd.Timestamp(year = 2019, month = 3, day = 24)

Releases[Releases["FILE_REFERENCE"].isin(['I1767','O10373','C38163'])][["FILE_REFERENCE","FAMILY_NAME","LATEST_RELEASE_DATE","RELEASE_DATE"]]

len(Releases.index)
# Releases.loc[Releases["RELEASE_DATE"] == '2104-07-18',"RELEASE_DATE"] = pd.Timestamp(year =2014, month = 7, day = 18)
# Releases.loc[Releases["RELEASE_DATE"] == '2104-07-18',"RELEASE_DATE"] = pd.Timestamp(year =2014, month = 7, day = 18)
