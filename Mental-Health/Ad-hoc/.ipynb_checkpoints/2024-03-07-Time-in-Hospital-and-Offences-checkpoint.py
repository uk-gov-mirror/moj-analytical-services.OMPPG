""" 
GOAL: PRODUCE OFFENCE BREAKDOWNSRESTRICTED PATIENTS STATISTICS FOR PUBLICATION
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

#--------------- Import the population dataset and replace long dash with normal dash

fl_off = pd.read_excel("s3://alpha-omppg/Mental Health/2023/Raw Data/Offence_all.xls")
fl_off = fl_off.replace("–","-")

fl_off = fl_off.drop_duplicates(subset=['FILE_REFERENCE','PRISON_NUMBER'])
len(fl_off)

pop = pd.read_excel(f"s3://alpha-omppg/Mental Health/{year}/Raw Data/population.xlsx")
pop = pop.replace("–","-")
len(pop) # 7842

#---------------------------------- Remove Test cases
    # Check 'test' cases and remove
# pop[pop['FAMILY_NAME'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

# pop[pop['FIRST_NAMES'].str.contains('Test',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

Test_Case_Mask =  (   (pop['FAMILY_NAME'].str.contains('Test',case = False,na = False)) |
                      (pop['FIRST_NAMES'].str.contains('Test',case = False,na = False))
                  ) & (pop['FILE_REFERENCE'] != 'T18122')

# releases[Test_Case_Mask][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 24 cases

pop = pop[~Test_Case_Mask]

pop.shape  #7840
pop['row'] = list(range(len(pop))) # similar to SAS _n_

    # Check 'case' cases and remove
#pop[pop['FAMILY_NAME'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0
#pop[pop['FIRST_NAMES'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 0

    # Check 'digit' cases - these are normally good and shoulbe untouched
#pop[pop['FAMILY_NAME'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 
#pop[pop['FIRST_NAMES'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 

#---------------------------------- Ensure File Reference and Prison numbers are proper to avoid wrong matching

    # Check prison numbers without digits - should be set to missing
# pop[~pop['PRISON_NUMBER'].astype(str).str.contains(r'\d',na=False)][['FILE_REFERENCE','PRISON_NUMBER','FAMILY_NAME','FIRST_NAMES']]

pop.loc[pop['PRISON_NUMBER'].isin(['Not Applicable']),'PRISON_NUMBER'] = np.nan # potential problem with only 'Not Applicable'

    # Check File reference without digits - should be set to missing
pop[~pop['FILE_REFERENCE'].astype(str).str.contains(r'\d',na=False)][['FILE_REFERENCE','PRISON_NUMBER','FAMILY_NAME','FIRST_NAMES']] # none

len(pop) #7840

#---------------------------------- Correct file reference
query0 = """SELECT a.*, 
                  b.FILE_REFERENCE AS FR2,
                  b.PRISON_NUMBER  AS PN2
                  
            FROM pop AS a LEFT JOIN fl_off AS b
            
            ON  (
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) OR
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)
                ) 
                """

pop2 = duckdb.sql(query0).df()

len(pop2) # 7843
pop2.head()
retain = ['row','FILE_REFERENCE','FR2','PRISON_NUMBER','PN2','FAMILY_NAME','DATE_OF_HOSPITAL_ORDER','DATE_RECEIVED_IN_MHU','AUTHORITY_FOR_DETENTION_DESCRIPTION','DA_STATUS_DESCRIPTION','END_DATE','CURRENT_ESTABLISHMENT_DESCRIPTION']

pop2[(pop2['FILE_REFERENCE'] != pop2['FR2']) & (~pop2['FR2'].isna())][retain].head(20)

pop2.loc[(pop2['FILE_REFERENCE'] != pop2['FR2']) & (pop2['PRISON_NUMBER'] == pop2['PN2']),'FILE_REFERENCE'] = pop2['FR2']

pop2[pop2['FILE_REFERENCE'] != pop2['FR2']][retain].head(20) # 0

pop2[(pop2['PRISON_NUMBER'] != pop2['PN2']) & (~pop2['PN2'].isna())][retain].head(20)

pop2.loc[(pop2['PRISON_NUMBER'] != pop2['PN2']) & (~pop2['PN2'].isna()) &(pop2['PN2'] !='Not Applicable'),'PRISON_NUMBER'] = pop2['PN2']

pop2[pop2.duplicated('FILE_REFERENCE',keep=False)][retain]

pop2 = pop2.drop(index=[1454,1650])
pop2[pop2.duplicated('row',keep=False)][retain]
pop2 = pop2.drop(index=[6846])

pop2 = pop2.drop(['row','FR2','PN2'],axis=1)
pop2.head()
pop2 = pop2.drop_duplicates(subset=['FILE_REFERENCE','PRISON_NUMBER'])
len(pop2)
pop = pop.drop(['row'],axis=1)
pop2 = pop2[pop.columns]

# pop2.to_excel("s3://alpha-omppg/Mental Health/2023/Raw Data/population_2023.xlsx", index=False)

 # End dates before 31 should be removed - these are ended cases without their status set to closed
pop2[~pop2['END_DATE'].isna()].head()

admissions = pd.read_excel(f"s3://alpha-omppg/Mental Health/Ad hoc/Admissions_4March.xls")
admissions = admissions.replace("–","-")
admissions.ACTUAL_DATE.dt.year.max()
admissions = admissions[admissions['ACTUAL_DATE'].dt.year <=2023]

recalls = pd.read_excel(f"s3://alpha-omppg/Mental Health/Ad hoc/Recalls_4March.xls")
recalls = recalls.replace("–","-")
recalls = recalls[recalls['ACTUAL_DATE'].dt.year <=2023]

    # Keep latest admissions and recalls
admissions = admissions.sort_values(by =['FILE_REFERENCE','ACTUAL_DATE'], ascending =[ True,False])
# admissions.head(10)
admissions = admissions.drop_duplicates('FILE_REFERENCE')
# len(admissions)

recalls = recalls.sort_values(by =['FILE_REFERENCE','ACTUAL_DATE'], ascending =[ True,False])
# recalls.head(10)

recalls = recalls.drop_duplicates('FILE_REFERENCE')
# len(recalls)

# ~-------------- Combine recalls and admissions and keep the earliest
rec_and_admin = pd.concat([admissions, recalls],axis = 0,ignore_index=True)[['FILE_REFERENCE','ACTUAL_DATE','PRISON_NUMBER','AUTHORITY_FOR_DETENTION_DESCRIPTION']]

rec_and_admin = rec_and_admin.sort_values(by =['FILE_REFERENCE','ACTUAL_DATE'], ascending =[ True,False])
rec_and_admin= rec_and_admin.drop_duplicates('FILE_REFERENCE')

len(rec_and_admin)

    # check datetime types
pop.info()

    # rearrange columns
retain_order = ['FILE_REFERENCE', 'FAMILY_NAME', 'DATE_OF_HOSPITAL_ORDER', 'DATE_RECEIVED_IN_MHU','AUTHORITY_FOR_DETENTION_DESCRIPTION','DA_STATUS_DESCRIPTION', 'END_DATE']
pop2 = pop2[retain_order + [col for col in pop2.columns if col not in retain_order]]

    # deduplicate pop and keep the latest hospital order
pop2 = pop2.sort_values(by =['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER'], ascending =[ True,False]) # 
pop2 = pop2.drop_duplicates(['FILE_REFERENCE'],keep='first') # 7840
                           
#----------------------------------  Add Recalls and Admissions;
query = """SELECT a.*, 
                  b.ACTUAL_DATE AS ADMIN_ACTUAL,
                  b.FILE_REFERENCE AS ADMIN_FR,
                  b.PRISON_NUMBER  AS ADMIN_PN
                  
            FROM pop2 AS a LEFT JOIN rec_and_admin AS b
            
            ON  (
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) OR
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)
                ) 
                """

pop_Admin_Rec = duckdb.sql(query).df()

len(pop_Admin_Rec) #7843

pop_Admin_Rec[pop_Admin_Rec.duplicated('FILE_REFERENCE',keep=False)][['FILE_REFERENCE','ADMIN_FR','PRISON_NUMBER','ADMIN_PN','FAMILY_NAME','ADMIN_ACTUAL','DATE_OF_HOSPITAL_ORDER','DATE_RECEIVED_IN_MHU','AUTHORITY_FOR_DETENTION_DESCRIPTION','DA_STATUS_DESCRIPTION','END_DATE','CURRENT_ESTABLISHMENT_DESCRIPTION']]

pop_Admin_Rec = pop_Admin_Rec.drop(index =[1069,1615,1616])
pop_Admin_Rec[pop_Admin_Rec['ADMIN_ACTUAL'].isna()] # these genuinely have no admissions set

#----------------------------------  Create time to current date;
pop_Admin_Rec['MONTHS_IN'] = pop_Admin_Rec.apply(lambda x: TimeDiffs.month_diff(x['ADMIN_ACTUAL'],snapshotDate),axis=1)
pop_Admin_Rec['YEAR_IN'] = pop_Admin_Rec.apply(lambda x: TimeDiffs.year_diff(x['ADMIN_ACTUAL'],snapshotDate),axis=1)

pop_Admin_Rec['YEAR_IN'].value_counts(dropna=False)

pop_Admin_Rec = pop_Admin_Rec.sort_values(by =['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER'], ascending =[ True,False])
pop_Admin_Rec[pop_Admin_Rec.duplicated('FILE_REFERENCE',keep=False)][['FILE_REFERENCE','FAMILY_NAME','DATE_OF_HOSPITAL_ORDER','DATE_RECEIVED_IN_MHU','AUTHORITY_FOR_DETENTION_DESCRIPTION','DA_STATUS_DESCRIPTION','END_DATE','CURRENT_ESTABLISHMENT_DESCRIPTION','MONTHS_IN']]

pop_Admin_Rec = pop_Admin_Rec.drop_duplicates('FILE_REFERENCE', keep='first')

len(pop_Admin_Rec[pop_Admin_Rec['ADMIN_ACTUAL'].isna()]['FILE_REFERENCE'].unique()) # 22

len(pop_Admin_Rec['FILE_REFERENCE'].unique()) # 7840 no duplicates

# pop_Admin_Rec.to_parquet("pop_Admin_Rec.pkl")

pop_Admin_Rec.DA_STATUS_DESCRIPTION.value_counts(dropna=False) #7910
pop_Admin_Rec.STATUS_DESCRIPTION.value_counts(dropna=False) #7910

len(pop_Admin_Rec)

inHospital = pop_Admin_Rec[pop_Admin_Rec['STATUS_DESCRIPTION'] != 'Conditionally Discharged'].copy()
len(inHospital[inHospital['ADMIN_ACTUAL'].isna()]['FILE_REFERENCE'].unique()) # 22

# Define bins: Note the bins are in months (1 year = 12 months, 5 years = 60 months, 10 years = 120 months)
bins = [0, 1, 5, 10, float('inf')]  # float('inf') is used for infinity
labels = ['Up to 1 year', '1-5 years', '5-10 years', 'More than 10 years']

# Categorize the data into bins
inHospital['TIME_CATEGORY'] = pd.cut(inHospital['YEAR_IN'], bins=bins, labels=labels, right=False)
len(inHospital)
# Count the number of occurrences in each category
inHospital['TIME_CATEGORY'].value_counts(dropna=False).sort_index()


##...........................Only 37/41s and 45A
inHospital['AUTHORITY_FOR_DETENTION_DESCRIPTION'].unique()

rlv_Auths = inHospital[inHospital['AUTHORITY_FOR_DETENTION_DESCRIPTION'].isin(['S37/41 - MHA 1983 - Hospital Order','S45A - MHA 1983 - Hospital & Limitation Direction'])].copy()

rlv_Auths.groupby('AUTHORITY_FOR_DETENTION_DESCRIPTION',dropna=False)['TIME_CATEGORY'].value_counts(dropna=False).sort_index()

rlv_Auths[rlv_Auths['AUTHORITY_FOR_DETENTION_DESCRIPTION']=='S37/41 - MHA 1983 - Hospital Order']['TIME_CATEGORY'].value_counts(dropna=False).sort_index()

len(rlv_Auths) # 2791

#----------------------------------  BRING IN OFFENCE DATA - RUN YOUR OWN OFFENCE DATA CAPTURING EVERYTHING;
Offences = pd.read_excel("s3://alpha-omppg/Mental Health/2023/Raw Data/Offence_all.xls")
Offences = Offences.replace("–","-")

#Offences =Offences.sort_values(by=['FILE_REFERENCE','PRISON_NUMBER','DATE_OF_HOSPITAL_ORDER','OFFENCE_DESCRIPTION','AUTHORITY_FOR_DETENTION_DESCRIPTION'])
#Offences[Offences.duplicated(['FILE_REFERENCE','PRISON_NUMBER','DATE_OF_HOSPITAL_ORDER','OFFENCE_DESCRIPTION'],keep=False)]

Offences.head()

len(rlv_Auths)

query2 = """SELECT a.*, 
                  b.OFFENCE_DESCRIPTION, 
                  b.OFFENCE_GROUP_DESCRIPTION
                  
            FROM rlv_Auths AS a LEFT JOIN Offences AS b
            
            ON  (
                    (a.FILE_REFERENCE = b.FILE_REFERENCE  and a.FILE_REFERENCE IS NOT NULL) OR
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)
                ) AND
                (a.DATE_OF_HOSPITAL_ORDER = b.DATE_OF_HOSPITAL_ORDER AND a.DATE_OF_HOSPITAL_ORDER IS NOT NULL) AND
                (a.AUTHORITY_FOR_DETENTION_DESCRIPTION = b.AUTHORITY_FOR_DETENTION_DESCRIPTION AND a.AUTHORITY_FOR_DETENTION_DESCRIPTION IS NOT NULL) """

rlv_Auth_off = duckdb.sql(query2).df()
len(rlv_Auth_off) # 4403

    # Resolve missing offence cases
missing_offence = rlv_Auth_off[rlv_Auth_off['OFFENCE_DESCRIPTION'].isna()]
len(missing_offence) # 1
missing_offence

rlv_Auth_off['OFFENCE_DESCRIPTION'].value_counts(dropna=False)
rlv_Auth_off['OFFENCE_GROUP_DESCRIPTION'].value_counts(dropna=False)

#********************* JUST PRECESSING for HELEN************
pop_off.head()
pop_off.sort_values(by=['FILE_REFERENCE','DATE_OF_HOSPITAL_ORDER',])

#*******************************************************
missing_offence = missing_offence.drop(['OFFENCE_DESCRIPTION',  'OFFENCE_GROUP_DESCRIPTION'], axis=1)

query3 = """SELECT a.*, 
                  b.OFFENCE_DESCRIPTION, 
                  b.OFFENCE_GROUP_DESCRIPTION
                  
            FROM missing_offence AS a LEFT JOIN Offences AS b
            
            ON  (
                    (a.FILE_REFERENCE = b.FILE_REFERENCE  and a.FILE_REFERENCE IS NOT NULL) OR
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL)
                ) AND
                (a.DATE_OF_HOSPITAL_ORDER = b.DATE_OF_HOSPITAL_ORDER AND a.DATE_OF_HOSPITAL_ORDER IS NOT NULL) """


missing_offence2 = duckdb.sql(query3).df()
len(missing_offence2)

rlv_Auth_off_2 = pd.concat([rlv_Auth_off[~rlv_Auth_off['OFFENCE_DESCRIPTION'].isna()], missing_offence2],axis = 0,ignore_index=True)
len(rlv_Auth_off_2) # 4408


rlv_Auth_off_2[rlv_Auth_off_2['OFFENCE_DESCRIPTION'].isna()] # 1

#----------------------------------  deduplicate offences

rlv_Auth_off_2 = rlv_Auth_off_2.sort_values(by=['FILE_REFERENCE','PRISON_NUMBER','DATE_OF_HOSPITAL_ORDER','OFFENCE_DESCRIPTION','AUTHORITY_FOR_DETENTION_DESCRIPTION'])
rlv_Auth_off_2[rlv_Auth_off_2.duplicated(['FILE_REFERENCE','PRISON_NUMBER','DATE_OF_HOSPITAL_ORDER','OFFENCE_DESCRIPTION'],keep=False)] # wow, none

#----------------------------------  breakdown all offences

rlv_Auth_off_2['OFFENCE_DESCRIPTION'].value_counts(dropna=False).to_excel('helen.xlsx')
rlv_Auth_off_2.drop_duplicates(['FILE_REFERENCE','OFFENCE_GROUP_DESCRIPTION'])['OFFENCE_GROUP_DESCRIPTION'].value_counts(dropna=False).to_excel('helen.xlsx')

rlv_Auth_off_2[rlv_Auth_off_2['AUTHORITY_FOR_DETENTION_DESCRIPTION']=='S37/41 - MHA 1983 - Hospital Order']['OFFENCE_DESCRIPTION'].value_counts(dropna=False).to_excel('helen.xlsx')

rlv_Auth_off_2.drop_duplicates(['FILE_REFERENCE','OFFENCE_GROUP_DESCRIPTION'])[rlv_Auth_off_2.drop_duplicates(['FILE_REFERENCE','OFFENCE_GROUP_DESCRIPTION'])['AUTHORITY_FOR_DETENTION_DESCRIPTION']=='S37/41 - MHA 1983 - Hospital Order']['OFFENCE_GROUP_DESCRIPTION'].value_counts(dropna=False).to_excel('helen.xlsx')

rlv_Auth_off_2[~(rlv_Auth_off_2['AUTHORITY_FOR_DETENTION_DESCRIPTION']=='S37/41 - MHA 1983 - Hospital Order')]['OFFENCE_DESCRIPTION'].value_counts(dropna=False).to_excel('helen.xlsx')

rlv_Auth_off_2.drop_duplicates(['FILE_REFERENCE','OFFENCE_GROUP_DESCRIPTION'])[~(rlv_Auth_off_2.drop_duplicates(['FILE_REFERENCE','OFFENCE_GROUP_DESCRIPTION'])['AUTHORITY_FOR_DETENTION_DESCRIPTION']=='S37/41 - MHA 1983 - Hospital Order')]['OFFENCE_GROUP_DESCRIPTION'].value_counts(dropna=False).to_excel('helen.xlsx')


#----------------------------------  MOST SERIOUS OFFENCE
ref_offences = pd.read_excel("s3://alpha-omppg/Mental Health/Reference/Reference.xls", sheet_name="Offences_use")
ref_offences = ref_offences.replace("–","-")
ref_offences['INDEX_OFFENCE_DESCRIPTION2'] = ref_offences['INDEX_OFFENCE_DESCRIPTION'].astype(str).str.upper().str.strip()

rlv_Auth_off_2['OFFENCE_DESCRIPTION2'] = rlv_Auth_off_2['OFFENCE_DESCRIPTION'].astype(str).str.upper().str.strip()

len(rlv_Auth_off_2) #4408

query4 = """SELECT a.*, 
                  b.*
                  
            FROM rlv_Auth_off_2 AS a LEFT JOIN ref_offences AS b
            
            ON  a.OFFENCE_DESCRIPTION2 = b.INDEX_OFFENCE_DESCRIPTION2  AND a.OFFENCE_DESCRIPTION2 IS NOT NULL """

most_ser = duckdb.sql(query4).df()
len(most_ser) # 4408
most_ser.head()

most_ser[most_ser['offencegrp_new'].isna()] # only 1

(most_ser['AUTHORITY_FOR_DETENTION_DESCRIPTION']=='S37/41 - MHA 1983 - Hospital Order').sum()
(rlv_Auth_off_2['AUTHORITY_FOR_DETENTION_DESCRIPTION']=='S37/41 - MHA 1983 - Hospital Order').sum()

#----------------------------------  breakdown per my groupings

most_ser = most_ser.sort_values(['FILE_REFERENCE', 'Rank', 'OFFID'])

most_ser.drop_duplicates(['FILE_REFERENCE','offencegrp_new'])['offencegrp_new'].value_counts(dropna=False).to_excel('helen.xlsx')

most_ser.drop_duplicates(['FILE_REFERENCE','offencegrp_new'])[most_ser.drop_duplicates(['FILE_REFERENCE','offencegrp_new'])['AUTHORITY_FOR_DETENTION_DESCRIPTION']=='S37/41 - MHA 1983 - Hospital Order']['offencegrp_new'].value_counts(dropna=False).to_excel('helen.xlsx')

most_ser.drop_duplicates(['FILE_REFERENCE','offencegrp_new'])[~(most_ser.drop_duplicates(['FILE_REFERENCE','offencegrp_new'])['AUTHORITY_FOR_DETENTION_DESCRIPTION']=='S37/41 - MHA 1983 - Hospital Order')]['offencegrp_new'].value_counts(dropna=False).to_excel('helen.xlsx')

#----------------------------------  Keep most serious offence only and breakdown per my groupings
most_ser = most_ser.sort_values(['FILE_REFERENCE', 'Rank', 'OFFID'])

most_ser2 = most_ser.drop_duplicates('FILE_REFERENCE', keep='first').copy()
len(most_ser2) # 2791

    #-  breakdown all offences

most_ser2['OFFENCE_DESCRIPTION'].value_counts(dropna=False).to_excel('helen.xlsx')
most_ser2.drop_duplicates(['FILE_REFERENCE','offencegrp_new'])['offencegrp_new'].value_counts(dropna=False).to_excel('helen.xlsx')

most_ser2[most_ser2['AUTHORITY_FOR_DETENTION_DESCRIPTION']=='S37/41 - MHA 1983 - Hospital Order']['OFFENCE_DESCRIPTION'].value_counts(dropna=False).to_excel('helen.xlsx')
most_ser2[most_ser2['AUTHORITY_FOR_DETENTION_DESCRIPTION']=='S37/41 - MHA 1983 - Hospital Order']['offencegrp_new'].value_counts(dropna=False).to_excel('helen.xlsx')

most_ser2[~(most_ser2['AUTHORITY_FOR_DETENTION_DESCRIPTION']=='S37/41 - MHA 1983 - Hospital Order')]['OFFENCE_DESCRIPTION'].value_counts(dropna=False).to_excel('helen.xlsx')
most_ser2[~(most_ser2['AUTHORITY_FOR_DETENTION_DESCRIPTION']=='S37/41 - MHA 1983 - Hospital Order')]['offencegrp_new'].value_counts(dropna=False).to_excel('helen.xlsx')
