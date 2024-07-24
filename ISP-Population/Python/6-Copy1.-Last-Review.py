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
        
#----------------------------------Set globals

yy = 23 # year as yy
mm = 12
dd = 31

year = 2023
quarter = 4 

#---------------------------------- Load GPP data

gpp = pd.read_excel(f's3://alpha-omppg/ISP Population/PPUD/{year}Q{quarter}/PPUD_ALLGPP_{year}Q{quarter}.xls')

gpp.shape
gpp = gpp.drop_duplicates()

gpp.info()

# strip_blanks(gpp)


    # Convert columns that should be datetime to datetime

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

query4 = """SELECT a.*,                                                         
                   b.NOMIS_ID,
                   b.DOS                        
            FROM gpp AS a INNER JOIN ispLastRel AS b ON 
                  ( (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                    (a.NOMS_ID = B.NOMIS_ID AND a.NOMS_ID IS NOT NULL) 
                  ) AND
                  (a.TARIFF_EXPIRY_DATE = b.TARIFF_EXPIRY_DATE AND a.TARIFF_EXPIRY_DATE IS NOT NULL)"""

gpp2 = duckdb.sql(query4).df()
gpp2.shape # 29584

# check bizare reviw dates

gpp2['DOS'].isna().sum() # 0
gpp2['REVIEW_DATE'].isna().sum() # 0

gpp2[gpp2['REVIEW_DATE'].dt.date <= gpp2['DOS'].dt.date][['FILE_REFERENCE','FAMILY_NAME','DOS','REVIEW_DATE','TARIFF_EXPIRY_DATE']].head()

gpp2 = gpp2[gpp2['REVIEW_DATE'].dt.date > gpp2['DOS'].dt.date]
gpp2.shape #29573

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
gpp2.loc[gpp2['DECISION'].isin(negatives),'REVIEW_RESULT'] = 'Negative'
gpp2.loc[gpp2['DECISION'].isin(positives),'REVIEW_RESULT'] = 'Release'
gpp2.loc[gpp2['DECISION'].isin(open),'REVIEW_RESULT'] = 'Open'

gpp2['REVIEW_RESULT'].value_counts(dropna=False)

gpp2.shape

#----------------------------------Deduplicate 

gpp2[gpp2['REVIEW_RESULT'].isna()]['DECISION'].value_counts(dropna=False)

gpp3 = gpp2[~(gpp2['REVIEW_RESULT'].isna())].copy()

gpp3 = gpp3.drop(['DECISION','PROPER'], axis=1)

gpp3.shape #26207

gpp3.duplicated(subset=['U_SENT', 'REVIEW_DATE'], keep=False).sum() # 18

gpp3[gpp3.duplicated(subset=['U_SENT', 'REVIEW_DATE'], keep=False)][['FILE_REFERENCE','U_SENT','SUBSEQUENT_OUTCOME_ACTUAL','FAMILY_NAME','DOS','REVIEW_DATE','TARIFF_EXPIRY_DATE','REVIEW_STATUS_DESCRIPTION','REVIEW_RESULT']].head()

    # select duplicated entry with the least missing values accross

gpp3['numb1'] = gpp3.apply(lambda x: x.astype(str).str.contains('Not Applicable',case=False).sum(), axis=1)
gpp3['numb2'] =gpp3.apply(lambda x: x.astype(str).str.contains('Not specified',case=False).sum(), axis=1)
gpp3['numb3'] = gpp3.apply(lambda x: pd.isna(x).sum(), axis=1)
gpp3['numb'] = gpp3['numb1'] + gpp3['numb2'] + gpp3['numb3']

gpp3 = gpp3.sort_values(['U_SENT','numb'])

gpp3[gpp3.duplicated(subset=['U_SENT', 'REVIEW_DATE'], keep=False)][['FILE_REFERENCE','U_SENT','SUBSEQUENT_OUTCOME_ACTUAL','FAMILY_NAME','numb','DOS','REVIEW_DATE','TARIFF_EXPIRY_DATE','REVIEW_STATUS_DESCRIPTION','REVIEW_RESULT']]

