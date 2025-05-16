"""
Statistics around when IPP offenders are getting recalled (i.e how long have they spent in the community before they are recalled) - preferably in graphical form.

Is it possible to provide the data on all IPP recalls (included those on first release and those on re-release) in 2024. If not please can the latest full year period be provided and can this be broken up into the following stages of release:
0-3 months
3-6 months
6-9 months
9-12 months
Upto 2 years
Upto 3 years
Upto 4 years
Upto 5 years
5 years +

As per the request please can this be provided in a chart?

"""
# Import modules
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from lifelines import KaplanMeierFitter

from itables import show

%config InlineBackend.figure_format = 'svg'

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.set_option('display.max_colwidth', None)

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Obtain IPP release data from OMSQ file

ipp_releases = pd.read_parquet("s3://alpha-omppg/isp_releases/final-data/isp_releases_2024q3.parquet")

# keep only IPP releases from 2015

ipp_releases = ipp_releases[ipp_releases['CUSTODY_TYPE_DESCRIPTION'].isin(['DPP','IPP'])]

ipp_releases = ipp_releases[ipp_releases['RELEASE_DATE'].dt.year > 2014]
len(ipp_releases) #7831

ipp_releases.head()

# Normalize next recall date

ipp_releases['NEXT_LICENCE_REVOKE_DATE'] = ipp_releases['NEXT_LICENCE_REVOKE_DATE'].dt.normalize()

# Create event date to signify recall date or end of study date for those not recalled yet

ipp_releases['EVENT_DATE'] = ipp_releases['NEXT_LICENCE_REVOKE_DATE'].fillna(pd.Timestamp('2024-09-30'))

# Create a censor variable

ipp_releases['EVENT'] = ipp_releases['NEXT_LICENCE_REVOKE_DATE'].notnull().astype(int)

# Calculate months to recall - all release dates are before recall date (if recalled)

recall_mask = ipp_releases['RELEASE_DATE'] <= ipp_releases['EVENT_DATE'] # to guard agains improper r

ipp_releases['MONTHS_TO_RECALL_NEW'] = np.nan

ipp_releases.loc[recall_mask,'MONTHS_TO_RECALL_NEW'] = (ipp_releases['EVENT_DATE'] - ipp_releases['RELEASE_DATE']).dt.days/30.44

# Rearrange columns

key_columns = ['NOMS_ID', 'FAMILY_NAME', 'RELEASE_DATE','NEXT_LICENCE_REVOKE_DATE','EVENT_DATE','MONTHS_TO_RECALL_NEW','EVENT','MONTHS_UNTIL_RECALL','CUSTODY_TYPE_DESCRIPTION','NEXT_RECALL_FURTHER_CHARGE','FIRST_NAMES']

ipp_releases = ipp_releases[key_columns + [col for col in ipp_releases.columns if col not in key_columns]]

ipp_releases.head(10)
ipp_releases.tail(10)

ipp_releases['RELEASE_DATE'].max()

# Replicate Kaplan-Meier for 2015 to 2019 first time releases only to check if approach matches SAS previously.
# Report: matches nicely!!!!!!!!!!!!!!!

replicate_mask = (ipp_releases['RELEASE_TYPE']=='First Release') & (ipp_releases['RELEASE_DATE'].dt.year <= 2019)

kmf = KaplanMeierFitter()

kmf.fit(durations=ipp_releases[replicate_mask]['MONTHS_TO_RECALL_NEW'], event_observed=ipp_releases[replicate_mask]['EVENT'])

# Define time points in months and caculate probabilities

time_points = [3, 6, 9, 12, 24, 36, 48, 60,np.inf]

surv_probs = kmf.survival_function_at_times(time_points)

surv_probs = surv_probs.values.flatten()  # Get as an array for easier manipulation

recall_cumulative = 1 - surv_probs
recall_cumulative # they match what was previously obtained

# Fit the Kaplan-Meier estimator for all releases (first and rereleases) from 2015 to 30 September 2024

kmf = KaplanMeierFitter()
kmf.fit(durations=ipp_releases['MONTHS_TO_RECALL_NEW'], event_observed=ipp_releases['EVENT'])

time_points = [3, 6, 9, 12, 24, 36, 48, 60,np.inf]

surv_probs = kmf.survival_function_at_times(time_points)
surv_probs = surv_probs.values.flatten()  # Get as an array for easier manipulation

recall_cumulative = 1 - surv_probs
recall_cumulative # they match what was previously obtained

# For interval-specific proportions:
# 0-3 months: recall_cumulative[0]
# 3-6 months: recall_cumulative[1] - recall_cumulative[0]
# 6-9 months: recall_cumulative[2] - recall_cumulative[1]
# 9-12 months: recall_cumulative[3] - recall_cumulative[2]
# Similarly for the longer intervals, you can either report cumulative or interval differences.

# Create table to sent to Excel

time_labels = [f"{int(tp)} months" if not np.isinf(tp) else "∞" for tp in time_points]

# Create a DataFrame
df_table = pd.DataFrame({
    "Time Point": time_labels,
    "Survival Probability": surv_probs,
    "Cumulative Recall Probability": recall_cumulative
})

# Display the DataFrame
show( df_table, buttons=["excelHtml5"])

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

plt.savefig("ipp_recalls.svg",bbox_inches='tight',pad_inches=0) 
plt.show()



