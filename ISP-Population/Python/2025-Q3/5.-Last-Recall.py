""" 
GOAL: ADD LAST RECALL INFORMATION FOR QUARTERLY ISP POP FOR OMSQ
By Eric Nyame, 05/02/2024
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

#----------------------------------Match to ISP Population Dataset on either NOMIS number, Prison Number or Name and 

isp_recalls_final = pd.read_parquet(f"s3://alpha-omppg/Recalls/final_data/recalls/isp/isp_recalls_{year}q{quarter}.parquet")

# duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query7 = """SELECT DISTINCT a.*,                                                         
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
                        
            FROM ispLastRel AS a LEFT JOIN isp_recalls_final AS b ON 
                        (a.EXTRACTDATE >= b.DOS OR b.DOS IS NULL) AND
                        a.EXTRACTDATE >= b.RTC_DATE AND
                        (a.TARIFF_EXPIRY_DATE <= b.RTC_DATE OR a.TARIFF_EXPIRY_DATE IS NULL) AND
                        (a.LAST_RELEASE_DATE <= b.RTC_DATE OR a.LAST_RELEASE_DATE IS NULL) AND
                        (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)"""

ispRecMatched = duckdb.sql(query7).df()
ispRecMatched.shape # 10887, 10903, 10908, 10949

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
ispLastRec.shape # 10899, 10939

#----------------------------------Add final variables

    # Only keep ISPs and any recalls with a match to an ISP on PPUD
    
cust_type_to_keep = ( (ispLastRec['SENTENCESTATUS'].isin(['(5) IPP','(6) Life'])) | 
                      (~ispLastRec['CUSTODY_TYPE_DESCRIPTION'].isna()) | 
                      (~ispLastRec['TARIFF_EXPIRY_DATE'].isna())
                )

ispLastRec = ispLastRec[cust_type_to_keep]
ispLastRec.shape #10881, 10961

    # Classify ISPs based on NOMIS sentence status, adding sentence information to recalls from PPUD
        
nomis_recall_cond = (ispLastRec['SENTENCESTATUS'] == '(7) Recall')
missing_cus_type = ispLastRec['CUSTODY_TYPE_DESCRIPTION'].isna()
ipp_cus_type = ispLastRec['CUSTODY_TYPE_DESCRIPTION'].isin(['IPP','DPP'])

ispLastRec['ISP_STATUS'] = ''
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

ispLastRec['PPUD_STATUS'] = ''
ispLastRec.loc[ppud_status_cond & missing_cus_type,'PPUD_STATUS'] = 'Recalled ISP (unknown sentence)'
ispLastRec.loc[ppud_status_cond & ipp_cus_type,'PPUD_STATUS'] = 'Recalled IPP'
ispLastRec.loc[ppud_status_cond & ~(missing_cus_type) & ~(ipp_cus_type),'PPUD_STATUS'] = 'Recalled Life'

ispLastRec.loc[~(ppud_status_cond) & missing_cus_type,'PPUD_STATUS'] = ispLastRec['ISP_STATUS']
ispLastRec.loc[~(ppud_status_cond) & ipp_cus_type,'PPUD_STATUS'] = 'Unreleased IPP'
ispLastRec.loc[~(ppud_status_cond) & ~(missing_cus_type) & ~(ipp_cus_type),'PPUD_STATUS'] = 'Unreleased Life'

ispLastRec['PPUD_STATUS'].value_counts(dropna=False) # close to ISP_STATUS
ispLastRec['ISP_STATUS'].value_counts(dropna=False) # close to ISP_STATUS

    # Time spent in custody since recall
ispLastRec.head()
ispLastRec.info()

ispLastRec['DAYS_RECALLED'] = (ispLastRec['EXTRACTDATE'].dt.date - ispLastRec['LAST_RTC_DATE'].dt.normalize().dt.date)
ispLastRec.head()

ispLastRec['MONTHS_RECALLED'] = ispLastRec.apply(lambda x: TimeDiffs.month_diff(x['LAST_RTC_DATE'],x['EXTRACTDATE']),axis=1)

    #custody_stage: shows if ISP is pre-tariff, post-tariff or recalled
    # isp_type: shows if ISP is Life or IPP for all, including recalls
    
ispLastRec['CUSTODY_STAGE'] = 'Unknown tariff'
ispLastRec.loc[nomis_recall_cond,'CUSTODY_STAGE'] = 'Recall'
ispLastRec.loc[~(nomis_recall_cond) & (ispLastRec['TARIFF_PAST'] == 'N'),'CUSTODY_STAGE'] = 'Pre-tariff'
ispLastRec.loc[~(nomis_recall_cond) & (ispLastRec['TARIFF_PAST'] == 'Y'),'CUSTODY_STAGE'] = 'Post-tariff'

ispLastRec['ISP_TYPE'] = ''
ispLastRec.loc[nomis_recall_cond & (ispLastRec['ISP_STATUS'] == 'Recalled IPP'),'ISP_TYPE'] = 'IPP'
ispLastRec.loc[nomis_recall_cond & (ispLastRec['ISP_STATUS'] == 'Recalled Life'),'ISP_TYPE'] = 'Life'
ispLastRec.loc[~(nomis_recall_cond) & (ispLastRec['SENTENCESTATUS'].str.contains('IPP',case=False)),'ISP_TYPE'] = 'IPP'
ispLastRec.loc[~(nomis_recall_cond) & (ispLastRec['SENTENCESTATUS'].str.contains('Life',case=False)),'ISP_TYPE'] = 'Life'

#---------------------------------- drop some variables

ispLastRec = ispLastRec.drop(['MATCH', 'SURNAME_PPUD', 'DOB_PPUD', 'INIT_PPUD', 'PN2', 'PN_TRIM','PN_START','PN_END', 'NOMS_ID_PPUD', 'NOMS_TRIM', 'NOMS_START', 'NOMS_END'],axis=1)

ispLastRec.shape # 10899, 10902, 10939
ispLastRec.head()
#---------------------------------- Save
ispLastRec.to_parquet("ispLastRec.parquet")
