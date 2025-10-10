"""
The relative proportions of lifer and IPP released from closed and open conditions who do not need to be recalled subsequently (ie, to show whether a period in open conditions generally leads to more successful resettlement). Please come back to me if any of this is unclear.

"""
# Import modules
import pandas as pd
import numpy as np
import sys
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import duckdb

from lifelines import KaplanMeierFitter

from itables import show

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
#importlib.reload(prepareMatch)
import openMatch


%config InlineBackend.figure_format = 'svg'

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.set_option('display.max_colwidth', None)

# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #
        
%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Obtain IPP release data from OMSQ file

isp_releases = pd.read_excel("s3://alpha-omppg/isp_releases/PPUD/PPUD_Releases_2025Q2.xls")

# clean release data
isp_releases.select_dtypes(include=['object']).dtypes
isp_releases = isp_releases.drop(columns=['LATEST_RELEASE_DATE'])

isp_releases.select_dtypes(include=['datetime64']).dtypes
isp_releases.info()
          
strip_blanks(isp_releases)

    
#---------------------------------- Remove Test cases
    # Check 'test' cases and remove
isp_releases[isp_releases['FAMILY_NAME'].astype(str).str.contains('Test|Lumen',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

isp_releases[isp_releases['FIRST_NAMES'].astype(str).str.contains('Test|Lumen',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']]

Test_Case_Mask =  (   (isp_releases['FAMILY_NAME'].astype(str).str.contains('Test',case = False,na = False)) |
                      (isp_releases['FIRST_NAMES'].astype(str).str.contains('Test',case = False,na = False))
                  ) & (isp_releases['FILE_REFERENCE'] != 'T18122')

# releases[Test_Case_Mask][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 24 cases

isp_releases = isp_releases[~Test_Case_Mask]

isp_releases.shape  # 21883

    # Check 'case' cases and remove
isp_releases[isp_releases['FAMILY_NAME'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 7

isp_releases[isp_releases['FIRST_NAMES'].str.contains('Case',case = False,na = False)][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] # 7

    # Check 'digit' cases - these are normally good and shoulbe untouched
isp_releases[isp_releases['FAMILY_NAME'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 
isp_releases[isp_releases['FIRST_NAMES'].str.contains(r'\d')][['FILE_REFERENCE','FAMILY_NAME','FIRST_NAMES']] 

#---------------------------------- Drop duplicates
isp_releases = isp_releases.drop_duplicates()
isp_releases.shape # 21883

#---------------------------------- Release date must not be before dos

    # check range of years for release date and dos
#isp_releases['RELEASE_DATE'].dt.year.value_counts(dropna = False).sort_index()
#isp_releases['DOS'].dt.year.value_counts(dropna = False).sort_index() # some missing data

    # note some entries with missing DOS
#isp_releases[isp_releases['DOS'].isna()].head()[['FILE_REFERENCE','FAMILY_NAME','DOS','RELEASE_DATE']]

    # remove release dates less than dos, excluding missing dos and release cases

isp_releases = isp_releases[(isp_releases['RELEASE_DATE'] >= isp_releases['DOS']) |
                    (isp_releases['DOS'].isna()) |
                    (isp_releases['RELEASE_DATE'].isna())
                   ]
isp_releases.shape # 21883

# Keep releases from 2015

isp_releases = isp_releases[isp_releases['RELEASE_DATE'].dt.year > 2014]

isp_releases.shape # 14579
'''
isp_releases['RELEASED_UNDER_DESCRIPTION'].value_counts(dropna=False)
isp_releases['RELEASE_TYPE_DESCRIPTION'].value_counts(dropna=False)

isp_releases['CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)
'''
# isp_releases = isp_releases[isp_releases['CUSTODY_TYPE_DESCRIPTION'].isin(['DPP','IPP']) | (isp_releases['RELEASED_UNDER_DESCRIPTION']== 'IPP Licence [*]')]

isp_releases.head()

# Bring in Recall data
isp_recalls = pd.read_excel("s3://alpha-omppg/Recalls/PPUD/ISP/PPUD_ISP_Recalls_2025Q2.xls")
strip_blanks(isp_recalls)

isp_recalls['LICENCE_REVOKE_DATE'] = isp_recalls['LICENCE_REVOKE_DATE'].dt.normalize()
isp_recalls.head()

# Match Releases and Recalls
query = """SELECT a.*, 
                b.LICENCE_REVOKE_DATE AS NEXT_LICENCE_REVOKE_DATE, 
                b.RELEASE_BEFORE_RECALL,
                b.RECALL_REASON_DESCRIPTIONS,
                b.CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION
                
            FROM isp_releases AS a LEFT JOIN isp_recalls AS b
            
            ON  (a.RELEASE_DATE <= b.LICENCE_REVOKE_DATE) AND
                (
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL)
                )"""


matched = duckdb.sql(query).df()
matched.shape # 20201

matched = matched.sort_values(by=['PRISON_NUMBER','FILE_REFERENCE','RELEASE_DATE','NEXT_LICENCE_REVOKE_DATE'])

key_columns = ['NOMS_ID', 'FAMILY_NAME', 'RELEASE_DATE','RELEASE_BEFORE_RECALL','NEXT_LICENCE_REVOKE_DATE','CUSTODY_TYPE_DESCRIPTION','CUSTODY_TYPE_AT_TIME_OF_RECALL_DESCRIPTION','FIRST_NAMES','RELEASED_UNDER_DESCRIPTION']

matched = matched[key_columns + [col for col in matched.columns if col not in key_columns]]
matched.head(10)

isp_releases_final = matched.drop_duplicates(subset=['PRISON_NUMBER','FILE_REFERENCE','RELEASE_DATE'], keep ='first')
isp_releases_final.head(5)
isp_releases_final.shape # 14428

bad_match_mask = (isp_releases_final['RELEASE_DATE'] != isp_releases_final['RELEASE_BEFORE_RECALL']) & (~ isp_releases_final['RELEASE_BEFORE_RECALL'].isna()) 

sum(bad_match_mask) # 60
isp_releases_final[bad_match_mask].head()

bad_match_mask_2 = (isp_releases_final['RELEASE_DATE'] != isp_releases_final['RELEASE_BEFORE_RECALL']) & (~ isp_releases_final['RELEASE_BEFORE_RECALL'].isna()) & (isp_releases_final['NEXT_LICENCE_REVOKE_DATE'] > isp_releases_final['RELEASE_BEFORE_RECALL'])

sum(bad_match_mask_2) # 60
isp_releases_final[bad_match_mask_2]

isp_releases_final.loc[bad_match_mask_2,'RELEASE_DATE'] =isp_releases_final[bad_match_mask_2][["RELEASE_DATE", "RELEASE_BEFORE_RECALL"]].max(axis=1)

bad_match_mask_3 = (isp_releases_final['RELEASE_DATE'] != isp_releases_final['RELEASE_BEFORE_RECALL']) & (isp_releases_final['RELEASE_DATE'] < isp_releases_final['RELEASE_BEFORE_RECALL']) 
sum(bad_match_mask_3) # 0

isp_releases_final.shape  # 14428

# Create event date to signify recall date or end of study date for those not recalled yet

isp_releases = isp_releases_final.copy()

cutOffDate = pd.Timestamp('2024-12-31')

isp_releases.loc[isp_releases['NEXT_LICENCE_REVOKE_DATE'] > cutOffDate, 'NEXT_LICENCE_REVOKE_DATE'] = pd.NaT

isp_releases = isp_releases[isp_releases['RELEASE_DATE'] <= cutOffDate]

isp_releases['EVENT_DATE'] = isp_releases['NEXT_LICENCE_REVOKE_DATE'].fillna(pd.Timestamp(cutOffDate))

# Create a censor variable

isp_releases['EVENT'] = isp_releases['NEXT_LICENCE_REVOKE_DATE'].notnull().astype(int)

# Determine first releases

isp_releases['FIRST_RELEASE'] = (isp_releases['RELEASE_DATE'] == isp_releases.groupby(['PRISON_NUMBER','FILE_REFERENCE'])['RELEASE_DATE'].transform('min')).astype(int)

isp_releases.head(10)
# Calculate months to recall - all release dates are before recall date (if recalled)

recall_mask = isp_releases['RELEASE_DATE'] <= isp_releases['EVENT_DATE'] # to guard against improper r

isp_releases['MONTHS_TO_RECALL_NEW'] = np.nan

isp_releases.loc[recall_mask,'MONTHS_TO_RECALL_NEW'] = (isp_releases['EVENT_DATE'] - isp_releases['RELEASE_DATE']).dt.days/30.44

# Rearrange columns
isp_releases['NEXT_RECALL_FURTHER_CHARGE'] = np.where(isp_releases['RECALL_REASON_DESCRIPTIONS'].str.contains('Further',case=False,na=False),1,0)

isp_releases.head()

key_columns = ['NOMS_ID', 'FAMILY_NAME', 'RELEASE_DATE','NEXT_LICENCE_REVOKE_DATE','EVENT_DATE','MONTHS_TO_RECALL_NEW','EVENT','CUSTODY_TYPE_DESCRIPTION','NEXT_RECALL_FURTHER_CHARGE','FIRST_RELEASE','FIRST_NAMES']

isp_releases = isp_releases[key_columns + [col for col in isp_releases.columns if col not in key_columns]]

isp_releases.head(10)
isp_releases.tail(10)

isp_releases['CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

wrongCustody = ['EDS','Determinate','SOPC','EPP','DCR']
goodReleaseType = ['On Licence','Parole Board Release','Parole Board (PAT)','SofS Executive Release (PPCS)','Migrated']

isp_releases = isp_releases[~isp_releases['CUSTODY_TYPE_DESCRIPTION'].isin(wrongCustody)]
isp_releases = isp_releases[isp_releases['RELEASE_TYPE_DESCRIPTION'].isin(goodReleaseType)]

isp_releases.shape # 13481

isp_releases['ISP_TYPE'] ='Life'
isp_releases.loc[isp_releases['CUSTODY_TYPE_DESCRIPTION'].isin(['IPP','DPP']),'ISP_TYPE'] = 'IPP'

isp_releases['ISP_TYPE'].value_counts()

isp_releases['RELEASE_TYPE_DESCRIPTION'].value_counts()

isp_releases['RELEASE_DATE'].max()
isp_releases['NEXT_LICENCE_REVOKE_DATE'].max()
isp_releases['RELEASED_FROM_DESCRIPTION'].value_counts(dropna=False)
#---------------------------------- Add release conditions
# Import Data
openPrisons = pd.read_excel("s3://alpha-omppg/Supporting Data/Open Prisons.xls",sheet_name='Open Prisons')

# openPrisons.tail()
# openPrisons.info()

# Change column headers to upper case
openPrisons.columns = openPrisons.columns.str.upper()


# Change year of 9999 2261 as pandas can't go past April 2262
for column in openPrisons.columns:
    if openPrisons[column].dtype == object:
        openPrisons[column] = openPrisons[column].astype(str).str.replace('9999', f'{pd.Timestamp.max.year - 1}')
        
# Convert some datetimes
len(isp_releases) #13481
sum(isp_releases.duplicated()) # 3 why?

openPrisons['END'] = pd.to_datetime(openPrisons['END'])
openPrisons['TYPEEND'] = pd.to_datetime(openPrisons['TYPEEND'])

query2 = """SELECT DISTINCT a.*, 
                   b.LOCATION
            FROM isp_releases AS a LEFT JOIN openPrisons AS b
            ON  ( a.RELEASED_FROM_DESCRIPTION = b.PRISONNAME AND
                  a.RELEASE_DATE >= b.START AND
                  a.RELEASE_DATE <= b."END"
                )"""
isp_releases = duckdb.sql(query2).df()
len(isp_releases)

isp_releases.head()
isp_releases['LOCATION'].value_counts(dropna=False)
isp_releases.pivot_table(index=['RELEASED_FROM_CATEGORY_ID_DESCRIPTION','LOCATION'],aggfunc='size')

isp_releases['RELEASE_CONDITIONS'] ='Closed'
isp_releases.loc[isp_releases['LOCATION']=='All','RELEASE_CONDITIONS'] = 'Open' 

isp_releases.pivot_table(index=['RELEASE_CONDITIONS','LOCATION'],aggfunc='size')


#----------------------------------------------
# Probability time points
time_points = [3, 6, 9, 12, 24, 36, 48, 60,np.inf]
time_labels = [f"{int(tp)} months" if not np.isinf(tp) else "∞" for tp in time_points]

# For interval-specific proportions:
# 0-3 months: recall_cumulative[0]
# 3-6 months: recall_cumulative[1] - recall_cumulative[0]
# 6-9 months: recall_cumulative[2] - recall_cumulative[1]
# 9-12 months: recall_cumulative[3] - recall_cumulative[2]
# Similarly for the longer intervals, you can either report cumulative or interval differences.

# Function to calculate KM estimates
def km_isp(condition,df):
    kmf = KaplanMeierFitter()
    kmf.fit(durations=df[condition]['MONTHS_TO_RECALL_NEW'], event_observed=df[condition]['EVENT'])
    surv_probs = kmf.survival_function_at_times(time_points)
    surv_probs = surv_probs.values.flatten()  # Get as an array for easier manipulation
    recall_cumulative = 1 - surv_probs
    recall_cumulative 
    
    # Create a DataFrame
    df_table = pd.DataFrame({
        "Time Point": time_labels,
        "Survival Probability": surv_probs,
        "Cumulative Recall Probability": recall_cumulative})
    
    # Display the DataFrame
    show( df_table, buttons=["excelHtml5"])

#masks
ipp_mask = isp_releases['ISP_TYPE']=='IPP'
life_mask = isp_releases['ISP_TYPE']=='Life'
open_release_mask = isp_releases['RELEASE_CONDITIONS'] == 'Open'
closed_release_mask = isp_releases['RELEASE_CONDITIONS'] == 'Closed'
first_release_mask = isp_releases['FIRST_RELEASE']==1

# Replicate Kaplan-Meier for 2015 to 2019 first time releases only to check if approach matches SAS previously.
# Report: matches nicely!!!!!!!!!!!!!!!

replicate_mask = (isp_releases['FIRST_RELEASE']==1) & (isp_releases['RELEASE_DATE'].dt.year <= 2019)

km_isp(replicate_mask,isp_releases)

# First-releases only from 2015 to 31 December 2024
km_isp(first_release_mask,isp_releases)

# IPP first-releases only from 2015 to 31 December 2024
km_isp((first_release_mask & ipp_mask),isp_releases)

# Life first-releases only from 2015 to 31 December 2024
km_isp((first_release_mask & life_mask),isp_releases)

# Recall-releases only from 2015 to 30 September 2024
recall_release_mask = ~(first_release_mask)

km_isp(recall_release_mask,isp_releases)

# IPP recall-releases only from 2015 to 30 September 2024
ipp_recall_release_mask = (recall_release_mask) & (isp_releases['ISP_TYPE']=='IPP')

km_isp(ipp_recall_release_mask,isp_releases)

# Life recall-releases only from 2015 to 30 September 2024
life_recall_release_mask = (recall_release_mask) & (isp_releases['ISP_TYPE']=='Life')

km_isp(life_recall_release_mask,isp_releases)

# All releases (first and rereleases) from 2015 to 30 September 2024
firstAndRecall_release_mask = isp_releases['ISP_TYPE'].notna()

km_isp(firstAndRecall_release_mask,isp_releases)

# IPP All releases (first and rereleases) from 2015 to 30 September 2024
ippfirstAndRecall_release_mask = (isp_releases['ISP_TYPE'] == 'IPP')

km_isp(ippfirstAndRecall_release_mask,isp_releases)

# Life all releases (first and rereleases) from 2015 to 30 September 2024
lifefirstAndRecall_release_mask = (isp_releases['ISP_TYPE'] == 'Life')

km_isp(lifefirstAndRecall_release_mask,isp_releases)


############################################# OPEN vs CLOSED
    # All releases
# Open vs Closed All releases (first and rereleases) from 2015 to 30 September 2024
km_isp(open_release_mask,isp_releases)
km_isp(closed_release_mask,isp_releases)

# IPP Open vs Closed All releases (first and rereleases) from 2015 to 30 September 2024
km_isp((open_release_mask & ipp_mask),isp_releases)
km_isp((closed_release_mask & ipp_mask),isp_releases)

# Life Open vs Closed All releases (first and rereleases) from 2015 to 30 September 2024
km_isp((open_release_mask & life_mask),isp_releases)
km_isp((closed_release_mask & life_mask),isp_releases)

    # First Time Releases
# All
km_isp((open_release_mask & first_release_mask),isp_releases)
km_isp((closed_release_mask & first_release_mask),isp_releases)

# IPPs
km_isp((open_release_mask & ipp_mask & first_release_mask),isp_releases)
km_isp((closed_release_mask & ipp_mask & first_release_mask),isp_releases)

# Life
km_isp((open_release_mask & life_mask & first_release_mask),isp_releases)
km_isp((closed_release_mask & life_mask & first_release_mask),isp_releases)

     # Recall Time Releases
# All
km_isp((open_release_mask & ~first_release_mask),isp_releases)
km_isp((closed_release_mask & ~first_release_mask),isp_releases)

# IPPs
km_isp((open_release_mask & ipp_mask & ~first_release_mask),isp_releases)
km_isp((closed_release_mask & ipp_mask & ~first_release_mask),isp_releases)

# Life
km_isp((open_release_mask & life_mask & ~first_release_mask),isp_releases)
km_isp((closed_release_mask & life_mask & ~first_release_mask),isp_releases)





# Plot probabilities
    # For plotting, we'll remove the np.inf value.

    # Original time points (excluding np.inf) and associated cummulative probability
    # We will handle that separately
    
time_points = [3, 6, 9, 12, 24, 36, 48, 60]
time_points = [0] + time_points # prepend with 0 time point

cummulative_probs = recall_cumulative[:-1]
cummulative_probs = np.append(0,cummulative_probs) # prepend with 0 probability

    # Survival probability beyond 60 (the np.inf value)
recall_beyond = recall_cumulative[-1]

# Plot step function
plt.figure(figsize=(7, 5))

plt.step(time_points, cummulative_probs, where='pre', label='Cummulative recall probability')

# plt.step(time_points,interval_probs, where='pre', label='interval recall probability')
#plt.plot(time_points, cummulative_probs, 'o', color='blue')

# Extend the horizontal line beyond 60 to, say, 80 months
plt.hlines(recall_beyond, 60, 80, colors='red', linestyles='dashed', label='Estimate beyond 60 months')

plt.xlabel('Months from release')
plt.ylabel('Cummulative recall probability')
plt.title('Estimated recall probability - IPPs (2015- September 2024)')
plt.xticks([0, 3, 6, 9, 12, 24, 36, 48, 60],
          ['0', '3', '6', '9', '12', '24', '36', '48', '60'])  # Custom ticks

plt.ylim(0, 1)
plt.xlim(left=0) # enjoyrs x axis starts fro 0
plt.grid(True,linestyle='--', linewidth=0.5)
plt.legend()

#plt.savefig("isp_recalls.svg",bbox_inches='tight',pad_inches=0) 
plt.show()



