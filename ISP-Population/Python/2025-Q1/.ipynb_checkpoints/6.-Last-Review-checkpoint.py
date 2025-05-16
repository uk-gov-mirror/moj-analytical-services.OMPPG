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

#---------------------------------- Load GPP data

gpp_ipp = pd.read_excel(f's3://alpha-omppg/isp-population/PPUD/{year}Q{quarter}/PPUD_IPP_GPP_{year}Q{quarter}.xls')
gpp_life = pd.read_excel(f's3://alpha-omppg/isp-population/PPUD/{year}Q{quarter}/PPUD_Life_GPP_{year}Q{quarter}.xls')

gpp = pd.concat([gpp_ipp,gpp_life],ignore_index = True)

gpp.shape # 69588, 68225

gpp = gpp.drop_duplicates()

gpp.shape

strip_blanks(gpp)


    # Convert columns that should be datetime to datetime
gpp.select_dtypes(include=['object']).dtypes

dateColsToChange =['CURRENT_TARGET_DATE']

        # Check wrong dates
    
check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(gpp,col)],axis = 0,ignore_index=True)

check1= check1[dateColsToChange + [col for col in gpp.columns if col not in dateColsToChange]]
check1.shape #6 cases, out of bounds years
check1

# Make two corrections to dates
gpp.loc[gpp['CURRENT_TARGET_DATE'].astype(str).str.contains('2911|2916|2917|2919'),'CURRENT_TARGET_DATE']=pd.NaT

    # Rerun check1 and see if if check1 is empty, then convert all datetime columns to datetime
    
check1 =pd.DataFrame()
for col in dateColsToChange:
    check1 = pd.concat([check1, Out_of_bounds_dates.date_out_of_bounds(gpp,col)],axis = 0,ignore_index=True)

check1.shape # if zero, proceed

    # change certain columns to pandas datetime type

for column in dateColsToChange:
    gpp[column] = pd.to_datetime(gpp[column])

gpp.select_dtypes(include=['datetime64']).dtypes

#----------------------------------Match to ISP Population Dataset on either NOMIS number, Prison Number or Name and 

#duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query8 = """SELECT a.*,                                                         
                   b.NOMIS_ID,
                   b.DOS                        
            FROM gpp AS a INNER JOIN ispLastRel AS b ON 
                  ( (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                    (a.NOMS_ID = B.NOMIS_ID AND a.NOMS_ID IS NOT NULL) 
                  ) AND
                  (a.TARIFF_EXPIRY_DATE = b.TARIFF_EXPIRY_DATE AND a.TARIFF_EXPIRY_DATE IS NOT NULL)"""

gpp2 = duckdb.sql(query8).df()
gpp2.shape # 29427, 29375, 29474, 29421, 29616

# check bizare reviw dates

gpp2['DOS'].isna().sum() # 0
gpp2['REVIEW_DATE'].isna().sum() # 0

gpp2[gpp2['REVIEW_DATE'].dt.date <= gpp2['DOS'].dt.date][['FILE_REFERENCE','FAMILY_NAME','DOS','REVIEW_DATE','TARIFF_EXPIRY_DATE']].head()

gpp2 = gpp2[gpp2['REVIEW_DATE'].dt.date > gpp2['DOS'].dt.date]
gpp2.shape # 29422, 29370,29466,29605

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
                        'Release - IPP on licence',
                        'Oral Hearing – Release',
                        'Release - IPP unconditional (Terminated)',
                        'Return to Open',
                        'Stay In Closed [*]',
                        'Stay In Open [*]']

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
                        'No Release',
                        'IPP re-release on licence [SO]',
                        'Withdrawn by PPCS - Executive Release',
                        'IPP re-release unconditionally [SO]']

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
            'Offender released by SofS before 28 days',
            'Release - IPP on licence',
            'Release - IPP unconditional (Terminated)',
            'Oral Hearing – Release',
            'IPP re-release on licence [SO]',
            'Withdrawn by PPCS - Executive Release',
            'IPP re-release unconditionally [SO]']

open = ['Open - Exceptional Circumstances',
        'Open Condition (SO) [*]',
        'Open Conditions',
        'Open Conditions - Accepted [*]',
        'Recommendation Accepted (PRS)',
        'Open Agreed - Awaiting TX',
        'PB Recommend Open Conditions',
        'Recommend Open Conditions',
        'Recommendation Accepted (Ministers)']

gpp2['REVIEW_RESULT'] = pd.NA
gpp2.loc[gpp2['DECISION'].isin(negatives),'REVIEW_RESULT'] = 'Negative'
gpp2.loc[gpp2['DECISION'].isin(positives),'REVIEW_RESULT'] = 'Release'
gpp2.loc[gpp2['DECISION'].isin(open),'REVIEW_RESULT'] = 'Open'

gpp2['REVIEW_RESULT'].value_counts(dropna=False)
gpp2[gpp2['REVIEW_RESULT'].isna()]['REVIEW_RESULT_DESCRIPTION'].value_counts(dropna=False)
gpp2[gpp2['REVIEW_RESULT'].isna()]['SUBSEQUENT_OUTCOME_DESCRIPTION'].value_counts(dropna=False)
gpp2.shape

#----------------------------------Deduplicate 

gpp2['REVIEW_RESULT'].value_counts(dropna=False)

gpp3 = gpp2[~(gpp2['REVIEW_RESULT'].isna())].copy()

gpp3 = gpp3.drop(['DECISION','PROPER'], axis=1)

gpp3.shape # 26417, 29370, 26376,26290

gpp3.loc[gpp3['SUBSEQUENT_OUTCOME_ACTUAL'].isna(),'SUBSEQUENT_OUTCOME_ACTUAL'] = gpp3['REVIEW_DATE']

gpp3.duplicated(subset=['U_SENT', 'REVIEW_DATE'], keep=False).sum() # 10

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

gpp3.shape # 26412,29352,26370, 26281

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

gpp3.loc[gpp3['REVIEW_REASON_DESCRIPTION'].astype(str).str.contains('Pre Tariff',case=False),'REVIEW_REASON_DESCRIPTION'] = 'Pre Tariff'

gpp3[gpp3['REVIEW_REASON_DESCRIPTION'].astype(str).str.contains('Recall',case=False)]['REVIEW_REASON_DESCRIPTION'].value_counts()

gpp3.loc[gpp3['REVIEW_REASON_DESCRIPTION'].astype(str).str.contains('Recall',case=False),'REVIEW_REASON_DESCRIPTION'] = 'Recall'

gpp3[~gpp3['REVIEW_REASON_DESCRIPTION'].isin(['Pre Tariff','Recall'])]['REVIEW_REASON_DESCRIPTION'].value_counts()

gpp3.loc[~gpp3['REVIEW_REASON_DESCRIPTION'].isin(['Pre Tariff','Recall']),'REVIEW_REASON_DESCRIPTION'] = 'On/Post Tariff'

gpp3.groupby(['REVIEW_REASON_DESCRIPTION','REVIEW_STATUS_DESCRIPTION']).size().reset_index(name='count')

# ---------------------------------Count number of on/post tariff reviews for each offender per tarrif expiry date 

gpp3.shape

gpp3 = gpp3.sort_values(by =['U_SENT','SUBSEQUENT_OUTCOME_ACTUAL'])

gpp3['REVIEWNUM'] = gpp3['U_SENT'].map(gpp3[gpp3['REVIEW_REASON_DESCRIPTION']=='On/Post Tariff'].groupby('U_SENT').size())
gpp3.fillna({'REVIEWNUM':0},inplace=True)

gpp3.head()
gpp3['OPEN_REVIEWNUM'] = gpp3['U_SENT'].map(gpp3[gpp3['REVIEW_RESULT']=='Open'].groupby('U_SENT').size())
gpp3.fillna({'OPEN_REVIEWNUM':0},inplace=True)

#gpp3[['FILE_REFERENCE','FAMILY_NAME','REVIEWNUM','OPEN_REVIEWNUM','U_SENT','REVIEW_REASON_DESCRIPTION','REVIEW_TYPE_DESCRIPTION','REVIEW_RESULT','SUBSEQUENT_OUTCOME_ACTUAL','DOS','REVIEW_DATE','TARIFF_EXPIRY_DATE','REVIEW_STATUS_DESCRIPTION']].head(15)

#--------------------------------------*Keep only valid outcomes and score them

gpp3['REVIEW_PROGRESS'] = 0
gpp3.loc[gpp3['REVIEW_RESULT'] == 'Release','REVIEW_PROGRESS'] = 2
gpp3.loc[(gpp3['REVIEW_RESULT'] == 'Open') | (gpp3['REVIEW_RESULT_DESCRIPTION'] == 'Stay In Open [*]'),'REVIEW_PROGRESS'] = 1

gpp3['MAX_PROGRESS'] = gpp3.groupby('U_SENT')['REVIEW_PROGRESS'].transform('max')

gpp3['PROGRESS_DATE'] = gpp3['U_SENT'].map(gpp3[gpp3['REVIEW_PROGRESS']==gpp3['MAX_PROGRESS']].groupby('U_SENT')['SUBSEQUENT_OUTCOME_ACTUAL'].max())

#gpp3[['FILE_REFERENCE','FAMILY_NAME','REVIEW_PROGRESS','MAX_PROGRESS','REVIEW_RESULT','PROGRESS_DATE','SUBSEQUENT_OUTCOME_ACTUAL','U_SENT','REVIEW_REASON_DESCRIPTION','REVIEW_TYPE_DESCRIPTION','REVIEW_DATE','TARIFF_EXPIRY_DATE']].head(40)

    # Add open progress date against each review*/

gpp3['LAST_OPEN_DATE'] = gpp3['U_SENT'].map(gpp3[gpp3['REVIEW_RESULT']=='Open'].groupby('U_SENT')['SUBSEQUENT_OUTCOME_ACTUAL'].max())


#----------------------------------Match to ISP Population Dataset on either NOMIS number, Prison Number or Name and 

#duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query9 = """SELECT DISTINCT a.*,                                                         
                            b.REVIEW_REASON_DESCRIPTION AS LAST_REVIEW_REASON,
                            b.REVIEW_RESULT AS LAST_REVIEW_RESULT, 
                            b.REVIEW_DATE AS LAST_REVIEW_DATE,
                            b.SUBSEQUENT_OUTCOME_DESCRIPTION AS LAST_SUBSEQUENT_OUTCOME, 
                            b.SUBSEQUENT_OUTCOME_ACTUAL AS LAST_SUBSEQUENT_DATE,
                            b.REVIEWNUM AS LAST_REVIEWNUM, 
                            b.MAX_PROGRESS, 
                            b.PROGRESS_DATE, 
                            b.OPEN_REVIEWNUM, 
                            b.LAST_OPEN_DATE
            FROM ispLastRec AS a LEFT JOIN gpp3 AS b
            ON b.SUBSEQUENT_OUTCOME_ACTUAL < a.EXTRACTDATE AND 
                (b.REVIEW_REASON_DESCRIPTION = 'On Tariff' OR
                 b.REVIEW_REASON_DESCRIPTION = 'On/Post Tariff' OR
                 b.REVIEW_DATE > a.TARIFF_EXPIRY_DATE
                ) AND
                (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) AND
                (a.TARIFF_EXPIRY_DATE = b.TARIFF_EXPIRY_DATE)"""

gppMatched = duckdb.sql(query9).df()
gppMatched.shape # 31285, 33797

    # deduplicate by latest review date
gppMatched = gppMatched.sort_values(by=['LAST_SUBSEQUENT_DATE'],ascending = False)

ispLastRev =gppMatched.drop_duplicates(subset='NOMIS_ID', keep ='first').copy()
ispLastRev.shape # 10899, 10902, 10939, 10961

#----------------------------------Add final variables

ispLastRev.loc[ispLastRev['MAX_PROGRESS'] == 0,'PREVIOUS_PROGRESS'] ='None'
ispLastRev.loc[ispLastRev['MAX_PROGRESS'] == 1,'PREVIOUS_PROGRESS'] = 'Open'
ispLastRev.loc[ispLastRev['MAX_PROGRESS'] == 2,'PREVIOUS_PROGRESS'] = 'Release'

ispLastRev.shape

ispLastRev.head()
#---------------------------------- Save
ispLastRev.to_parquet(f"s3://alpha-omppg/isp-population/final/isp_pop_{year}q{quarter}.parquet",index=False)
