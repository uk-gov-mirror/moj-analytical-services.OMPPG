""" 
In 2022 and 2023, how many Fixed Term Recalls were cited with "Facing a further charge" as their recall reason?

By Eric Nyame, 09/10/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib

# import re

# from dateutil.relativedelta import relativedelta

#---------------------------------- Import own predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
# import prepareMatch
# importlib.reload(prepareMatch)
# import openMatch
# importlib.reload(openMatch)
import TimeDiffs

#----------------------------------Set display options

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
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #


#----------------------------------Set Global Parameters

years = [2022,2023]
quarters =['q1','q2','q3','q4']

#---------------------------------- Import data

recalls = pd.DataFrame() # start with an empty dataframe

# some of the files are SAS and others are Parquet, so try to import each

for year in years:
    for quarter in quarters:
        # Try to import SAS file
        try:
            quart_recs = pd.read_sas(f"s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_{year}{quarter}.sas7bdat", encoding='latin1')
            quart_recs.columns = quart_recs.columns.str.upper()
            print(f"Loaded SAS file for {year}{quarter}")
        except Exception as e:
            # else if the file is not SAS, import it if it's a parquet file
            print(f"Failed to load SAS file for {year}{quarter}, error: {e}")
            try:
                quart_recs = pd.read_parquet(f"s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_{year}{quarter}.parquet")
                quart_recs.columns = quart_recs.columns.str.upper()
                print(f"Loaded Parquet file for {year}{quarter}")
            except Exception as e:
                print(f"Failed to load Excel file for {year}{quarter}, error: {e}")

        recalls = pd.concat([recalls,quart_recs],axis=0)

#---------------------------------- Process data
len(recalls) # 51391
recalls['RECALL_TYPE_DESCRIPTION'].value_counts(sort = False, dropna=False)

# create fixed-term reall flag
ftr_mask = recalls['RECALL_TYPE_DESCRIPTION'].str.contains('fix|ftr', case=False)

len(recalls[ftr_mask]) # 11925 
recalls[ftr_mask]['RECALL_TYPE_DESCRIPTION'].value_counts(sort = False, dropna=False) # 11925 fixed

# create further offence flag
further_offence_mask = recalls['RECALL_REASON_DESCRIPTIONS'].str.contains('Offence|further', case = False,na=False)

further_offence_mask_2 = (recalls['FURTHER_CHARGE'] == 100)

# create fixed-term with further offence data
ftr_fo_data = recalls[ftr_mask & further_offence_mask]
len(ftr_fo_data) # 1944

# Breakdown by year
ftr_fo_data.set_index('LICENCE_REVOKE_DATE', inplace=True)
ftr_fo_data.info()

ftr_fo_data.groupby(ftr_fo_data.index.year)['LICENCE_REVOKE_TIME'].size().reset_index()