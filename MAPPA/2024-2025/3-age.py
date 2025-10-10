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

# GET A LIST OF FILE NAMES FROM RETURNS FOLDER

returns_folder = 'returns' 
list_of_file_names = os.listdir(returns_folder)
list_of_file_names = [name for name in list_of_file_names if name.endswith('.xlsx')]
list_of_file_names.remove('NSD.xlsx') # exclude NSD for now. Will work on it separately
len(list_of_file_names) # should be 42 for now without NSD

# IMPORT DATA FROM EACH FILE IN RETURNS FOLDER

list_of_data_frames = []

for file_name in list_of_file_names: 
    
    # For each file, get the area id and area name
    
    file_path = os.path.join(returns_folder, file_name)
    area_id = pd.read_excel(file_path, sheet_name = 'Data entry', usecols = 'A', nrows = 2).iloc[0, 0]
    area_name = pd.read_excel(file_path, sheet_name = 'Data entry', usecols = 'C', nrows = 2).iloc[0, 0]
    
    # Get age data from the file. 
    # Start from the row containing 'Under 18'
    # Read 9 rows down and 7 colums right
    
    sheet_df = pd.read_excel(file_path, sheet_name ='Data entry')
    start_row = sheet_df[sheet_df.iloc[:, 1]=='Under 18'].index[0]
    data_range = sheet_df.iloc[start_row:start_row + 9, 1:8].fillna(value = 0)
    
    # Rename the 7 columns appropriately
    data_range.columns = ['AGE', 'CAT1L2', 'CAT1L3', 'CAT2L2', 'CAT2L3', 'CAT3L2', 'CAT3L3']
     
    data_range['AREA_ID'] = area_id
    data_range['AREA'] = area_name
    
    list_of_data_frames.append(data_range)  # Append to the list of data frames

# Append NSD data separately
    
file_path = os.path.join(returns_folder, 'NSD.xlsx')
sheet_df = pd.read_excel(file_path, sheet_name = 'Data entry')
start_row = sheet_df[sheet_df.iloc[:, 1] == 'Under 18'].index[0]
data_range = sheet_df.iloc[start_row:start_row+9, 1:4].fillna(value=0) # have only cat 4
data_range.columns = ['AGE', 'CAT4L2', 'CAT4L3']
area_id = pd.read_excel(file_path, sheet_name='Data entry', usecols='A', nrows=2).iloc[0, 0]
area_name = pd.read_excel(file_path, sheet_name='Data entry', usecols='C', nrows=2).iloc[0, 0]
data_range['AREA_ID'] = area_id
data_range['AREA'] = area_name

list_of_data_frames.append(data_range)
list_of_data_frames

# Concatenate all the dataframes into one
age_data = pd.concat(list_of_data_frames, ignore_index = True).fillna(value=0)
age_data = age_data[['AREA_ID','AREA'] + [col for col in age_data.columns if col not in ['AREA_ID','AREA']]]
age_data[age_data.columns[3:]] =age_data[age_data.columns[3:]].astype('int64')

age_data['TOTAL'] = age_data[age_data.columns[3:]].sum(axis=1)
len(age_data) # should be 387
age_data['AREA'].value_counts() # 9 each to reflect age breakdown

age_data.head()

age_data.groupby('AGE')[sex_data.columns[3:]].sum().reset_index().to_excel('age.xlsx',index = False)
# CHECK TOTALS FOR LEVELS 2 AND 3 MATCH

age_correction = age_data.groupby(['AREA_ID','AREA'])['TOTAL'].sum().reset_index(name ='TOTAL')

age_correction = pd.merge(age_correction, mappa_data[['AREA_ID','LEVEL2TOTT1','LEVEL3TOTT1']], on='AREA_ID')

age_correction['L2_L3_TOTAL'] = age_correction['LEVEL2TOTT1'] +  age_correction['LEVEL3TOTT1']

age_correction =  age_correction.drop(['LEVEL2TOTT1','LEVEL3TOTT1'],axis=1)

age_correction['DIFFERENCE'] = (age_correction['TOTAL']  - age_correction['L2_L3_TOTAL'])
age_correction['DIFFERENCE'] = age_correction['DIFFERENCE'].abs()

age_correction['CHECK']='Yes'
age_correction.loc[age_correction['DIFFERENCE']==0,'CHECK'] = ''

age_correction

# Write to Excel if there is any to check

output_work_book = 'corrections_areas.xlsx'

with pd.ExcelWriter(output_work_book) as writer:
    age_correction.to_excel(writer, sheet_name='Age',index=False)
