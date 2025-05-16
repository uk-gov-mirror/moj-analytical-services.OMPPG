""" 
GOAL: PRODUCE DATA FOR MAPPA PUBLICATION.
By Eric Nyame, 31/07/2024
"""

#---------------------------------- Import Packages

import pandas as pd
# from pandas.api.types import CategoricalDtype
import numpy as np
import os
import sys
# import duckdb
# import importlib

# openpyxl
# from openpyxl import Workbook, load_workbook
# from openpyxl.styles import Font, Alignment
# from openpyxl.utils import get_column_letter

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

# sys.path.append('/home/jovyan/OMPPG/Macro Library')
# from my_log import my_log
# import Out_of_bounds_dates
# import prepareMatch
# importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
# import TimeDiffs

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

# IMPORT DATA FROM SHEET '23-24 data'

returns_folder = 'returns'
list_of_file_names = os.listdir(returns_folder)
list_of_file_names = [name for name in list_of_file_names if name.endswith('.xlsx')]
list_of_file_names.remove('NSD.xlsx') # exclude NSD for now. Will work on it separately
len(list_of_file_names) # should be 42 for now without NSD

sheet_name = '23-24 data'
cols_to_import = 'A:BQ'

# Initialize an empty list to hold the dataframes
list_of_data_frames = []

# Loop through the files and read the specified range
for file_name in list_of_file_names:
    
    file_path = os.path.join(returns_folder, file_name)
    data_range = pd.read_excel(file_path, sheet_name = sheet_name, usecols = cols_to_import, nrows=2)
    list_of_data_frames.append(data_range)

# Append NSD
file_path = os.path.join(returns_folder, 'NSD.xlsx')
data_range = pd.read_excel(file_path, sheet_name=sheet_name, usecols='A:T', nrows=2)
data_range
list_of_data_frames.append(data_range)

# Concatenate all the dataframes into one
mappa_data = pd.concat(list_of_data_frames, ignore_index=True)
mappa_data.columns = mappa_data.columns.str.upper()
mappa_data = mappa_data.sort_values('AREAID',ignore_index=True)

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

mappa_data['AREA_NAME'] = mappa_data['AREAID'].map(area_dict)

mappa_data = mappa_data[['AREAID','AREA_NAME'] + [col for col in mappa_data.columns if col not in ['AREAID','AREA_NAME']]]
mappa_data.head()

# Level totals for table 1

mappa_data['LEVEL1TOTT1'] = mappa_data['CAT1L1'] + mappa_data['CAT2L1'] + mappa_data['CAT4L1']
mappa_data['LEVEL2TOTT1'] = mappa_data['CAT1L2'] + mappa_data['CAT2L2'] + mappa_data['CAT3L2'] + mappa_data['CAT4L2']
mappa_data['LEVEL3TOTT1'] = mappa_data['CAT1L3'] + mappa_data['CAT2L3'] + mappa_data['CAT3L3'] + mappa_data['CAT4L3']

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

# BRING IN IN POPULATION DATA
"""pop_link = "https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/populationestimatesforukenglandandwalesscotlandandnorthernireland/mid2022/mye22final.xlsx""""

pop_link = "https://www.ons.gov.uk/file?uri=/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/estimatesofthepopulationforenglandandwales/mid20232023localauthorityboundarieseditionofthisdataset/mye23tablesew.xlsx"

storage_options = {'User-Agent': 'Mozilla/5.0'} # don't understand but it's needed to import the excel file
pop_data = pd.read_excel(pop_link, storage_options = storage_options, sheet_name = 'MYE2 - Persons', skiprows = 7)
pop_data.head()

ten_col_num = pop_data.columns.get_loc('10')
ten_plus_total = pop_data[pop_data.columns[ten_col_num:]].sum(axis=1)
pop_data.insert(4,'10+',ten_plus_total)

pop_lookup = pd.read_excel('../lookup-table-uk-authority-codes-2024.xlsx')
pop_lookup.head()

ons_pop_data = pd.merge(pop_lookup[['LAD24CD','LAD24NM','PFA24CD','PFA24NM','MAPPA_NAME']],
                        pop_data[['Code','10+']],left_on = 'LAD24CD',right_on ='Code')
ons_pop_data.head()
ons_pop_data = ons_pop_data.groupby(['MAPPA_NAME'])['10+'].sum().reset_index()

# CRUCIAL - CHECK THE TOTALS HERE MATCH!!!!!

ons_pop_data['10+'].sum() == pop_data[pop_data['Name'] == 'ENGLAND AND WALES']['10+'].values[0] # 54,117,598

ons_pop_data.head()

mappa_data  =  pd.merge(mappa_data, ons_pop_data,left_on = 'AREA_NAME',right_on ='MAPPA_NAME', how = 'left')
mappa_data['10+'] = mappa_data['10+'].fillna(value = 0)
mappa_data['10+'] = mappa_data['10+'].astype('int64')

mappa_data['10+'].sum() # must match the totals above

# this works - calculate rate of RSO per 100,000 head of population
mappa_data['RSO_POP'] = round(mappa_data['CAT1TOT']*100000/mappa_data['10+'])
mappa_data['RSO_POP'] = mappa_data['RSO_POP'].fillna(value = 0)
mappa_data['RSO_POP'] = mappa_data['RSO_POP'].astype('int64')

