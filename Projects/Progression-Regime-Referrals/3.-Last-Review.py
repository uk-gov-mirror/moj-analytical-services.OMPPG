""" 
GOAL: CREATE GPP AND INFORMATION TO QUARTERLY ISP POP FOR OMSQ
By Eric Nyame, 14/04/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
# print(duckdb.__version__)
import importlib

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
# from my_log import my_log
import Out_of_bounds_dates
import prepareMatch
importlib.reload(prepareMatch)
import openMatch
importlib.reload(openMatch)
import TimeDiffs
import tariff_groups
importlib.reload(tariff_groups)

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
        

#---------------------------------- Load GPP data

gpp_ipp = pd.read_excel(f's3://alpha-omppg/ISP Population/PPUD/{year}Q{quarter}/PPUD_IPP_GPP_{year}Q{quarter}.xls')
gpp_life = pd.read_excel(f's3://alpha-omppg/ISP Population/PPUD/{year}Q{quarter}/PPUD_Life_GPP_{year}Q{quarter}.xls')

gpp = pd.concat([gpp_ipp,gpp_life],ignore_index = True)

gpp.shape

gpp = gpp.drop_duplicates()

gpp.shape

strip_blanks(gpp)


    # Convert columns that should be datetime to datetime
gpp.info()

dateColsToChange =['CURRENT_TARGET_DATE']

        # Check wrong dates
    
check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(gpp,col)],axis = 0,ignore_index=True)

check1= check1[dateColsToChange + [col for col in gpp.columns if col not in dateColsToChange]]
check1.shape #6 cases, out of bounds years
check1

# Make two corrections to dates
gpp.loc[gpp['CURRENT_TARGET_DATE'].astype(str).str.contains('2911|2916|2917|2919'),'CURRENT_TARGET_DATE']=np.nan

    # Rerun check1 and see if if check1 is empty, then convert all datetime columns to datetime
    
check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(gpp,col)],axis = 0,ignore_index=True)

check1.shape # if zero, proceed

    # change certain columns to pandas datetime type

for column in dateColsToChange:
    gpp[column] = pd.to_datetime(gpp[column])

gpp.info()

#----------------------------------Match to ISP Population Dataset on either NOMIS number, Prison Number or Name and 

duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query = """SELECT a.*,                                                         
                   b.NOMIS_ID,
                   b.DOS                        
            FROM gpp AS a INNER JOIN ispTNodup AS b ON 
                  ( (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                    (a.NOMS_ID = B.NOMIS_ID AND a.NOMS_ID IS NOT NULL) 
                  ) AND
                  (a.TARIFF_EXPIRY_DATE = b.TARIFF_EXPIRY_DATE AND a.TARIFF_EXPIRY_DATE IS NOT NULL)"""

gpp2 = duckdb.sql(query).df()
gpp2.shape # 29077

# check bizare reviw dates

gpp2['DOS'].isna().sum() # 0
gpp2['REVIEW_DATE'].isna().sum() # 0

gpp2[gpp2['REVIEW_DATE'].dt.normalize() <= gpp2['DOS'].dt.normalize()][['FILE_REFERENCE','FAMILY_NAME','DOS','REVIEW_DATE','TARIFF_EXPIRY_DATE']].head()

gpp2 = gpp2[gpp2['REVIEW_DATE'].dt.normalize() > gpp2['DOS'].dt.normalize()]
gpp2.shape #29067

gpp2['U_SENT'] = gpp2['TARIFF_EXPIRY_DATE'].astype(str) + gpp2['PRISON_NUMBER'].astype(str)

#---------------------------------- Sort out outcome

gpp2['DECISION'] = gpp2['REVIEW_RESULT_DESCRIPTION']
gpp2['PROPER'] = 1

# gpp2['REVIEW_RESULT_DESCRIPTION'].value_counts(dropna=False)

correct_review_result = ['Compassionate Release',
                        'Future Release',
                        'Nil Discharge',
                        'No Release',
                        'Offender automatically released at 28 days',
                        'Offender released by SofS before 28 days',
                        'Open - Exceptional Circumstances',
                        'Open Conditions - Accepted [*]',
                        'Open Conditions - Rejected [*]',
                        'Oral Hearing - Release',
                        'Paper Decision - Release',
                        'Paper Decision - Release',
                        'Parole Board Forward Release Date',
                        'Parole Board No Recommendation',
                        'Parole Board Release Immediately',
                        'Recommend Release',
                        'Recommendation Accepted (Ministers)',
                        'Recommendation Accepted (PRS)',
                        'Recommendation Rejected',
                        'Release (FTR)',
                        'Release (SofS)',
                        'Release [*]',
                        'Release at CRD (EDS/SOPC)',
                        'Release at SED',
                        'Release on papers (IPP/DPP cases only)',
                        'Return to Open',
                        'Stay In Closed [*]',
                        'Stay In Open [*]']

(~gpp2['DECISION'].isin(correct_review_result)).sum()
gpp2.loc[~(gpp2['DECISION'].isin(correct_review_result)),'DECISION'] = np.nan
gpp2.loc[~(gpp2['DECISION'].isin(correct_review_result)),'PROPER'] = 0

gpp2.loc[gpp2['DECISION'].isna(),'DECISION'] = gpp2['SUBSEQUENT_OUTCOME_DESCRIPTION']

correct_subs_outcome = ['Direct Release',
                        'Release (SO) [**]',
                        'Immediate Release',
                        'Immediate Release (determ. recall ONLY)',
                        'No Direction for Release',
                        'No Hearing (SO) [*]',
                        'No recommendation for open',
                        'Not Granted',
                        'Open Condition (SO) [*]',
                        'Open Conditions',
                        'Recommend Open Conditions',
                        'Recommend Release',
                        'Release (SO) [*]',
                        'Release at a Future Date',
                        'Release at specified date (determ. recall ONLY)',
                        'Remain in Custody (Knockback)(SO) [*]',
                        'Remain in Custody (Knockback) [*]',
                        'No Release']

gpp2.loc[(gpp2['PROPER']==0) & ~(gpp2['DECISION'].isin(correct_subs_outcome)),'DECISION'] = np.nan

correct_status_result =['Open Agreed - Awaiting TX',
                        'Released on Compassionate Grounds',
                        'zzzCompleted - release at CRD']

gpp2.loc[gpp2['DECISION'].isna() & gpp2['REVIEW_STATUS_DESCRIPTION'].isin(correct_status_result),'DECISION'] = gpp2['REVIEW_STATUS_DESCRIPTION']

# gpp2.groupby(['REVIEW_RESULT_DESCRIPTION','SUBSEQUENT_OUTCOME_DESCRIPTION','DECISION']).size().reset_index(name='count')

# gpp2['DECISION'].value_counts(dropna=False)

gpp2.head()

#----------------------------------Simplified results
negatives = ['Stay In Closed [*]',
            'Parole Board No Recommendation',
            'Remain in Custody (Knockback)(SO) [*]',
            'Remain in Custody (Knockback) [*]',
            'Not Granted',
            'No Release',
            'Negative Decision (Paper) [*]',
            'PB No Direction for Release',
            'No Direction for Release',
            'Nil Discharge',
            'No Hearing (SO) [*]',
            'Open Conditions - Rejected [*]',
            'PB No Recommendation for Open',
            'Recommendation Rejected',
            'Stay In Open [*]',
            'Return to Open']

positives =['Release [*]',
            'Release (SO) [*]',
            'Release on papers (IPP/DPP cases only)',
            'Release (SofS)',
            'Parole Board Release Immediately',
            'Parole Board Forward Release Date',
            'Release at SED',
            'Immediate Release',
            'Release at a Future Date',
            'Recommend Release',
            'PB Immediate Release',
            'Release (FTR)',
            'Direct Release',
            'Future Release',
            'Immediate Release (determ. recall ONLY)',
            'Release at specified date (determ. recall ONLY)',
            'Compassionate Release',
            'Offender automatically released at 28 days',
            'PB Release at a Future Date',
            'Release',
            'Release at CRD (EDS/SOPC))',
            'Release (SO) [**]',
            'Release at CRD (EDS/SOPC)',
            'Paper Decision - Release',
            'Oral Hearing - Release',
            'Offender released by SofS before 28 days']

open = ['Open - Exceptional Circumstances',
        'Open Condition (SO) [*]',
        'Open Conditions',
        'Open Conditions - Accepted [*]',
        'Recommendation Accepted (PRS)',
        'Open Agreed - Awaiting TX',
        'PB Recommend Open Conditions',
        'Recommend Open Conditions',
        'Recommendation Accepted (Ministers)']

gpp2['REVIEW_RESULT'] = np.nan
gpp2.loc[gpp2['DECISION'].isin(negatives),'REVIEW_RESULT'] = 'No Release'
gpp2.loc[gpp2['DECISION'].isin(positives),'REVIEW_RESULT'] = 'Release'
gpp2.loc[gpp2['DECISION'].isin(open),'REVIEW_RESULT'] = 'Open'

gpp2['REVIEW_RESULT'].value_counts(dropna=False)

gpp2.shape

#----------------------------------Deduplicate 

gpp2['REVIEW_RESULT'].value_counts(dropna=False)

gpp3 = gpp2[~(gpp2['REVIEW_RESULT'].isna())].copy()

gpp3 = gpp3.drop(['DECISION','PROPER'], axis=1)

gpp3.shape #26290

gpp3.loc[gpp3['SUBSEQUENT_OUTCOME_ACTUAL'].isna(),'SUBSEQUENT_OUTCOME_ACTUAL'] = gpp3['REVIEW_DATE']

gpp3.duplicated(subset=['U_SENT', 'REVIEW_DATE'], keep=False).sum() # 14

# gpp3[gpp3.duplicated(subset=['U_SENT', 'REVIEW_DATE'], keep=False)][['FILE_REFERENCE','U_SENT','SUBSEQUENT_OUTCOME_ACTUAL','FAMILY_NAME','DOS','REVIEW_DATE','TARIFF_EXPIRY_DATE','REVIEW_STATUS_DESCRIPTION','REVIEW_RESULT']].head()

    # select duplicated entry with the least missing values accross

gpp3['numb1'] = gpp3.apply(lambda x: x.astype(str).str.contains('Not Applicable',case=False).sum(), axis=1)
gpp3['numb2'] =gpp3.apply(lambda x: x.astype(str).str.contains('Not specified',case=False).sum(), axis=1)
gpp3['numb3'] = gpp3.apply(lambda x: pd.isna(x).sum(), axis=1)
gpp3['numb'] = gpp3['numb1'] + gpp3['numb2'] + gpp3['numb3']

gpp3 = gpp3.sort_values(['U_SENT','numb'])

gpp3[gpp3.duplicated(subset=['U_SENT', 'REVIEW_DATE'], keep=False)][['FILE_REFERENCE','U_SENT','SUBSEQUENT_OUTCOME_ACTUAL','FAMILY_NAME','numb','DOS','REVIEW_DATE','TARIFF_EXPIRY_DATE','REVIEW_STATUS_DESCRIPTION','REVIEW_RESULT']]

gpp3 = gpp3.drop_duplicates(subset=['U_SENT','REVIEW_DATE'])  # keeps only the first entries with fewer missing data
gpp3 = gpp3.drop(columns=(['numb1','numb2','numb3','numb']))

gpp3.shape # 25760

# ---------------------------------Identify pre, post and recall reviews

on_and_post_tariff = ['Post Tariff',
                      'On Tariff',
                      '01 RECALL',
                      'Pre Tariff',
                      'ZZZ- GPP ON/POST tariff - DO NOT USE',
                      'Lifer Migrated Review',
                      'First Review [*]',
                      'Subsequent Review [*]',
                      'ZZZ- GPP pre tariff - DO NOT USE',
                      'Oral Hearing',
                      'Post tariff consideration for open conditions',
                      'Oral Lifer Recall Hearing',
                      'ZZZ- GPP POST Tariff - DO NOT USE',
                      'Post Tariff - MHT Positive Dec (RC Neg Rec) - MHSP',
                      'On Tariff - MHT Positive Dec (RC Neg Rec) - MHSP']

#gpp2 = gpp2[gpp2['REVIEW_REASON_DESCRIPTION'].isin(on_and_post_tariff)]

gpp3[gpp3['REVIEW_REASON_DESCRIPTION'].astype(str).str.contains('Pre Tariff',case=False)]['REVIEW_REASON_DESCRIPTION'].value_counts()

gpp3.loc[gpp3['REVIEW_REASON_DESCRIPTION'].astype(str).str.contains('Pre Tariff',case=False),'REASON'] = 'Pre Tariff'
gpp3.loc[~(gpp3['REVIEW_REASON_DESCRIPTION'].astype(str).str.contains('Pre Tariff',case=False)),'REASON'] = 'On/Post-Tariff'

gpp3['REASON'].value_counts(dropna=False)

# ---------------------------------Count number of on/post tariff reviews for each offender per tarrif expiry date 

gpp3.shape

gpp3 = gpp3.sort_values(by =['U_SENT','SUBSEQUENT_OUTCOME_ACTUAL'])

gpp3.groupby('U_SENT')
NUM_POST_REVS
gpp3['NUM_POST_REVS'] = gpp3['U_SENT'].map(gpp3[gpp3['REASON']=='On/Post-Tariff'].groupby('U_SENT').size())
gpp3['NUM_POST_REVS'].fillna(0,inplace=True)

gpp3['NUM_PRET_REVS'] = gpp3['U_SENT'].map(gpp3[gpp3['REASON']=='Pre Tariff'].groupby('U_SENT').size())
gpp3['NUM_PRET_REVS'].fillna(0,inplace=True)

gpp3[['U_SENT','FAMILY_NAME','REASON','NUM_PRET_REVS','NUM_POST_REVS']].head(50)

# Keep last review
gpp3 = gpp3.sort_values(['U_SENT','SUBSEQUENT_OUTCOME_ACTUAL'],ascending=[True,False])
gpp4 = gpp3.drop_duplicates('U_SENT')
gpp4.shape

#----------------------------------Match to ISP Population Dataset on either NOMIS number, Prison Number or Name and 

duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query = """SELECT a.*,                                                         
                  b.REVIEW_REASON_DESCRIPTION AS LAST_REVIEW_REASON,
                  b.REASON AS LAST_REVIEW_REASON_2,
                  b.REVIEW_RESULT AS LAST_REVIEW_RESULT, 
                  b.REVIEW_DATE AS LAST_REVIEW_DATE,
                  b.SUBSEQUENT_OUTCOME_DESCRIPTION AS LAST_SUBSEQUENT_OUTCOME, 
                  b.SUBSEQUENT_OUTCOME_ACTUAL AS LAST_SUBSEQUENT_DATE,
                  b.NUM_POST_REVS,
                  b.NUM_PRET_REVS
            FROM ispTNodup AS a LEFT JOIN gpp4 AS b
            ON a.NOMIS_ID = b.NOMIS_ID"""

gppMatched = duckdb.sql(query).df()
gppMatched.shape

gppMatched = gppMatched.sort_values(['NOMIS_ID', 'LAST_SUBSEQUENT_DATE'],ascending=[True,False])
gppMatched = gppMatched.drop_duplicates('NOMIS_ID')
gppMatched.shape # 109340

retain = ['NOMIS_ID', 'PRISON_NUMBER', 'SURNAME', 'FORENAME', 'DATEOFBIRTH', 'DOS', 'TARIFF_EXPIRY_DATE', 'TARIFF_PAST', 'MONTHS_TO_TARIFF_EXPIRY', 'FOUR_YRS_MOST_TO_TED', 'TARIFF', 'ISP_STATUS', 'EXCLUDED_FROM_OPEN', 'PROGRESSION_REGIME', 'OPEN_TYPE', 'CONDITIONS', 'WHOLE_LIFE', 'OFFENCEGROUP', 'OFFENCE', 'PRISONNAME', 'CELLLOCATION', 'PRISONPGDREGION', 'SEC_CAT_LONG', 'IEP', 'F2052_STATUS', 'F2052START', 'AGEBAND', 'ETHNICITY', 'OFFENDER_GENDER', 'NATIONALITYNAME', 'FNPSTATUS', 'LATEST_RELEASE_DATE', 'TARIFF_YEARS', 'SERVED_YEARS', 'OVERTARIFF_MONTHS', 'SENTENCED_AGE', 'LAST_REVIEW_RESULT', 'LAST_REVIEW_REASON', 'LAST_REVIEW_REASON_2', 'LAST_SUBSEQUENT_DATE', 'NUM_POST_REVS', 'EXTRACTDATE', 'AGE', 'TARIFF_MONTHS', 'SERVED_MONTHS', 'OVERTARIFF_YEARS']

gppMatched = gppMatched[retain]

gppMatched.head()
for i in gppMatched.columns:
    print(i)
#---------------------------------- Save
gppMatched.to_parquet(f"s3://alpha-omppg/Eric-Temp/Central Referall/Charlotte/isps.parquet",index=False)
gppMatched.to_excel(f"s3://alpha-omppg/Eric-Temp/Central Referall/Charlotte/isps.xlsx",index=False)

