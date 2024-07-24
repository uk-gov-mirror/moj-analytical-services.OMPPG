import pandas as pd
import numpy as np
import duckdb


pd.options.display.max_columns = None
pd.options.display.max_rows = None

filenames = ['Recalls_2014_2016.xls', 'Recalls_2017_2018.xls', 'Recalls_2019_2020.xls',
             'Recalls_2021_2022.xls', 'Recalls_2023.xls']

Recalls_14_22 = pd.DataFrame()

for filename in filenames:
    path = "s3://alpha-omppg/Data Central/PPUD Recalls/" + filename
    data = pd.read_excel(path)
    Recalls_14_22 = pd.concat([Recalls_14_22,data],ignore_index = True)

Recalls_14_22.head()
Recalls_14_22.dtypes

stringToDatetime = ['LICENCE_END','LICENCE_START','RELEASE_BEFORE_RECALL','SED']
Recalls_14_22[stringToDatetime] = Recalls_14_22[stringToDatetime].apply(pd.to_datetime,
                                                                        format='%Y-%m-%d %H:%M:%S',
                                                                        errors ='coerce')

# Normalize recall times to midnight, keeping it as a datetime object
recallTimes = ['LICENCE_REVOKE_DATE','RTC_DATE']
Recalls_14_22['LICENCE_REVOKE_DATE'] = pd.to_datetime(Recalls_14_22['LICENCE_REVOKE_DATE']).dt.normalize()
Recalls_14_22['RTC_DATE'] = pd.to_datetime(Recalls_14_22['RTC_DATE']).dt.normalize()

Recalls_14_22.shape
Recalls_14_22 = Recalls_14_22.drop_duplicates().reset_index(drop = True)
Recalls_14_22.shape

duplicates = Recalls_14_22[Recalls_14_22.duplicated(keep = False)]
duplicates.head()

High_Profile_SFOs = pd.read_excel("s3://alpha-omppg/Data Central/SFO/SFO High Profile 2017-2022.xlsx")
licenceSupTypes =['Life Licence','IPP','Post-Release']
High_Profile_SFOs = High_Profile_SFOs[High_Profile_SFOs['SUPERVISION_TYPE_DESCRIPTION'].isin(licenceSupTypes)]

High_Profile_SFOs = High_Profile_SFOs.drop_duplicates().reset_index(drop = True)
High_Profile_SFOs.head()
High_Profile_SFOs.shape


# Match Terminations and Releases
query =  """SELECT a.*, 
                   b.RELEASE_BEFORE_RECALL,
                   b.LICENCE_REVOKE_DATE,
                   b.LICENCE_START,
                   b.LICENCE_END,
                   b.SED,
                   b.TYPE_OF_LICENCE_DESCRIPTION,
                   b.RECALL_REASON_DESCRIPTIONS,
                   b.RECALL_TYPE_DESCRIPTION,
                   b.DOS,
                   b.CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION,
                   b.CUSTODY_TYPE_DESCRIPTION
                   
            FROM High_Profile_SFOs AS a LEFT JOIN Recalls_14_22 AS b 
            ON  (
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) OR
                    (a.NOMS_ID = b.NOMS_ID AND a.NOMS_ID IS NOT NULL) 
                ) AND
                a.PRISON_SENTENCE_START_DATE <= b.LICENCE_REVOKE_DATE"""

Matched1 = duckdb.sql(query).df()
retain = ['FILE_REFERENCE', 'FAMILY_NAME', 'PRISON_SENTENCE_START_DATE', 'DOS','PROBATION_SUPERVISION_START_DATE',
          'LICENCE_START','RELEASE_BEFORE_RECALL','DATE_OF_SFO','LICENCE_REVOKE_DATE','LICENCE_END','SED',
          'CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION','STAGE_12_DOCN_RECEIVED_ACTUAL']

retain = retain + [col for col in Matched1.columns if col not in retain]
Matched1 = Matched1[retain]
Matched1.head()
Matched1.shape

# deduplicate Matched1
Matched1['SHORTEST'] = abs((Matched1['DATE_OF_SFO'] - Matched1['LICENCE_REVOKE_DATE']).dt.days)

Matched_nodup = Matched1.copy()
Matched_nodup.sort_values(['SFO_ID','SHORTEST'], inplace=True)
Matched_nodup.head()
Matched_nodup[Matched_nodup['FILE_REFERENCE']=='M40503']
Matched_nodup = Matched_nodup.drop_duplicates(subset=['SFO_ID'])
Matched_nodup.shape
Matched_nodup.dtypes
Matched_nodup



import pandas as pd

# Calculating the thirds and determining the period
Matched_nodup['period'] = round((Matched_nodup['LICENCE_END'] - Matched_nodup['PROBATION_SUPERVISION_START_DATE']).dt.days / 3)
Matched_nodup['first_third'] = Matched_nodup['PROBATION_SUPERVISION_START_DATE'] + pd.to_timedelta(Matched_nodup['period'], unit='D')
Matched_nodup['second_third'] = Matched_nodup['PROBATION_SUPERVISION_START_DATE'] + pd.to_timedelta(Matched_nodup['period']*2, unit='D')

Matched_nodup[['PROBATION_SUPERVISION_START_DATE','LICENCE_END','period','first_third','second_third']].head()

# Determine the period in whichSFO_DATE falls
def determine_period(row):
  
    if pd.isna(row['period']):
        return " "
    elif row['DATE_OF_SFO'] <= row['first_third']:
        return 'first_third'
    elif row['DATE_OF_SFO'] <= row['second_third']:
        return 'second_third'
    else:
        return 'last_third'
    
Matched_nodup['SFO_POINT'] = Matched_nodup.apply(determine_period, axis=1)

# Drop the auxiliary columns if they are no longer needed
Matched_nodup.drop(['period'], axis=1, inplace=True)

# Save
Matched_nodup.to_excel("Matched_SFO.xlsx")
# Matched_nodup.to_excel(""s3://alpha-omppg/Data Central/SFO/Matched_SFO.xlsx")
