""" 
GOAL: PRODUCE RESTRICTED PATIENTS STATISTICS FOR PUBLICATION
By Eric Nyame, 29/02/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib

import re

from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
# from my_log import my_log
import Out_of_bounds_dates
importlib.reload(Out_of_bounds_dates)
import prepareMatch
importlib.reload(prepareMatch)
import openMatch
importlib.reload(openMatch)
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

#************* MAIN ADMISSION CATEGORIES**********************************
"""
s45A/s45B = HOSPTAL DIRECTIONS. Court convicts but directs to hospital. 
       Prison sentence to be served after successful treatment in hospital.
    
s37/s41 = HOSPITAL ORDER with RESTRICTIONS added. 
          Issued by the court. Patient could be unfit or not guilty by insanity.
          Not guilty by isanity does not mean they didn't commit the offence?


s47/s49 =  TRANSFER OF CONVICTED PRISONERS with RESTRICTIONS added
           Secretary of State transfers a CONVICTED prisoner from prison to hospital. 

s48/s49 = TRANSFER OF UNCONVICTED PRISONERS with RESTRICTIONS added.
          Secretary of State transfers an UNSENTENCED prisoner from prison to hospital. 
          This could include remand, immigration detainees, unsentenced prisoners, civil prisoners.
"""
#*********************************************************************

#----------------------------------Set globals

year = 2023
snapshotDate = pd.Timestamp(2023,12,31)

#--------------- Load population dataset

pop = pd.read_excel(f"s3://alpha-omppg/Mental Health/{year}/Raw Data/population__4March.xls")
pop = pop.replace("–","-")

pop.info()

moves = pd.read_excel(f"s3://alpha-omppg/Mental Health/{year}/Raw Data/All_Moves_12Dec2023_4March.xls")
moves = moves.replace("–","-")
moves.info()
moves.head(10)
len(moves) # 680

    # keep Only cases with non missing actual date after 31 Dec
moves = moves[moves['ACTUAL_DATE'] >= pd.Timestamp(2023,12,31)]
len(moves) #502

    # rearrange columns
movesCol =['FILE_REFERENCE','FAMILY_NAME','ACTUAL_DATE','AUTHORISATION_DATE','MOVE_TYPE_DESCRIPTION','MOVE_SUB_TYPE_DESCRIPTION',
           'FROM_ESTABLISHMENT_DESCRIPTION','TO_ESTABLISHMENT_DESCRIPTION','AUTHORITY_FOR_DETENTION_DESCRIPTION','CURRENT_ESTABLISHMENT_DESCRIPTION',
           'CUSTODY_TYPE_DESCRIPTION','DOB','ETHNICITY_DESCRIPTION','FIRST_NAMES','GENDER','MENTAL_DISORDER_DESCRIPTION',
           'MOVE_SUB_SUB_TYPE_DESCRIPTION','NATIONALITY_DESCRIPTION','NOMS_ID','STATUS_DESCRIPTION','PRISON_NUMBER']

moves = moves[movesCol]

    # Custom priority entries to sort move types if there are multiple moves for an individual on the same Actual_Date
priority_move =['Abscond','Escape','Disposal By Court','Admission'] + list(set(moves['MOVE_SUB_TYPE_DESCRIPTION']) - set(['Abscond','Escape','Disposal By Court','Admission']))

    # Convert Move sub sub to a categorical variable in the sort order of priority move list
moves['MOVE_SUB_TYPE_DESCRIPTION'] = pd.Categorical(moves['MOVE_SUB_TYPE_DESCRIPTION'], categories = priority_move, ordered = True)

moves = moves.sort_values(by=['FILE_REFERENCE','ACTUAL_DATE','MOVE_SUB_TYPE_DESCRIPTION'])

    # View Duplicates to see if the order of entries, where Actual_Date is the same, is as expected. 
    # For example, IF ACTUAL_DATE IS THE SAME, abscond should come first before return from abscond, disposal should come first before admission.
moves[moves.duplicated('FILE_REFERENCE',keep=False)]

moves = moves.sort_values(by=['FILE_REFERENCE','ACTUAL_DATE','MOVE_SUB_TYPE_DESCRIPTION'])
moves2 = moves.drop_duplicates('FILE_REFERENCE', keep='first').copy()
len(moves2) #441

# moves2['MOVE_TYPE_DESCRIPTION'].value_counts()
# moves2['STATUS_DESCRIPTION'].value_counts()

# moves2.groupby(['MOVE_TYPE_DESCRIPTION','FROM_ESTABLISHMENT_DESCRIPTION'],as_index=False).agg('size')
# moves2.groupby(['MOVE_TYPE_DESCRIPTION','STATUS_DESCRIPTION'],as_index=False).agg('size')
# moves2[~(moves2['MOVE_TYPE_DESCRIPTION'] == 'Admission')]['FROM_ESTABLISHMENT_DESCRIPTION'].value_counts()

# moves2[moves2.duplicated(subset='FILE_REFERENCE',keep=False)].sort_values(['FILE_REFERENCE','ACTUAL_DATE']).head(10)

    # Aditional fields to identify Prior variables before first movements on or after 31 Dec
moves2['PRIOR_ESTA'] = moves2['FROM_ESTABLISHMENT_DESCRIPTION']
moves2['PRIOR_LOCATION'] = 'In Hospital'

    # All admissions were not in custody on 31 Dec 
# moves2[moves2['MOVE_TYPE_DESCRIPTION'] =='Admission'][movesCol]
moves2.loc[moves2['MOVE_TYPE_DESCRIPTION'] =='Admission','PRIOR_LOCATION'] = 'Not in Pop'

    # All Recalls were CD in community on 31 Dec
moves2.loc[moves2['MOVE_TYPE_DESCRIPTION'] =='Recall','PRIOR_LOCATION'] = 'Conditionally Discharged'

    # Absolute discharge is nuansed on 31 Dec
        # If not from community England, then from hospital
moves2.loc[(moves2['MOVE_TYPE_DESCRIPTION'] =='Absolute Discharge') & (moves2['FROM_ESTABLISHMENT_DESCRIPTION'] =='Community - England'),'PRIOR_LOCATION'] = 'Conditionally Discharged'

    # Abscond is Tricky on 31 Dec
        # All absconds/escape were in hospital on 31 Dec, except those who returned from abscond/escape after 31 Dec
moves2.loc[(moves2['MOVE_TYPE_DESCRIPTION'] =='Abscond/Escape') & (moves2['MOVE_SUB_TYPE_DESCRIPTION'] =='Return from Abscond/Escape'),'PRIOR_LOCATION'] = 'Not in Pop'

    # Deceased is nuansed on 31 Dec
        # If not from community England, then from hospital
moves2.loc[(moves2['MOVE_TYPE_DESCRIPTION'] =='Deceased') & (moves2['FROM_ESTABLISHMENT_DESCRIPTION'] =='Community - England'),'PRIOR_LOCATION'] = 'Conditionally Discharged'

pop.head()
moves2.head()
len(pop)
len(moves2)

#--------------- Join Populatoin and Movements after 31 Dec to pop date to identify those who were not in the pop on 31 Dec

popRetain = ['FILE_REFERENCE', 'FAMILY_NAME','AUTHORITY_FOR_DETENTION_DESCRIPTION','PRIOR_AUTHORITY','STATUS_DESCRIPTION','PRIOR_LOCATION','CURRENT_ESTABLISHMENT_DESCRIPTION','PRIOR_ESTA',
       'CURRENT_ESTABLISHMENT_UNIT_DESCRIPTION', 'DA_CUSTODY_TYPE_DESCRIPTION','DA_STATUS_DESCRIPTION', 'DOB', 'DATE_OF_HOSPITAL_ORDER','DATE_RECEIVED_IN_MHU', 'DETAINING_HOSPITAL_DESCRIPTION',
       'DETAINING_UNIT_DESCRIPTION', 'DOLS_ORDER', 'END_DATE', 'ETHNICITY_DESCRIPTION', 'EXPIRY_DATE', 'EXTREMISM_TYPE_DESCRIPTION', 'FIRST_NAMES', 'GENDER',  'LEGAL_CATEGORY_DESCRIPTION', 'LTLoA_FLAG',
       'MENTAL_DISORDER_DESCRIPTION', 'NATIONALITY_DESCRIPTION', 'NOMS_ID', 'NOTEWORTHY_FLAG', 'OWNING_CASEWORKER_DESCRIPTION', 'OWNING_TEAM_DESCRIPTION', 'PRISON_NUMBER',  'RESTRICTED_FLAG', 'SECURITY_CATEGORY_DESCRIPTION',
       'SUPERVISED_DISCHARGE_FLAG', 'TECHNICAL_RECALL_FLAG']

query = """SELECT a.*, 
                  b.AUTHORITY_FOR_DETENTION_DESCRIPTION AS PRIOR_AUTHORITY, 
                  b.PRIOR_ESTA,
                  b. PRIOR_LOCATION
                  
            FROM pop AS a LEFT JOIN moves2 AS b
            
            ON  (
                    (a.FILE_REFERENCE = b.FILE_REFERENCE  and a.FILE_REFERENCE IS NOT NULL) OR
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)
                ) """

pop_mv = duckdb.sql(query).df()
pop_mv = pop_mv[popRetain]
len(pop_mv) # 8005
pop_mv[pop_mv['PRIOR_LOCATION'] == 'Not in Pop'].head()
    
    # drop those in the population on 31 Dec
pop_mv['PRIOR_LOCATION'].value_counts()
pop_mv[pop_mv['PRIOR_LOCATION'] == 'Not in Pop'].head()

pop_mv = pop_mv[~pop_mv['PRIOR_LOCATION'] == 'Not in Pop']

pop_mv_check = pop_mv[~pop_mv['PRIOR_LOCATION'].isna()]
len(pop_mv_check) # 343
pop_mv_check.head()

pop_mv.loc[~pop_mv['PRIOR_LOCATION'].isna(),'AUTHORITY_FOR_DETENTION_DESCRIPTION'] = pop_mv['PRIOR_AUTHORITY']
pop_mv.loc[~pop_mv['PRIOR_LOCATION'].isna(),'STATUS_DESCRIPTION'] = pop_mv['PRIOR_LOCATION']
pop_mv.loc[~pop_mv['PRIOR_LOCATION'].isna(),'CURRENT_ESTABLISHMENT_DESCRIPTION'] = pop_mv['PRIOR_ESTA']

pop_mv['S']
query2 = """SELECT a.*,b.DATE_OF_HOSPITAL_ORDER
                  
            FROM moves2 AS a LEFT JOIN pop AS b
            
            ON  (
                    (a.FILE_REFERENCE = b.FILE_REFERENCE  and a.FILE_REFERENCE IS NOT NULL) OR
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)
                ) 
            """

mv_pop = duckdb.sql(query2).df()
mv_pop = mv_pop[mv_pop['DATE_OF_HOSPITAL_ORDER'].isna()]
len(mv_pop) # 102
mv_pop.head()

# pop_mv[pop_mv['FILE_REFERENCE']=='3/4816']



# pop.info() # 7842

# pop['AUTHORITY_FOR_DETENTION_DESCRIPTION'].value_counts(dropna=False)

#---------------Year of hospital order and year of receiving in MHCS should be up to year of snapshot data - check if we can do this

# pop['DATE_OF_HOSPITAL_ORDER'].dt.year.value_counts(dropna=False).sort_index()
# pop['DATE_RECEIVED_IN_MHU'].dt.year.value_counts(dropna=False).sort_index()

del_cond = (pop['DATE_OF_HOSPITAL_ORDER'].dt.year > year) # | (pop['DATE_RECEIVED_IN_MHU'].dt.year > year)

# pop[del_cond]['FILE_REFERENCE'] # 2 cases to delete MHU_414312 and PPU_259114

pop = pop[~del_cond]
len(pop) # 7840

#--------------- Remove Non applicables and in foreign prisons

# pop['AUTHORITY_FOR_DETENTION_DESCRIPTION'].value_counts(dropna = False)

pop = pop[~pop['AUTHORITY_FOR_DETENTION_DESCRIPTION'].isin(['Not Applicable', 'Not Specified'])]
len(pop)

# pop[pop['CURRENT_ESTABLISHMENT_DESCRIPTION'].str.contains('forei', case=False)]

pop = pop[~pop['CURRENT_ESTABLISHMENT_DESCRIPTION'].str.contains('forei', case=False)]
len(pop) # 7837

#---------------  Remove unrestricted patients

# pop['DA_CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

pop = pop [pop['DA_CUSTODY_TYPE_DESCRIPTION'] != 'Unrestricted Patient']
len(pop) # 7836

#--------------- Add some fields

    # Gender
# pop.GENDER.unique()
pop.loc[pop['GENDER'] == 'M ( Was F )', 'GENDER'] = 'M'
pop.loc[pop['GENDER'] == 'F ( Was M )', 'GENDER'] = 'F'

    # Status/Loation
    
# pop['STATUS_DESCRIPTION'].unique()
pop['STATUS'] = np.where(pop['STATUS_DESCRIPTION'] == 'Conditionally Discharged','bCD','aHospital')
# pd.crosstab(pop['STATUS_DESCRIPTION'],pop['STATUS'], margins = True, margins_name = 'Total')

    # Age
    
# pop['DOB'].dt.year.value_counts(dropna=False).sort_index() # question DOB 1900
pop['AGE'] = pop.apply(lambda x: TimeDiffs.year_diff(x['DOB'],snapshotDate),axis=1)
# pop['AGE'].value_counts().sort_index()
# pop[['DOB','AGE']].head()

a1 = pop['AGE'] <= 20
a2 = (~a1) & (pop['AGE'] <= 39)
a3 = ~(a1 | a2) & (pop['AGE'] <= 59)
a4 = ~(a1 | a2 | a3)

pop.loc[a1,'AGEBAND'] = '20 and under'
pop.loc[a2,'AGEBAND'] = '21-39'
pop.loc[a3,'AGEBAND'] = '40-59'
pop.loc[a4,'AGEBAND'] = '60 or more' # formerly '60+'

# pd.crosstab(pop['AGE'],pop['AGEBAND'], margins = True, margins_name = 'Total')

#--------------- Deduplicate

    # missing file reference repalcement with prison number
# pop[pop['FILE_REFERENCE'].isna()][['FILE_REFERENCE','PRISON_NUMBER']] # None
pop.loc[pop['FILE_REFERENCE'].isna(),'FILE_REFERENCE'] = pop['PRISON_NUMBER']

    # check repeated file_reference
# pop[pop.duplicated(subset =['FILE_REFERENCE'], keep=False)] # 0

pop['FL'] = pop['FILE_REFERENCE'].astype(str) # temporary string column to allow sorting on file reference
pop = pop.sort_values(by=['FL','DATE_OF_HOSPITAL_ORDER'],ascending = [True,False])
pop = pop.drop_duplicates(subset=['FILE_REFERENCE'], keep ='first')

len(pop) #7 836

#--------------- match up Population Detention Authority Data to DetAuth reference file
detAuth = pd.read_excel("s3://alpha-omppg/Mental Health/Reference/Reference.xls", sheet_name = "DetAuth")
detAuth_dict1 = dict(zip(detAuth['AUTHORITY_FOR_DETENTION_DESCRIPT'],detAuth['DETAUTH']))
detAuth_dict2 = dict(zip(detAuth['AUTHORITY_FOR_DETENTION_DESCRIPT'],detAuth['DETAUTH_PUB']))

pop['DETAUTH'] = pop['AUTHORITY_FOR_DETENTION_DESCRIPTION'].map(detAuth_dict1).fillna('check')
pop['DETAUTH2'] = pop['AUTHORITY_FOR_DETENTION_DESCRIPTION'].map(detAuth_dict2).fillna('check')

pd.crosstab(pop['AUTHORITY_FOR_DETENTION_DESCRIPTION'],pop['DETAUTH'], margins = True, margins_name = 'Total')
# pop['DETAUTH'].isna().sum() #0

#---------------------------------- Remove Test cases
    # Check 'test' cases and remove
# pop[pop['FAMILY_NAME'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]
# pop[pop['FIRST_NAMES'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

Test_Case_Mask =  (   (pop['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (pop['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (pop['FILE_REFERENCE'] != 'T18122')

pop = pop[~Test_Case_Mask]
len(pop) # 7834

    # Check 'case' cases and remove
# pop[pop['FAMILY_NAME'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0
# pop[pop['FIRST_NAMES'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

    # Check 'digit' cases - these are normally good and shoulbe untouched
# pop[pop['FAMILY_NAME'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 
# p[pop['FIRST_NAMES'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 


#----------------------------------  BRING IN OFFENCE DATA - RUN YOUR OWN OFFENCE DATA CAPTURING EVERYTHING;
Offences = pd.read_excel("s3://alpha-omppg/Mental Health/2023/Raw Data/Offence_all.xls")
Offences = Offences.replace("–","-")
Offences.head()

query = """SELECT a.*, 
                  b.OFFENCE_DESCRIPTION, 
                  b.OFFENCE_GROUP_DESCRIPTION
                  
            FROM pop AS a LEFT JOIN Offences AS b
            
            ON  (
                    (a.FILE_REFERENCE = b.FILE_REFERENCE  and a.FILE_REFERENCE IS NOT NULL) OR
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)
                ) AND
                a.DATE_OF_HOSPITAL_ORDER = b.DATE_OF_HOSPITAL_ORDER AND a.DATE_OF_HOSPITAL_ORDER IS NOT NULL"""

pop_off = duckdb.sql(query).df()
len(pop_off) # 12077

    # Resolve missing offence cases
missing_offence = pop_off[pop_off['OFFENCE_DESCRIPTION'].isna()]
missing_offence = missing_offence.drop(['OFFENCE_DESCRIPTION',  'OFFENCE_GROUP_DESCRIPTION'], axis=1)

query2 = """SELECT a.*, 
                  b.OFFENCE_DESCRIPTION, 
                  b.OFFENCE_GROUP_DESCRIPTION,
                  b.AUTHORITY_FOR_DETENTION_DESCRIPTION as AFD_OFF,
                  b.DATE_OF_HOSPITAL_ORDER as DOHO_OFF,
                  b.DATE_RECEIVED_IN_MHU as DRIMU_OFF
                  
            FROM missing_offence AS a LEFT JOIN Offences AS b
            
            ON  (
                    (a.FILE_REFERENCE = b.FILE_REFERENCE  and a.FILE_REFERENCE IS NOT NULL) OR
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)
                ) """

missing_offence2 = duckdb.sql(query2).df()

retain = ['FILE_REFERENCE', 'PRISON_NUMBER','FAMILY_NAME', 'AUTHORITY_FOR_DETENTION_DESCRIPTION', 'AFD_OFF', 'DATE_OF_HOSPITAL_ORDER','DOHO_OFF','DATE_RECEIVED_IN_MHU','DRIMU_OFF','OFFENCE_DESCRIPTION','OFFENCE_GROUP_DESCRIPTION','DA_CUSTODY_TYPE_DESCRIPTION']

missing_offence2[retain]

Offences[Offences['FILE_REFERENCE'].isin(missing_offence['FILE_REFERENCE'])]


    
    # Deduplicate

dups = pop_off[pop_off.duplicated(subset =['FILE_REFERENCE'], keep=False)].head(50)[retain] 
dups.to_excel("More_Than_One_Offence.xlsx", index = False)

 
dups.to_excel("More_Than_One_Offence.xlsx", index = False)

pop = pop.sort_values(by=['FL','DATE_OF_HOSPITAL_ORDER'],ascending = [True,False])
pop = pop.drop_duplicates(subset=['FILE_REFERENCE'], keep ='first')

len(Offences) # 61905

Offences[Offences['OFFENCE_DESCRIPTION'].isin(['','Not Specified','Not Applicable'])][['PRISON_NUMBER','DATE_OF_HOSPITAL_ORDER','DATE_RECEIVED_IN_MHU','OFFENCE_DESCRIPTION']]

Offences = Offences[~Offences['OFFENCE_DESCRIPTION'].isin(['','Not Specified','Not Applicable'])]
len(Offences) # 61834

   # missing file reference repalcement with prison number
# fences[Offences['FILE_REFERENCE'].isna()][['FILE_REFERENCE','PRISON_NUMBER']] # None
Offences.loc[Offences['FILE_REFERENCE'].isna(),'FILE_REFERENCE'] = Offences['PRISON_NUMBER']

  # missing date of hospital
Offences[Offences['DATE_OF_HOSPITAL_ORDER'].isna()][['PRISON_NUMBER','DATE_OF_HOSPITAL_ORDER','DATE_RECEIVED_IN_MHU']] # None
Offences.loc[Offences['DATE_RECEIVED_IN_MHUFILE_REFERENCE'].isna(),'FILE_REFERENCE'] = Offences['PRISON_NUMBER']















recall_to_release.info() #15481

def calculate_match(row):
   
    condition_a = (row['FILE_REFERENCE'] == row['REC_FILEREF'])
    condition_b = (row['PRISON_NUMBER'] == row['REC_PRISNUM'])
      
    if condition_a and condition_b:
        return 2
    elif condition_a:
        return 1
    elif condition_b:
        return 1
    else:
        return 0

# Apply the function to each row
recall_to_release['MATCH'] = recall_to_release.apply(calculate_match, axis=1)

# recall_to_release[recall_to_release['PRISON_NUMBER'].isna()].head()[['FILE_REFERENCE','REC_FILEREF','MATCH','PRISON_NUMBER','REC_PRISNUM']]

# recall_to_release['MATCH'].value_counts(dropna=False)

#---------------------------------- deduplicate
recall_to_release.sort_values(by=['MATCH','LAST_LICENCE_REVOKE_DATE'],ascending = [False,False], inplace = True)
recall_to_release.drop_duplicates(subset=['PRISON_NUMBER','RELEASE_DATE'], keep ='first', inplace = True)
recall_to_release.shape # 15476

#---------------------------------- Add next recall to releases dataset

recall_to_release = recall_to_release.drop(['REC_DOB','REC_SURNAME','REC_FILEREF','REC_PRISNUM'],axis=1)

query2 = """SELECT a.*, 
                b.LICENCE_REVOKE_DATE AS NEXT_LICENCE_REVOKE_DATE, 
                b.RTC_DATE AS NEXT_RTC_DATE,
                b.RECALLNUM AS NEXT_RECALLNUM,
                b.NUMBER_OF_RECALL_REASONS AS NEXT_RECALL_NUMBER_OF_REASONS, 
                b.RECALL_REASON_DESCRIPTIONS AS NEXT_RECALL_REASONS,
                b.FURTHER_CHARGE AS NEXT_RECALL_FURTHER_CHARGE,
                b.NPS_CRC_NAME AS NEXT_RECALL_AREA,
                b.CUSTODYTYPE AS NEXT_RECALL_CUSTODYTYPE,
                b.PRISON_NUMBER AS REC_PRISNUM, b.FILE_REFERENCE AS REC_FILEREF,
                b.FAMILY_NAME AS REC_SURNAME, 
                b.DOB AS REC_DOB
        
            FROM recall_to_release AS a LEFT JOIN recalls AS b
            
            ON  (a.RELEASE_DATE <= b.LICENCE_REVOKE_DATE) AND
                (a.NEXT_RELEASE_DATE > b.LICENCE_REVOKE_DATE OR a.NEXT_RELEASE_DATE IS NULL) AND
                (
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL)
                )"""


recall_to_release2 = duckdb.sql(query2).df()
recall_to_release2.info()

#recall_to_release2[recall_to_release2['FILE_REFERENCE']=='K13370'].sort_values('RELEASE_DATE')
#sasReleases[sasReleases['FILE_REFERENCE']=='K13370'].sort_values('RELEASE_DATE')
#isp_releases_final[isp_releases_final['FILE_REFERENCE']=='K13370'].sort_values('RELEASE_DATE')

# Apply the function to each row
recall_to_release2['MATCH'] = recall_to_release2.apply(calculate_match, axis=1)

recall_to_release2['MATCH'].value_counts(dropna=False)

recall_to_release2['UNIQUEREF']= recall_to_release2['PRISON_NUMBER'].astype(str) + recall_to_release2['RELEASE_DATE'].astype(str)

#---------------------------------- deduplicate
recall_to_release2.sort_values(by=['MATCH','NEXT_LICENCE_REVOKE_DATE'],ascending = [False,True], inplace = True)
recall_to_release2.info()
recall_to_release2.head()

isp_releases_final = recall_to_release2.drop_duplicates(subset=['UNIQUEREF'], keep ='first')
isp_releases_final.shape #15476

isp_releases_final['MATCH'].value_counts(dropna=False)

isp_releases_final = isp_releases_final.drop(['REC_DOB','REC_SURNAME','REC_FILEREF','REC_PRISNUM'],axis=1)

# recall_to_release[recall_to_release['FILE_REFERENCE'].isin(['T4778','S7004'])]\
    #[['FILE_REFERENCE','PRISON_NUMBER','REC_FILEREF','REC_PRISNUM','RELEASE_DATE','LAST_LICENCE_REVOKE_DATE','LAST_RTC_DATE','MATCH']]

#sasReleases[sasReleases['FILE_REFERENCE'].isin(['T4778','S7004'])]\
    #[['FILE_REFERENCE','PRISON_NUMBER','RELEASE_DATE','LAST_LICENCE_REVOKE_DATE','LAST_RTC_DATE','NEXT_LICENCE_REVOKE_DATE']]

#recalls[recalls['FILE_REFERENCE'].isin(['T4778','S7004'])]\
 #   [['FILE_REFERENCE','PRISON_NUMBER','LICENCE_REVOKE_DATE','RTC_DATE']]

#---------------------------------- Create derived variables on releases dataset

isp_releases_final = isp_releases_final.copy()

isp_releases_final['LATEST_QUARTER'] = pd.Timestamp(year, quarter * 3 - 2, 1) - pd.Timedelta(days=1)

isp_releases_final['MONTHS_UNTIL_RECALL'] = (isp_releases_final['NEXT_LICENCE_REVOKE_DATE'] - isp_releases_final['RELEASE_DATE']) / np.timedelta64(1, 'M')
isp_releases_final['MONTHS_UNTIL_RECALL'] = isp_releases_final['MONTHS_UNTIL_RECALL'].apply(np.floor)
# isp_releases_final['MONTHS_UNTIL_RECALL'].value_counts(dropna=False).sort_index()

scope_rel_mask = isp_releases_final['RELEASE_DATE'] <= isp_releases_final['LATEST_QUARTER']
isp_releases_final['RECALLED_3_MONTHS'] = np.where(scope_rel_mask, 
                                                        np.where(isp_releases_final['MONTHS_UNTIL_RECALL'] < 3,100,0),
                                                    np.nan)

scope_rel_mask2 = isp_releases_final['RELEASE_DATE'] <= (isp_releases_final['LATEST_QUARTER'] - pd.DateOffset(months = 3))
isp_releases_final['RECALLED_6_MONTHS'] = np.where(scope_rel_mask2, 
                                                        np.where(isp_releases_final['MONTHS_UNTIL_RECALL'] < 6,100,0),
                                                    np.nan)

scope_rel_mask3 = isp_releases_final['RELEASE_DATE'] <= (isp_releases_final['LATEST_QUARTER'] - pd.DateOffset(months = 9))
isp_releases_final['RECALLED_12_MONTHS'] = np.where(scope_rel_mask3, 
                                                        np.where(isp_releases_final['MONTHS_UNTIL_RECALL'] < 12,100,0),
                                                    np.nan)

isp_releases_final['RELEASE_TYPE'] = np.where(isp_releases_final['LAST_RTC_DATE'].isna(),'First Release','Recall Re-release')

rel_type_mask = (isp_releases_final['RELEASE_DATE'] > isp_releases_final['FIRST_RELEASE_DATE']) & \
                (isp_releases_final['FIRST_RELEASE_DATE'] >= isp_releases_final['TARIFF_EXPIRY_DATE']) 

isp_releases_final['RELEASE_TYPE'] = np.where(rel_type_mask,'Recall Re-release',isp_releases_final['RELEASE_TYPE'])


rel_type_mask = (isp_releases_final['RELEASE_DATE'] > isp_releases_final['LAST_RELEASE_DATE']) & \
                (isp_releases_final['LAST_RELEASE_DATE'] >= isp_releases_final['TARIFF_EXPIRY_DATE']) 

isp_releases_final['RELEASE_TYPE'] = np.where(rel_type_mask,'Recall Re-release',isp_releases_final['RELEASE_TYPE'])

isp_releases_final['RELEASE_TYPE'] = np.where(isp_releases_final['RELEASE_DATE'].dt.year < 2013,'First Release',isp_releases_final['RELEASE_TYPE'])

served_mask = (isp_releases_final['RELEASE_TYPE'] == 'First Release') & (isp_releases_final['DOS'] < isp_releases_final['RELEASE_DATE'])

isp_releases_final['YEARS_SERVED']  = np.where(served_mask, 
                                               ((isp_releases_final['RELEASE_DATE'] - isp_releases_final['DOS']) / np.timedelta64(1, 'Y')).apply(np.floor),
                                               np.nan)

isp_releases_final['MONTHS_SERVED']  = np.where(served_mask, 
                                               ((isp_releases_final['RELEASE_DATE'] - isp_releases_final['DOS']) / np.timedelta64(1, 'M')).apply(np.floor),
                                               np.nan)

isp_releases_final.info() #15476
sasReleases.info() #15476


#---------------------------------- Some checks

sasReleases['RELEASE_TYPE'].value_counts(dropna=False)
isp_releases_final['RELEASE_TYPE'].value_counts(dropna=False)

sasFirsts = sasReleases[sasReleases['RELEASE_TYPE']=='First Release'][['FILE_REFERENCE','RELEASE_TYPE','RELEASE_DATE','DOS','MONTHS_SERVED']]
meFirsts = isp_releases_final[isp_releases_final['RELEASE_TYPE']=='First Release'][['FILE_REFERENCE','RELEASE_TYPE','RELEASE_DATE','DOS','MONTHS_SERVED']]

checkdf = meFirsts[~(meFirsts['FILE_REFERENCE'].isin(sasFirsts['FILE_REFERENCE']))]
checkdf.shape


isp_releases_final[isp_releases_final.FILE_REFERENCE.isin(checkdf.FILE_REFERENCE)][['FILE_REFERENCE','RELEASE_TYPE','RELEASE_DATE','FIRST_RELEASE_DATE','DOS','MONTHS_SERVED','LAST_RTC_DATE','TARIFF_EXPIRY_DATE','LAST_RELEASE_DATE']].sort_values(['FILE_REFERENCE','RELEASE_DATE'])

sasReleases[sasReleases['FILE_REFERENCE']=='103229'][['FILE_REFERENCE','RELEASE_TYPE','RELEASE_DATE','DOS','MONTHS_SERVED','LAST_RTC_DATE','TARIFF_EXPIRY_DATE','LAST_RELEASE_DATE']]

# p = pop.drop(columns = ['FL'])

#---------------------------------- Temporary Save, delete later

isp_releases_final =isp_releases_final.drop(['MATCH','UNIQUEREF'],axis=1)

isp_releases_final.to_pickle(f"isp_releases_{year}q{quarter}_b.pkl")

