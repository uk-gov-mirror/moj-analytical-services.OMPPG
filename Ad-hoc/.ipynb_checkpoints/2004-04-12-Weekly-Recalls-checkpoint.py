""" 
GOAL: Count of weekly recalls in a year
By Eric Nyame, 12/04/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np

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

# Concatenate 2022 and 2023 recall data

years = [2022, 2023]
quarters =['q1','q2','q3','q4']

recalls = pd.DataFrame() # empty data frame

for i in years:
    for j in quarters:
        
        # 2023 doesn't have a q4 yet, so skip 2023q4
        if (i == 2023) and (j =='q4'): 
            break
            
        # read each quarter's dataset
        rec = pd.read_sas(f"s3://alpha-omppg/Recalls/Final Data/SAS/recalls_final_{i}{j}.sas7bdat", encoding='latin1')
        
        # uppercase the colums
        rec.columns = rec.columns.str.upper()
        
        # concatenate with recalls dataset to expand recalls dataset
        recalls = pd.concat([recalls,rec],axis = 0, ignore_index= True)
        
# check number of rows and view first 5 rows
len(recalls) #44239
recalls.head()


# Create a 'Year-Week' column formatted as '2022W1', '2022W2', etc.
recalls['Year_Week'] = recalls['LICENCE_REVOKE_DATE'].dt.isocalendar().year.astype(str)  + 'W' + recalls['LICENCE_REVOKE_DATE'].dt.isocalendar().week.astype(str).str.zfill(2)

recalls.head()

# Group by 'Year-Week' and count the occurrences - the only approach that seems to work for counting day of the week
# starting from 1 on 1 January of each year

    # first create count of each week, where the counting resets to 1 on 1 January
recalls['week_of_year'] = recalls['LICENCE_REVOKE_DATE'].apply(lambda x: int(x.strftime("%W"))+1)

    # concatenate to create something like 2022W02, etch. .zfill(2) pads 2022W1 to get 2022W01 for correct sorting.
recalls['Year_Week'] = recalls['LICENCE_REVOKE_DATE'].dt.year.astype(str) + 'W' + recalls['week_of_year'].astype(str).str.zfill(2)


# check border days 1 January and 31 December as well as cut off date 30 Sep for 2023

np.sort(recalls[recalls['Year_Week']== '2022W01']['LICENCE_REVOKE_DATE'].unique()) # 2 days, count from Monday to Sunday for 1 week, restarting from first day of each year
np.sort(recalls[recalls['Year_Week']== '2022W02']['LICENCE_REVOKE_DATE'].unique()) # 7 days
np.sort(recalls[recalls['Year_Week']== '2022W53']['LICENCE_REVOKE_DATE'].unique()) # 6 days

np.sort(recalls[recalls['Year_Week']== '2023W01']['LICENCE_REVOKE_DATE'].unique()) # 1 day, count from Monday to Sunday for 1 week, restarting from first day of each year
np.sort(recalls[recalls['Year_Week']== '2023W02']['LICENCE_REVOKE_DATE'].unique()) # 7 days
np.sort(recalls[recalls['Year_Week']== '2023W40']['LICENCE_REVOKE_DATE'].unique()) # 6 days

# count by week and send
recalls.groupby('Year_Week').size().reset_index(name='count')
