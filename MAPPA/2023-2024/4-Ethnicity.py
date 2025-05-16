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

# Initialize an empty list to hold the data

list_of_data_frames = []

# Loop through the files and read the necessary data
for file_name in list_of_file_names:
    file_path = os.path.join(returns_folder, file_name)
    
    # Read the value in cell C2
    area_id = pd.read_excel(file_path, sheet_name='Data entry', usecols='A', nrows=2).iloc[0, 0]
    area_name = pd.read_excel(file_path, sheet_name='Data entry', usecols='C', nrows=2).iloc[0, 0]
    
    # Read the entire sheet to locate the row containing '18' in column B
    sheet_df = pd.read_excel(file_path, sheet_name='Data entry')
    
    # Find the first row where column B contains '18'
    start_row = sheet_df[sheet_df.iloc[:, 1]=='White - Scottish'].index[0]
    
    # Define the range to extract data: 8 rows down and 6 columns to the right from the start_row
    data_range = sheet_df.iloc[start_row:start_row+40, 1:8].fillna(value=0)
    
    # Rename the columns appropriately
    data_range.columns = ['ETHNICITY', 'CAT1L2', 'CAT1L3', 'CAT2L2', 'CAT2L3', 'CAT3L2', 'CAT3L3']
    
    # Add the 'AREA' column to the dataframe
    data_range['AREA_ID'] = area_id
    data_range['AREA'] = area_name
    # Append to the data list
    list_of_data_frames.append(data_range)

    # Append NSD
file_path = os.path.join(returns_folder, 'NSD.xlsx')
sheet_df = pd.read_excel(file_path, sheet_name='Data entry')
start_row = sheet_df[sheet_df.iloc[:, 1]=='White - Scottish'].index[0]
data_range = sheet_df.iloc[start_row:start_row+40, 1:4].fillna(value=0)
data_range.columns = ['ETHNICITY', 'CAT4L2', 'CAT4L3']
area_id = pd.read_excel(file_path, sheet_name='Data entry', usecols='A', nrows=2).iloc[0, 0]
area_name = pd.read_excel(file_path, sheet_name='Data entry', usecols='C', nrows=2).iloc[0, 0]
data_range['AREA_ID'] = area_id
data_range['AREA'] = area_name

list_of_data_frames.append(data_range)

# Concatenate all the dataframes into one
ethnicity_data = pd.concat(list_of_data_frames, ignore_index=True).fillna(value=0)
ethnicity_data = ethnicity_data[['AREA_ID','AREA'] + [col for col in ethnicity_data.columns if col not in ['AREA_ID','AREA']]]
ethnicity_data[ethnicity_data.columns[3:]] = ethnicity_data[ethnicity_data.columns[3:]].astype('int64')

ethnicity_data['TOTAL'] = ethnicity_data[ethnicity_data.columns[3:]].sum(axis=1)

len(ethnicity_data) # should be 1720
ethnicity_data['AREA'].value_counts() # 40 each

ethnicity_data.head()

ethnicity(ethnicity_data,'ETHNICITY','ETHNICITY2')
    
ethnicity_data.groupby('ETHNICITY2')[sex_data.columns[3:]].sum().reset_index().to_excel('ethnicity.xlsx',index = False)

# Bring in Level 2 + Level 3

ethnicity_correction = ethnicity_data.groupby(['AREA_ID','AREA'])['TOTAL'].sum().reset_index(name='TOTAL')

ethnicity_correction = pd.merge(ethnicity_correction, mappa_data[['AREA_ID','LEVEL2TOTT1','LEVEL3TOTT1']], on='AREA_ID')

ethnicity_correction['L2_L3_TOTAL'] = ethnicity_correction['LEVEL2TOTT1'] +  ethnicity_correction['LEVEL3TOTT1']

ethnicity_correction =  ethnicity_correction.drop(['LEVEL2TOTT1','LEVEL3TOTT1'],axis=1)

ethnicity_correction['DIFFERENCE'] = (ethnicity_correction['TOTAL']  - ethnicity_correction['L2_L3_TOTAL'])
ethnicity_correction['DIFFERENCE'] = ethnicity_correction['DIFFERENCE'].abs()

ethnicity_correction['CHECK']='Yes'
ethnicity_correction.loc[ethnicity_correction['DIFFERENCE']==0,'CHECK'] = ''

ethnicity_correction

# Write to Excel if any to check

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a',if_sheet_exists='replace') as writer:
    ethnicity_correction.to_excel(writer,sheet_name='Ethnicity',index=False)