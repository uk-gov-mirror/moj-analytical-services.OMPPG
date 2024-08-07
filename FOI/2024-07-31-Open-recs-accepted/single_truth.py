""" 
GOAL: PRODUCE RECALL TABLES FOR OMSQ.
By Eric Nyame, 17/04/2024
"""

#---------------------------------- Import Packages

import pandas as pd
# from pandas.api.types import CategoricalDtype
import numpy as np
import sys
import os

import duckdb
import importlib

# openpyxl
# from openpyxl import Workbook, load_workbook
# from openpyxl.styles import Font, Alignment
# from openpyxl.utils import get_column_letter

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
# import prepareMatch
# importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
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

# function to remove trailing and leading blanks
def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x) #

        
        # Period variables
qtr = 1 # 1:Jan-Mar, 2:Apr-Jun, 3:Jul-Sep, 4:Oct-Dec
year = 2024 # Enter the year being run in 4 digit format


# Folder containing the Excel files
os.getcwd()
folder_path = os.getcwd()

# List all files in the folder
# os.listdir(folder_path)
file_list = [f for f in os.listdir(folder_path) if f.endswith('.xlsx')]

# Initialize an empty list to hold the data

data = []

# Loop through the files and read the necessary data
for file_name in file_list:
    file_path = os.path.join(folder_path, file_name)
    
    data_range = pd.read_excel(file_path, skiprows=2,usecols='A:O')
    
    data_range = data_range.rename(columns={'Unnamed: 0':'REF','Unnamed: 1':'DESCRIPTION','Unnamed: 2':'TEAM'})
    
    start_row = data_range[data_range.iloc[:, 1].isin(['Number of Open Recommendations Accepted within target','Number of Open Acceptances considered within target'])].index[0]
    
    data_range = data_range.loc[range(start_row,start_row+4)].fillna(value=0)
    
    data_range = data_range.reindex(data_range.columns[0:3].to_list() + sorted(data_range.columns[3:]), axis=1)
    
    data.append(data_range)

[1:10]
    # Append NSD
file_list
file_path = os.path.join(folder_path, 'Copy of PEC Single Truth 2022-2023 (003).xlsx')
data_range = pd.read_excel(file_path,skiprows=2,usecols='A:O')
data_range = data_range.rename(columns={'Unnamed: 0':'REF','Unnamed: 1':'DESCRIPTION','Unnamed: 2':'TEAM'})
start_row = data_range[data_range.iloc[:, 1].isin(['Number of Open Recommendations Accepted within target','Number of Open Acceptances considered within target'])].index[0]
data_range = data_range.loc[range(start_row,start_row+5)].fillna(value=0)
data_range = data_range.reindex(data_range.columns[0:3].to_list() + sorted(data_range.columns[3:]), axis=1)

data = pd.concat(data, ignore_index=True).fillna(value=0)
data
data2 = data[data['DESCRIPTION'].str.contains('of which IPPs',case=False)]
data2

sum_row = data2[data2.columns[3:]].sum(axis=0)
sum_row
len(sum_row)

sum_row.index = pd.to_datetime(sum_row.index)
yearly_sum = sum_row.resample('Y').sum().reset_index()

def format_datetime_column(column):
    return column.strftime('%Y_%b').upper()

# Apply the function to the column names
data.columns[3:] = [format_datetime_column(col) for col in data.columns[3:]]
data.iloc[:,3:].columns
data.head()
start_row = sheet_df[sheet_df.iloc[:, 1]=='Under 18'].index[0]
data_range = sheet_df.iloc[start_row:start_row+9, 1:4].fillna(value=0)
data_range.columns = ['AGE', 'CAT4L2', 'CAT4L3']
area_id = pd.read_excel(file_path, sheet_name='Data entry', usecols='A', nrows=2).iloc[0, 0]
area_name = pd.read_excel(file_path, sheet_name='Data entry', usecols='C', nrows=2).iloc[0, 0]
data_range['AREA_ID'] = area_id
data_range['AREA'] = area_name

data.append(data_range)

# Concatenate all the dataframes into one
age = pd.concat(data, ignore_index=True).fillna(value=0)
age = age[['AREA_ID','AREA'] + [col for col in age.columns if col not in ['AREA_ID','AREA']]]
age[age.columns[3:]] = age[age.columns[3:]].astype('int64')

age['TOTAL'] = age[age.columns[3:]].sum(axis=1)
len(age) # should be 387
age['AREA'].value_counts()

age.head()

# Bring in Level 2 + Level 3

age_correction = age.groupby(['AREA_ID','AREA'])['TOTAL'].sum().reset_index(name='TOTAL')

age_correction = pd.merge(age_correction, mappa_data[['AREA_ID','LEVEL2TOTT1','LEVEL3TOTT1']], on='AREA_ID')

age_correction['L2_L3_TOTAL'] = age_correction['LEVEL2TOTT1'] +  age_correction['LEVEL3TOTT1']

age_correction =  age_correction.drop(['LEVEL2TOTT1','LEVEL3TOTT1'],axis=1)

age_correction['DIFFERENCE'] = (age_correction['TOTAL']  - age_correction['L2_L3_TOTAL'])
age_correction['DIFFERENCE'] = age_correction['DIFFERENCE'].abs()

age_correction['CHECK']='Yes'
age_correction.loc[age_correction['DIFFERENCE']==0,'CHECK'] = ''

age_correction

# Write to Excel

output_work_book = 'corrections_areas.xlsx'

with pd.ExcelWriter(output_work_book) as writer:
    age_correction.to_excel(writer, sheet_name='Age',index=False)
