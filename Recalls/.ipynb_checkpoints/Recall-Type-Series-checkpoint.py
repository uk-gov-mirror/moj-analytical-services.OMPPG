""" 
GOAL: PRODUCE A SERIES OF RECALL TYPES OVERTIME FROM 2017
By Eric Nyame, 07/03/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib

import re

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
# from my_log import my_log
import Out_of_bounds_dates
importlib.reload(Out_of_bounds_dates)
import prepareMatch
importlib.reload(prepareMatch)
import openMatch
importlib.reload(openMatch)
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


# years =[*range(2017,2023)]
years = [2014,2015,2016,2017, 2018, 2019, 2020, 2021, 2022, 2023]
quarters =['q1','q2','q3','q4']

rec_types = pd.DataFrame()

for i in years:
    for j in quarters:
        if (i == 2023) and (j =='q4'):
            break
        rec = pd.read_sas(f"s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_{i}{j}.sas7bdat", encoding='latin1')
        rec.columns = rec.columns.str.upper()
        rec_types = pd.concat([rec_types,rec],axis = 0, ignore_index= True)

rec_2023Q4 = pd.read_parquet(f's3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2023q4.parquet')

rec_types = pd.concat([rec_types,rec_2023Q4],ignore_index=True)

len(rec_types) #16

rec_types.info()

rec_types.set_index('LICENCE_REVOKE_DATE', inplace=True)

# Resample and count per week
yearly_counts = rec_types.resample('Y').size()
yearly_counts
print(weekly_counts)
# Create a new column representing the year and quarter for each date
rec_types['Year_Quarter'] = rec_types['LICENCE_REVOKE_DATE'].dt.to_period('Q')
rec_types['Year_Year'] = rec_types['LICENCE_REVOKE_DATE'].dt.to_period('Y')

pd.crosstab(rec_types['RECALL_TYPE_DESCRIPTION'],rec_types['Year_Quarter'], margins = True, margins_name = 'Total').to_excel("Recall_Tyepes.xlsx")

pd.crosstab(rec_types['RECALL_TYPE_DESCRIPTION'],rec_types['Year_Year'], margins = True, margins_name = 'Total').to_excel("Recall_Types_Year.xlsx")
