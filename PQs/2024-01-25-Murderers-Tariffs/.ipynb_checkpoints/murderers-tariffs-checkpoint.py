""" 
GOAL: DETERMINE THE AVERAGE TARIFF FOR MURDER CONVICTIONS
By Eric Nyame, 02/02/2024
"""

# Import Packages

import pandas as pd
import numpy as np
import duckdb
from dateutil.relativedelta import relativedelta
import XlsxWriter

# Set display options

pd.options.display.max_columns = None
pd.options.display.max_rows = None

# Ensures no wrapping of cell contents

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Import PPUD ISP cases

ispPPUD = pd.read_excel("s3://alpha-omppg/ISP Population/PPUD/2023Q4/PPUD_ISP_2023Q4.xls")
wlPPUD = pd.read_excel("s3://alpha-omppg/ISP Population/PPUD/2023Q4/PPUD_WholeLife_2023Q4.xls")

ispPPUD.head()
wlPPUD.head()

# Remove duplicates - all columns

ispPPUD.drop_duplicates(inplace=True)
wlPPUD.drop_duplicates(inplace=True)

# Check date fields and ensure every date field has type 'datetime' 

ispPPUD.dtypes
wlPPUD.dtypes

# Convert wrong type of object to datetime

ispPPUD['INDEX_OFFENCE_DATE'] = pd.to_datetime(ispPPUD['INDEX_OFFENCE_DATE'], errors ='coerce') 
ispPPUD['LATEST_RELEASE_DATE'] = pd.to_datetime(ispPPUD['LATEST_RELEASE_DATE'], errors ='coerce')

ispPPUD.dtypes

# Date ranges of datetime fields should be within datetime bounds in pandas

datetime_cols = ispPPUD.select_dtypes(include =['datetime64[ns]']).columns

for col in datetime_cols:
    yr_min = ispPPUD[col].min()
    yr_max = ispPPUD[col].max()
    print([yr_min,yr_max,col])

# If any datetime is out of the bounds below, then run the code below to find the rows

# min_ts = pd.Timestamp.min
# max_ts = pd.Timestamp.max
# out_of_bounds_mask = pd.Series([False] * len(ispPPUD))
# for col in ispPPUD.select_dtypes(include=['datetime64[ns]']).columns:
#    out_of_bounds_mask |= (ispPPUD[col] < min_ts) | (ispPPUD[col] > max_ts)
# out_of_bounds_df = ispPPUD[out_of_bounds_mask]
# out_of_bounds_df

# Add whole life flag to PPUD ISP data - use duckDB

query =  """SELECT a.*, 
                   b.WHOLE_LIFE
            FROM ispPPUD AS a LEFT JOIN 
                (SELECT DISTINCT PRISON_NUMBER, DOS,NOMS_ID,FILE_REFERENCE,WHOLE_LIFE FROM wlPPUD) AS b 
            ON  (
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) OR
                    (a.NOMS_ID = b.NOMS_ID AND a.NOMS_ID IS NOT NULL)
                ) AND a.DOS = b.DOS AND a.DOS IS NOT NULL"""

ispPPUD_MATCHED = duckdb.sql(query).df()
ispPPUD_MATCHED.head()

# Check how murder is entered as an offence

murder_mask = ispPPUD_MATCHED['INDEX_OFFENCE_DESCRIPTION'].str.contains('Murder', na = False, case = False,)

ispPPUD_MATCHED[murder_mask]['INDEX_OFFENCE_DESCRIPTION'].value_counts().to_frame()

# Murder cases from 2000 onwards, no whole life orders

Murderers = ispPPUD_MATCHED[
                            (ispPPUD_MATCHED['INDEX_OFFENCE_DESCRIPTION'] == 'Murder') & \
                            (ispPPUD_MATCHED['DOS'].dt.year >= 2000) & \
                            (ispPPUD_MATCHED['WHOLE_LIFE'] != True)
                           ].copy()

# Calculate tariff_days, tariff_months and tariff_years

Murderers['TARIFF_DAYS'] = Murderers.apply(
                                            lambda row: (row['TARIFF_EXPIRY_DATE'] - row['DOS']).days \
                                            if (row['DOS'] < row['TARIFF_EXPIRY_DATE']) else pd.NA,
                                            axis = 1
                                          )

    # Define a function for calculating difference in months and years
    
def calculate_months_years(row):
    if pd.isnull(row['DOS']) or pd.isnull(row['TARIFF_EXPIRY_DATE']):
        return pd.NA, pd.NA # returns values to be assigned to tariff_months and tariff_years
    elif row['DOS'] >= row['TARIFF_EXPIRY_DATE']:
        return pd.NA,pd.NA  # Handle cases where DOS is on or after TARIFF_EXPIRY_DATE
    else:
        delta = relativedelta(row['TARIFF_EXPIRY_DATE'], row['DOS'])
        total_years = delta.years
        total_months = delta.years * 12 + delta.months
        return  total_months, total_years # returns values to be assigned to tariff_months and tariff_years

    # Apply the function to the DataFrame to create tariff_months and tariff_years
Murderers[['TARIFF_MONTHS', 'TARIFF_YEARS']] = Murderers.apply(
                                                                lambda row: calculate_months_years(row), 
                                                                axis=1, 
                                                                result_type='expand'
                                                              )

# Take a look
tariff_columns = ['TARIFF_DAYS', 'TARIFF_MONTHS', 'TARIFF_YEARS']

Murderers[tariff_columns + [col for col in Murderers.columns if col not in tariff_columns]].head()


# We should calculated values all being non-negative integers

for col in tariff_columns:
    print([Murderers[col].isna().sum(),(Murderers[col] < 0).sum(), col])

# Tabulate

    # Send Results to Excel.
writer = pd.ExcelWriter('murder_tariffs.xlsx', engine='xlsxwriter')

def nmiss(x):
    return x.isna().sum()

    # Perform the aggregation for TARIFF_DAYS, TARIFF_MONTHS, TARIFF_YEARS

for var in ['TARIFF_DAYS', 'TARIFF_MONTHS', 'TARIFF_YEARS']:
    print(f"\nStatistics for {var}:")
    result = Murderers.groupby( Murderers['DOS'].dt.year)[var].agg(['count', 'min', 'median', 'mean', 'max']).rename(columns={'count': 'N'})
    result['NMISS'] = Murderers.groupby( Murderers['DOS'].dt.year)[var].apply(lambda x: x.isna().sum())
    result.round(2).to_excel(writer, sheet_name= var)
    display(result.round(2))

    # Save and close excel file
writer.save()