gpp3 = gpp3.drop_duplicates(subset=['U_SENT','REVIEW_DATE'])  # keeps only the first entries with fewer missing data
gpp3 = gpp3.drop(columns=(['numb1','numb2','numb3','numb']))

gpp3.shape # 261918

# ---------------------------------Identify pre, post and recall reviews

# on_and_post_tariff = ['Post Tariff',
                      #'On Tariff',
                      #'01 RECALL',
                      #'Pre Tariff',
                      #'ZZZ- GPP ON/POST tariff - DO NOT USE',
                      #'Lifer Migrated Review',
                      #'First Review [*]',
                      #'Subsequent Review [*]',
                      #'ZZZ- GPP pre tariff - DO NOT USE',
                      #'Oral Hearing',
                      #'Post tariff consideration for open conditions',
                      #'Oral Lifer Recall Hearing',
                      #'ZZZ- GPP POST Tariff - DO NOT USE',
                     #'Post Tariff - MHT Positive Dec (RC Neg Rec) - MHSP',
                     #'On Tariff - MHT Positive Dec (RC Neg Rec) - MHSP']

#gpp2 = gpp2[gpp2['REVIEW_REASON_DESCRIPTION'].isin(on_and_post_tariff)]

gpp3[gpp3['REVIEW_REASON_DESCRIPTION'].astype(str).str.contains('Pre Tariff',case=False)]['REVIEW_REASON_DESCRIPTION'].value_counts()

gpp3.loc[gpp3['REVIEW_REASON_DESCRIPTION'].astype(str).str.contains('Pre Tariff',case=False),'REVIEW_REASON_DESCRIPTION'] = 'Pre Tariff'

gpp3[gpp3['REVIEW_REASON_DESCRIPTION'].astype(str).str.contains('Recall',case=False)]['REVIEW_REASON_DESCRIPTION'].value_counts()

gpp3.loc[gpp3['REVIEW_REASON_DESCRIPTION'].astype(str).str.contains('Recall',case=False),'REVIEW_REASON_DESCRIPTION'] = 'Recall'

gpp3.loc[~gpp3['REVIEW_REASON_DESCRIPTION'].isin(['Pre Tariff','Recall']),'REVIEW_REASON_DESCRIPTION'] = 'On/Post Tariff'

gpp3.groupby(['REVIEW_REASON_DESCRIPTION','REVIEW_STATUS_DESCRIPTION']).size().reset_index(name='count')

# ---------------------------------Count number of on/post tariff reviews for each offender per tarrif expiry date 

gpp3 = gpp3.sort_values(by =['U_SENT','REVIEW_DATE'])

gpp3['REVIEWNUM'] = gpp3[gpp3['REVIEW_REASON_DESCRIPTION']=='On/Post Tariff'].groupby('U_SENT')['U_SENT'].transform('count')

#gpp3[['FILE_REFERENCE','REVIEWNUM','U_SENT','REVIEW_REASON_DESCRIPTION','SUBSEQUENT_OUTCOME_ACTUAL','FAMILY_NAME','DOS','REVIEW_DATE','TARIFF_EXPIRY_DATE','REVIEW_STATUS_DESCRIPTION','REVIEW_RESULT']].head(15)

gpp3['OPEN_REVIEWNUM'] = gpp3[gpp3['REVIEW_RESULT']=='Open'].groupby('U_SENT')['U_SENT'].transform('count')

#gpp3[['FILE_REFERENCE','REVIEWNUM','U_SENT','REVIEW_REASON_DESCRIPTION','SUBSEQUENT_OUTCOME_ACTUAL','FAMILY_NAME','DOS','REVIEW_DATE','TARIFF_EXPIRY_DATE','REVIEW_STATUS_DESCRIPTION','REVIEW_RESULT']].head(15)

#--------------------------------------*Keep only valid outcomes and score them

gpp3['REVIEW_PROGRESS'] = 0

gpp3.loc[gpp3['REVIEW_RESULT'] == 'Release','REVIEW_PROGRESS'] = 2
gpp3.loc[(gpp3['REVIEW_RESULT'] == 'Open') | (gpp3['REVIEW_RESULT_DESCRIPTION'] == 'Stay In Open [*]'),'REVIEW_PROGRESS'] = 1

