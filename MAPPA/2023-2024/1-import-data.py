""" 
GOAL: PRODUCE RECALL TABLES FOR OMSQ.
By Eric Nyame, 17/04/2024
"""

#---------------------------------- Import Packages

import pandas as pd
from pandas.api.types import CategoricalDtype
import numpy as np
import sys
import duckdb
import importlib

# openpyxl
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
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

import os
import pandas as pd

# Folder containing the Excel files
folder_path = 'returns'
sheet_name = '23-24 data'
cols_to_import = 'A:BQ'

# List all files in the folder
file_list = [f for f in os.listdir(folder_path) if f.endswith('.xlsx') and f != 'NSD.xlsx']
file_list

# Initialize an empty list to hold the dataframes
data = []

# Loop through the files and read the specified range
for file_name in file_list:
    file_path = os.path.join(folder_path, file_name)
    # Read the data from the specified sheet and range
    data_range = pd.read_excel(file_path, sheet_name=sheet_name, usecols=cols_to_import, nrows=2)
    data.append(data_range)

# Append NSD
file_path = os.path.join(folder_path, 'NSD.xlsx')
data_range = pd.read_excel(file_path, sheet_name=sheet_name, usecols='A:T', nrows=2)
data_range
data.append(data_range)

# Concatenate all the dataframes into one
mappa_data = pd.concat(data, ignore_index=True)
mappa_data.columns = mappa_data.columns.str.upper()
mappa_data = mappa_data.rename(columns ={'AREAID':'AREA_ID'})
mappa_data = mappa_data.sort_values('AREA_ID',ignore_index=True)

# Replace NAs with zeros
mappa_data = mappa_data.fillna(value = 0)

mappa_data[mappa_data.columns[1:]] = mappa_data[mappa_data.columns[1:]].astype('int64')

mappa_data.head()
mappa_data.info()
len(mappa_data)

# rename
mappa_data = mappa_data.rename(columns ={'CAT3L3SFOCONVICT': 'CAT3L3SFOCONV',
                               'CAT1L3SFOCHARGED':'CAT1L3SFOCHARGE', 
                               'CAT4L3SFOCHARGED':'CAT4L3SFOCHARGE'})

# Areanames

area_dict = {1:'Avon and Somerset',2:'Bedfordshire',3:'Cambridgeshire',4:'Cheshire',5:'Durham',6:'Cumbria',7:'Derbyshire',8:'Devon & Cornwall',9:'Dorset',10:'Dyfed-Powys',11:'Essex',12:'Gloucestershire',13:'Gwent',14:'Hampshire',15:'Hertfordshire',16:'Humberside',17:'Kent',18:'Lancashire',19:'Leicestershire',20:'Lincolnshire',21:'London',22:'Greater Manchester',23:'Merseyside',24:'Norfolk',25:'North Wales',26:'North Yorkshire',27:'Northamptonshire',28:'Northumbria',29:'Nottinghamshire',30:'South Wales',31:'South Yorkshire',32:'Staffordshire',33:'Suffolk',34:'Surrey',35:'Sussex',36:'Cleveland',37:'Thames Valley',38:'Warwickshire',39:'West Mercia',40:'West Midlands',41:'West Yorkshire',42:'Wiltshire',43:'National Security Division'}

# reorder cols

mappa_data['AREA'] = mappa_data['AREA_ID'].map(area_dict)

mappa_data = mappa_data[['AREA_ID','AREA'] + [col for col in mappa_data.columns if col not in ['AREA_ID','AREA']]]
mappa_data.head()

# Level totals for table 1

mappa_data['LEVEL1TOTT1'] = mappa_data['CAT1L1'] + mappa_data['CAT2L1'] + mappa_data['CAT4L1']
mappa_data['LEVEL2TOTT1'] = mappa_data['CAT1L2'] + mappa_data['CAT2L2'] + mappa_data['CAT3L2'] + mappa_data['CAT4L2'];
mappa_data['LEVEL3TOTT1'] = mappa_data['CAT1L3'] + mappa_data['CAT2L3'] + mappa_data['CAT3L3'] + mappa_data['CAT4L3'];

# mappa_data[['AREAID','AREA_NAME','LEVEL1TOTT1']]

# Category totals for table 1

mappa_data['CAT1TOT'] = mappa_data['CAT1L1'] + mappa_data['CAT1L2'] + mappa_data['CAT1L3']
mappa_data['CAT2TOT'] = mappa_data['CAT2L1'] + mappa_data['CAT2L2'] + mappa_data['CAT2L3']
mappa_data['CAT3TOT'] = mappa_data['CAT3L2'] + mappa_data['CAT3L3']
mappa_data['CAT4TOT'] = mappa_data['CAT4L1'] + mappa_data['CAT4L2'] + mappa_data['CAT4L3']

mappa_data['TOTAL_MAPPA_OFFENDERS'] = mappa_data['LEVEL1TOTT1'] + mappa_data['LEVEL2TOTT1'] + mappa_data['LEVEL3TOTT1']

# Level totals for table 3

mappa_data['LEVEL2TOTT3'] = mappa_data['CAT1L2YEAR'] + mappa_data['CAT2L2YEAR'] + mappa_data['CAT3L2YEAR'] + mappa_data['CAT4L2YEAR']
mappa_data['LEVEL3TOTT3'] = mappa_data['CAT1L3YEAR'] + mappa_data['CAT2L3YEAR'] + mappa_data['CAT3L3YEAR'] + mappa_data['CAT4L3YEAR']