# this works - round the 10+ population to nearest 100
mappa_data['NEWPOP'] = round(mappa_data['10+'],-2)
mappa_data

retain =['AREAID', 'AREA_NAME', 'CAT1L1', 'CAT1L2', 'CAT1L3', 'CAT2L1', 'CAT2L2', 'CAT2L3', 'CAT3L2', 'CAT3L3', 'LEVEL1TOTT1', 'LEVEL2TOTT1', 'LEVEL3TOTT1', 'CAT1TOT', 'CAT2TOT', 'CAT3TOT', 'TOTAL_MAPPA_OFFENDERS', 'NEWPOP', 'RSO_POP', 'CAT1L2YEAR', 'CAT1L3YEAR', 'CAT2L2YEAR', 'CAT2L3YEAR', 'CAT3L2YEAR', 'CAT3L3YEAR', 'CAT1YEAR', 'CAT2YEAR', 'CAT3YEAR', 'LEVEL2TOTT3', 'LEVEL3TOTT3', 'CAT1CAUTCON', 'CAT1L1CAUTCON', 'CAT1L2CAUTCON', 'CAT1L3CAUTCON', 'SOPOGRANT', 'NOGRANT', 'FTOGRANT', 'CAT1L2LICBREACH', 'CAT2L2LICBREACH', 'CAT3L2LICBREACH', 'LEVEL2BREACHT7', 'CAT1L3LICBREACH', 'CAT2L3LICBREACH', 'CAT3L3LICBREACH', 'LEVEL3BREACHT7', 'BREACHTOTALT7', 'CAT1L2SOPOBREACH', 'CAT1L3SOPOBREACH', 'SOPOTOTALT7', 'CAT1L1SFO', 'CAT1L2SFO', 'CAT1L3SFO', 'CAT2L1SFO', 'CAT2L2SFO', 'CAT2L3SFO', 'CAT3L2SFO', 'CAT3L3SFO', 'TOTALSFOCHARGE', 'CAT1L1SFOCONV', 'CAT1L2SFOCONV', 'CAT1L3SFOCONV', 'CAT2L1SFOCONV', 'CAT2L2SFOCONV', 'CAT2L3SFOCONV', 'CAT3L2SFOCONV', 'CAT3L3SFOCONV', 'TOTALSFOCONV', 'CAT1L1SFOCHARGE', 'CAT1L2SFOCHARGE', 'CAT1L3SFOCHARGE', 'CAT2L1SFOCHARGE', 'CAT2L2SFOCHARGE', 'CAT2L3SFOCHARGE', 'CAT3L2SFOCHARGE', 'CAT3L3SFOCHARGE', 'TOTALSFOSTILLCHARGE', 'CAT1L1SFOOTHER', 'CAT1L2SFOOTHER', 'CAT1L3SFOOTHER', 'CAT2L1SFOOTHER', 'CAT2L2SFOTHER', 'CAT2L3SFOOTHER', 'CAT3L2SFOOTHER', 'CAT3L3SFOOTHER', 'TOTALSFOOTHER', 'TOTALSCRL2', 'TOTALSCRL3', 'TOTALSCR', 'SROBREACH', 'RSOREVOKE']

mappa_data2 = mappa_data[retain + [col for col in mappa_data if col not in retain]]
mappa_data2

mappa_data2.to_excel('Table All Areas Source.xlsx',index=False)

# NSD
retain2 = ['AREAID', 'AREA_NAME', 'CAT4L1', 'CAT4L2', 'CAT4L3', 'LEVEL1TOTT1', 'LEVEL2TOTT1', 'LEVEL3TOTT1', 'CAT4TOT', 'CAT4L2YEAR', 'CAT4L3YEAR', 'CAT4YEAR', 'LEVEL2TOTT3', 'LEVEL3TOTT3', 'SOPOGRANT', 'NOGRANT', 'FTOGRANT', 'CAT4L2LICBREACH', 'LEVEL2BREACHT7', 'CAT4L3LICBREACH', 'LEVEL3BREACHT7', 'BREACHTOTALT7', 'SOPOTOTALT7', 'CAT4L1SFO', 'CAT4L2SFO', 'CAT4L3SFO', 'TOTALSFOCHARGE', 'CAT4L1SFOCONV', 'CAT4L2SFOCONV', 'CAT4L3SFOCONV', 'TOTALSFOCONV', 'CAT4L1SFOCHARGE', 'CAT4L2SFOCHARGE', 'CAT4L3SFOCHARGE', 'CAT2L1SFOCHARGE', 'TOTALSFOSTILLCHARGE', 'CAT4L1SFOOTHER', 'CAT4L2SFOOTHER', 'CAT4L3SFOOTHER', 'TOTALSFOOTHER', 'TOTALSCRL2', 'TOTALSCRL3', 'TOTALSCR', 'SROBREACH', 'RSOREVOKE']

nsd = mappa_data2[(mappa_data2['AREAID'] == 43)][retain2]

nsd.to_excel('NSD.xlsx',index=False)