gpp3['MAX_PROGRESS'] = gpp3.groupby('U_SENT')['REVIEW_PROGRESS'].transform('max')


gpp3[gpp3['REVIEW_REASON_DESCRIPTION']=='On/Post Tariff'].groupby('U_SENT')['U_SENT'].transform('count')





gpp3.loc[gpp3['REVIEW_REASON_DESCRIPTION'].isin(['First Review [*]','On Tariff - MHT Positive Dec (RC Neg Rec) - MHSP']),'REVIEW_REASON_DESCRIPTION'] = 'On Tariff'

pos_tariff = ['Subsequent Review [*]',
              'ZZZ- GPP POST Tariff - DO NOT USE',
              'Post tariff consideration for open conditions',
              'Oral Hearing',
              'Lifer Migrated Review',
              'ZZZ- GPP ON/POST tariff - DO NOT USE',
              'Post Tariff - MHT Positive Dec (RC Neg Rec) - MHSP']

gpp.loc[gpp['REVIEW_REASON_DESCRIPTION'].isin(pos_tariff),'REVIEW_REASON_DESCRIPTION'] = 'Post Tariff'

recall_rev = ['01 RECALL','Oral Lifer Recall Hearing']
gpp.loc[gpp['REVIEW_REASON_DESCRIPTION'].isin(recall_rev),'REVIEW_REASON_DESCRIPTION'] = 'Recall'

gpp.loc[gpp['REVIEW_REASON_DESCRIPTION'] =='ZZZ- GPP pre tariff - DO NOT USE','REVIEW_REASON_DESCRIPTION'] = 'Pre Tariff'
gpp.loc[gpp['REVIEW_TYPE_DESCRIPTION'].isin(['PB - Pre-TED [*]','GPP ISP Pre Tariff']),'REVIEW_REASON_DESCRIPTION'] = 'Pre Tariff'

gpp.loc[gpp['SUBSEQUENT_OUTCOME_ACTUAL'].isna(),'SUBSEQUENT_OUTCOME_ACTUAL'] = gpp['REVIEW_DATE']

gpp['REVIEW_REASON_DESCRIPTION'].value_counts(dropna=False)

gpp.shape


# rec2[['FILE_REFERENCE','numb']].head(20)


#----------------------------------Match to ISP Population Dataset on either NOMIS number, Prison Number or Name and 

duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query3 = """SELECT DISTINCT a.*,                                                         
                            b.LICENCE_REVOKE_DATE AS LAST_LICENCE_REVOKE_DATE, 
                            b.RTC_DATE AS LAST_RTC_DATE,
                            b.RECALLNUM AS LAST_RECALLNUM,
                            b.NUMBER_OF_RECALL_REASONS AS LAST_RECALL_NUMBER_OF_REASONS, 
                            b.RECALL_REASON_DESCRIPTIONS AS LAST_RECALL_REASONS,
                            b.PROBATION_AREA_DESCRIPTION AS LAST_RECALL_AREA,
                            b.FURTHER_CHARGE AS LAST_RECALL_FURTHER_CHARGE,
                            b.PRISON_NUMBER AS PN2, 
                            b.PN_TRIM, 
                            b.PN_START, 
                            b.PN_END, 
                            b.NOMS_ID AS NOMS_ID_PPUD, 
                            b.NOMS_TRIM, 
                            b.NOMS_START, 
                            b.NOMS_END,
                            b.FAMILY_NAME AS SURNAME_PPUD, 
                            b.INIT AS INIT_PPUD, 
                            b.DOB AS DOB_PPUD
                        
            FROM ispLastRel AS a LEFT JOIN isp_recalls AS b ON 
                        (a.EXTRACTDATE >= b.DOS OR b.DOS IS NULL) AND
                        a.EXTRACTDATE >= b.RTC_DATE AND
                        (a.TARIFF_EXPIRY_DATE <= b.RTC_DATE OR a.TARIFF_EXPIRY_DATE IS NULL) AND
                        (a.LAST_RELEASE_DATE <= b.RTC_DATE OR a.LAST_RELEASE_DATE IS NULL) AND
                        (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)"""

