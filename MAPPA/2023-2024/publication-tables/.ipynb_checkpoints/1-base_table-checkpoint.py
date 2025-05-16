""" 
GOAL: PRODUCE MAPPA TABLES FOR PUBLICATION
By Eric Nyame, 27/09/2024
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

# BRING IN IN POPULATION DATA

storage_options = {'User-Agent': 'Mozilla/5.0'} # don't understand but it's needed to import the excel file

area_data_frames = [] # will contain individual area tables for the years

# area table links from 2014 to 2023

link_list =['https://assets.publishing.service.gov.uk/media/5a7e1dc640f0b62305b80e80/mappa-annual-report-2013-14-by-area.xls',
'https://assets.publishing.service.gov.uk/media/5a7f2e26e5274a2e8ab4a9c6/mappa-annual-report-2014-15-area.xls',
'https://assets.publishing.service.gov.uk/media/5a74a39ee5274a5294068f8f/MAPPA_Annual_Report_2015-16_Area_Tables.xls',
'https://assets.publishing.service.gov.uk/media/5a74c421ed915d502d6cad26/MAPPA-annual-report-2016-17-area-tables.xlsx',
'https://assets.publishing.service.gov.uk/media/5bd04867ed915d789dcd637b/mappa-annual-report-2017-18-area-tables.xlsx',
'https://assets.publishing.service.gov.uk/media/5db964b940f0b637a57b061d/mappa-annual-report-2018-19-area-tables.xlsx',
            'https://assets.publishing.service.gov.uk/media/5f99719f8fa8f57919208818/MAPPA_Annual_Report_2019-20_Area_Tables.xlsx',
'https://assets.publishing.service.gov.uk/media/617946c2e90e07197483b857/MAPPA_Annual_Report_2020-21_Area_Tables.xlsx',
'https://assets.publishing.service.gov.uk/media/6359740ad3bf7f0bcfa56301/MAPPA-Annual-Report-2021-22-Area-Tables.xlsx',
'https://assets.publishing.service.gov.uk/media/653967afe6c968000daa9b29/MAPPA_Annual_Report_-_Areas_Tables_2022-23.xlsx']

years = [2014, 2015, 2016, 2017, 2018, 2019, 2020,2021, 2022,2023]

for i,link in enumerate(link_list):
    xl = pd.ExcelFile(link)
    sheet_name = xl.sheet_names[-1] # read the last sheet name in case there is a content sheet
    
    pop_data = pd.read_excel(link, storage_options = storage_options, sheet_name = sheet_name)
    area_loc = pop_data.iloc[5,0]
    
    if area_loc == 'Area':
        pop_data = pd.read_excel(link, storage_options = storage_options, sheet_name = sheet_name, skiprows = 6, nrows=43)
    else:
        pop_data = pd.read_excel(link, storage_options = storage_options, sheet_name = sheet_name, skiprows = 4, nrows=43)
    pop_data['Year'] = years[i]
    
    pop_data.columns = [c.replace('\n','') for c in pop_data.columns]
    pop_data.columns = [c.split('(')[0].strip() for c in pop_data.columns]
    pop_data.columns = [c.replace('  ',' ') for c in pop_data.columns]
    pop_data = pop_data.replace('-',0)
    
    area_data_frames.append(pop_data)

pop_data
# Concatenate all the dataframes into one
all_data = pd.concat(area_data_frames, ignore_index=True).fillna(value=0)

all_data = all_data.loc[all_data['Total MAPPA offenders'] > 0]
all_data['Year'].value_counts(dropna=False).sort_index()

all_data.head()
all_data.tail()

all_data.info()
all_data.to_parquet('all_area_data.parquet')