mappa_data['CAT1YEAR'] = mappa_data['CAT1L2YEAR'] + mappa_data['CAT1L3YEAR']
mappa_data['CAT2YEAR'] = mappa_data['CAT2L2YEAR'] + mappa_data['CAT2L3YEAR']
mappa_data['CAT3YEAR'] = mappa_data['CAT3L2YEAR'] + mappa_data['CAT3L3YEAR']
mappa_data['CAT4YEAR'] = mappa_data['CAT4L2YEAR'] + mappa_data['CAT4L3YEAR']

# Totals for table 5

mappa_data['CAT1CAUTCON'] = mappa_data['CAT1L1CAUTCON'] + mappa_data['CAT1L2CAUTCON'] + mappa_data['CAT1L3CAUTCON']

# Level totals for table 7

mappa_data['LEVEL2BREACHT7'] = mappa_data['CAT1L2LICBREACH'] + mappa_data['CAT2L2LICBREACH'] + mappa_data['CAT3L2LICBREACH'] + mappa_data['CAT4L2LICBREACH']
mappa_data['LEVEL3BREACHT7'] = mappa_data['CAT1L3LICBREACH'] + mappa_data['CAT2L3LICBREACH'] + mappa_data['CAT3L3LICBREACH'] + mappa_data['CAT4L3LICBREACH']

mappa_data['BREACHTOTALT7'] = mappa_data['LEVEL2BREACHT7'] + mappa_data['LEVEL3BREACHT7']
mappa_data['SOPOTOTALT7'] = mappa_data['CAT1L2SOPOBREACH'] + mappa_data['CAT1L3SOPOBREACH']

#SFO totals for tables 8, 9 & 10

mappa_data['LEVEL1SFOCHARGE'] = mappa_data['CAT1L1SFO'] + mappa_data['CAT2L1SFO'] + mappa_data['CAT4L1SFO']
mappa_data['LEVEL2SFOCHARGE'] = mappa_data['CAT1L2SFO'] + mappa_data['CAT2L2SFO'] + mappa_data['CAT3L2SFO'] + mappa_data['CAT4L2SFO']
mappa_data['LEVEL3SFOCHARGE'] = mappa_data['CAT1L3SFO'] + mappa_data['CAT2L3SFO'] + mappa_data['CAT3L3SFO'] + mappa_data['CAT4L3SFO']

mappa_data['TOTALSFOCHARGE'] = mappa_data['LEVEL1SFOCHARGE'] + mappa_data['LEVEL2SFOCHARGE'] + mappa_data['LEVEL3SFOCHARGE']

#Totals for table 11

mappa_data['TOTALSFOCONV'] = (mappa_data['CAT1L1SFOCONV'] + mappa_data['CAT1L2SFOCONV'] + mappa_data['CAT1L3SFOCONV'] + mappa_data['CAT2L1SFOCONV'] + 
                             mappa_data['CAT2L2SFOCONV'] + mappa_data['CAT2L3SFOCONV'] + mappa_data['CAT3L2SFOCONV'] + mappa_data['CAT3L3SFOCONV'] + 
                             mappa_data['CAT4L1SFOCONV'] + mappa_data['CAT4L2SFOCONV'] + mappa_data['CAT4L3SFOCONV'])

#Totals for table 12

mappa_data['TOTALSFOSTILLCHARGE'] = (mappa_data['CAT1L1SFOCHARGE'] + mappa_data['CAT1L2SFOCHARGE'] + mappa_data['CAT1L3SFOCHARGE'] + 
                                     mappa_data['CAT2L1SFOCHARGE'] + mappa_data['CAT2L2SFOCHARGE'] + mappa_data['CAT2L3SFOCHARGE'] + 
                                     mappa_data['CAT3L2SFOCHARGE'] + mappa_data['CAT3L3SFOCHARGE'] + mappa_data['CAT4L1SFOCHARGE'] + 
                                     mappa_data['CAT4L2SFOCHARGE'] + mappa_data['CAT4L3SFOCHARGE'])

#Totals for table 13

mappa_data['TOTALSFOOTHER'] = (mappa_data['CAT1L1SFOOTHER'] + mappa_data['CAT1L2SFOOTHER'] + mappa_data['CAT1L3SFOOTHER'] + 
                               mappa_data['CAT2L1SFOOTHER'] + mappa_data['CAT2L2SFOTHER'] + mappa_data['CAT2L3SFOOTHER'] + 
                               mappa_data['CAT3L2SFOOTHER'] + mappa_data['CAT3L3SFOOTHER'] + mappa_data['CAT4L1SFOOTHER'] + 
                               mappa_data['CAT4L2SFOOTHER'] + mappa_data['CAT4L3SFOOTHER'])

#Totals for table 14

mappa_data['TOTALSCR'] = (mappa_data['CAT1L2SCR'] + mappa_data['CAT1L3SCR'] + mappa_data['CAT2L2SCR'] + mappa_data['CAT2L3SCR'] + 
                          mappa_data['CAT3L2SCR'] + mappa_data['CAT3L3SCR'])

mappa_data['TOTALSCRL2'] = mappa_data['CAT1L2SCR'] + mappa_data['CAT2L2SCR'] + mappa_data['CAT3L2SCR']
mappa_data['TOTALSCRL3'] = mappa_data['CAT1L3SCR'] + mappa_data['CAT2L3SCR'] + mappa_data['CAT3L3SCR']


#removes unwanted variables

#drop mappa_data['CAT2L2SOPOBREACH'] mappa_data['CAT3L2SOPOBREACH'] mappa_data['CAT2L3SOPOBREACH'] mappa_data['CAT3L3SOPOBREACH'];