ispRecMatched = duckdb.sql(query3).df()
ispRecMatched.shape

#---------------------------------- Rate quality of the match
def calculate_match(row):
    
    condition_a = pd.notna(row['NOMIS_ID']) and (
        row['NOMIS_ID'] in [row['NOMS_ID_PPUD'], row['NOMS_TRIM'], row['NOMS_START'], row['NOMS_END']]
    )
    
    condition_b = pd.notna(row['NOMIS_ID']) and (
        row['NOMIS_ID'] in [row['PRISON_NUMBER'], row['PN_START'], row['PN_END'], row['PN_TRIM']]
    )
    condition_c = (
        pd.notna(row['SURNAME']) and row['SURNAME'] == row['SURNAME_PPUD'] and
        pd.notna(row['DATEOFBIRTH']) and row['DATEOFBIRTH'] == row['DOB_PPUD'] and
        pd.notna(row['INITIAL']) and row['INITIAL'] == row['INIT_PPUD']
    )
    
    if condition_a and condition_c:
        return 4
    elif (condition_a or condition_b) and condition_c:
        return 3
    elif (condition_a or condition_b):
        return 2
    elif condition_c:
        return 1
    else:
        return 0

    # Create Match column by applying the function to each row
ispRecMatched['MATCH'] =ispRecMatched.apply(calculate_match, axis=1)


    # deduplicate
ispRecMatched = ispRecMatched.sort_values(by=['MATCH','LAST_RTC_DATE'],ascending = [False,False])

ispLastRec =ispRecMatched.drop_duplicates(subset='NOMIS_ID', keep ='first').copy()
ispLastRec.shape

#----------------------------------Add final variables

    # Only keep ISPs and any recalls with a match to an ISP on PPUD
    
cust_type_to_keep = ( (ispLastRec['SENTENCESTATUS'].isin(['(5) IPP','(6) Life'])) | 
                      (~ispLastRec['CUSTODY_TYPE_DESCRIPTION'].isna()) | 
                      (~ispLastRec['TARIFF_EXPIRY_DATE'].isna())
                )

ispLastRec = ispLastRec[cust_type_to_keep]
ispLastRec.shape

    # Classify ISPs based on NOMIS sentence status, adding sentence information to recalls from PPUD
        
nomis_recall_cond = (ispLastRec['SENTENCESTATUS'] == '(7) Recall')
missing_cus_type = ispLastRec['CUSTODY_TYPE_DESCRIPTION'].isna()
ipp_cus_type = ispLastRec['CUSTODY_TYPE_DESCRIPTION'].isin(['IPP','DPP'])

ispLastRec['ISP_STATUS'] = np.nan
ispLastRec.loc[nomis_recall_cond & missing_cus_type,'ISP_STATUS'] = 'Recalled ISP (unknown sentence)'
ispLastRec.loc[nomis_recall_cond & ipp_cus_type,'ISP_STATUS'] = 'Recalled IPP'
ispLastRec.loc[nomis_recall_cond & ~(missing_cus_type) & ~(ipp_cus_type),'ISP_STATUS'] = 'Recalled Life'

ispLastRec.loc[ispLastRec['SENTENCESTATUS'] == '(5) IPP','ISP_STATUS'] = 'Unreleased IPP'
ispLastRec.loc[ispLastRec['SENTENCESTATUS'] == '(6) Life','ISP_STATUS'] = 'Unreleased Life'

ispLastRec['ISP_STATUS'].value_counts(dropna=False) # matches

    # Classify ISPs based on PPUD sentence and recall information*
        
ppud_status_cond1 = (ispLastRec['LAST_LICENCE_REVOKE_DATE'].dt.date < ispLastRec['EXTRACTDATE'].dt.date) & \
                 (~ispLastRec['LAST_LICENCE_REVOKE_DATE'].isna())
ppud_status_cond2 = (ispLastRec['FIRST_RELEASE_DATE'].dt.date < ispLastRec['EXTRACTDATE'].dt.date) & \
                 (~ispLastRec['FIRST_RELEASE_DATE'].isna())
ppud_status_cond3 = (ispLastRec['LAST_RELEASE_DATE'].dt.date < ispLastRec['EXTRACTDATE'].dt.date) & \
                 (~ispLastRec['LAST_RELEASE_DATE'].isna())
tariff_past_or_missing = (ispLastRec['TARIFF_PAST'] == 'Y') | (ispLastRec['TARIFF_PAST'].isna())

ppud_status_cond = (ppud_status_cond1 | ppud_status_cond2 | ppud_status_cond3 | nomis_recall_cond) & \
                   tariff_past_or_missing

ispLastRec['PPUD_STATUS'] = np.nan
ispLastRec.loc[ppud_status_cond & missing_cus_type,'PPUD_STATUS'] = 'Recalled ISP (unknown sentence)'
ispLastRec.loc[ppud_status_cond & ipp_cus_type,'PPUD_STATUS'] = 'Recalled IPP'
ispLastRec.loc[ppud_status_cond & ~(missing_cus_type) & ~(ipp_cus_type),'PPUD_STATUS'] = 'Recalled Life'

ispLastRec.loc[~(ppud_status_cond) & missing_cus_type,'PPUD_STATUS'] = ispLastRec['ISP_STATUS']
ispLastRec.loc[~(ppud_status_cond) & ipp_cus_type,'PPUD_STATUS'] = 'Unreleased IPP'
ispLastRec.loc[~(ppud_status_cond) & ~(missing_cus_type) & ~(ipp_cus_type),'PPUD_STATUS'] = 'Unreleased Life'

ispLastRec['PPUD_STATUS'].value_counts(dropna=False) # close to ISP_STATUS

    # Time spent in custody since recall
ispLastRec['DAYS_RECALLED'] = ispLastRec['EXTRACTDATE'].dt.date - ispLastRec['LAST_RTC_DATE'].dt.date
ispLastRec['MONTHS_RECALLED'] = ispLastRec.apply(lambda x: TimeDiffs.month_diff(x['LAST_RTC_DATE'],x['EXTRACTDATE']),axis=1)

    #custody_stage: shows if ISP is pre-tariff, post-tariff or recalled
    # isp_type: shows if ISP is Life or IPP for all, including recalls
    
ispLastRec['CUSTODY_STAGE'] = 'Unknown tariff'
ispLastRec.loc[nomis_recall_cond,'CUSTODY_STAGE'] = 'Recall'
ispLastRec.loc[~(nomis_recall_cond) & (ispLastRec['TARIFF_PAST'] == 'N'),'CUSTODY_STAGE'] = 'Pre-tariff'
ispLastRec.loc[~(nomis_recall_cond) & (ispLastRec['TARIFF_PAST'] == 'Y'),'CUSTODY_STAGE'] = 'Post-tariff'

ispLastRec['ISP_TYPE'] = np.nan
ispLastRec.loc[nomis_recall_cond & (ispLastRec['ISP_STATUS'] == 'Recalled IPP'),'ISP_TYPE'] = 'IPP'
ispLastRec.loc[nomis_recall_cond & (ispLastRec['ISP_STATUS'] == 'Recalled Life'),'ISP_TYPE'] = 'Life'
ispLastRec.loc[~(nomis_recall_cond) & (ispLastRec['SENTENCESTATUS'].str.contains('IPP',case=False)),'ISP_TYPE'] = 'IPP'
ispLastRec.loc[~(nomis_recall_cond) & (ispLastRec['SENTENCESTATUS'].str.contains('Life',case=False)),'ISP_TYPE'] = 'Life'

#---------------------------------- drop some variables

ispLastRec = ispLastRec.drop(['MATCH', 'SURNAME_PPUD', 'DOB_PPUD', 'INIT_PPUD', 'PN2', 'PN_TRIM','PN_START','PN_END', 'NOMS_ID_PPUD', 'NOMS_TRIM', 'NOMS_START', 'NOMS_END'],axis=1)

ispLastRec.shape

#---------------------------------- Save
ispLasttRel.to_parquet("ispLasttRel.parquet")
