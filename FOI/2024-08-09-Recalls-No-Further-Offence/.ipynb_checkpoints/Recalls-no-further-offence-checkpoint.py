""" 
2 The number of women recalled into custody for breach of post-release licence during 2023 ,
excluding those returned to custody for the commission of a further offence in Wales 
broken down into regional Probation Districts.

3 The number of women recalled into custody for breach of post-release  licence conditions,
excluding those returned to custody for the commission of a further offence,during 2023 for 
(a) England and (b) Wales and for England and Wales together.

By Eric Nyame, 29/05/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib
import os

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
#importlib.reload(Out_of_bounds_dates)
#import prepareMatch
#importlib.reload(prepareMatch)
#import openMatch
#importlib.reload(openMatch)
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


# ------------------ Import data

    # Interprets last 5 years as 2018 to 2022
# years = [2018, 2019, 2020, 2021, 2022] #2013,2014,2015,2016,2017, 
quarters =['q1','q2','q3','q4']

# loop through folders and try to import files with different file types but same name

recalls = pd.DataFrame()

for quarter in quarters:
    # import the file if it's a SAS file and name it pop_year
    try:
        quart_recs = pd.read_sas(f"s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2023{quarter}.sas7bdat", encoding='latin1')
        quart_recs.columns = quart_recs.columns.str.upper()
        print(f"Loaded SAS file for {quarter}")
    except Exception as e:
        print(f"Failed to load SAS file for {quarter}, error: {e}")
        # else if the file is not SAS, import it if it's a parquet file
        try:
            quart_recs = pd.read_parquet(f"s3://alpha-omppg/Recalls/final_data/recalls/all/recalls_final_2023{quarter}.parquet")
            quart_recs.columns = quart_recs.columns.str.upper()
            print(f"Loaded Parquet file for {quarter}")
        except Exception as e:
            print(f"Failed to load Excel file for {quarter}, error: {e}")
  
    recalls = pd.concat([recalls,quart_recs],axis=0)

    # upper case columns
len(recalls) # 27820

further_offence_mask_1 = recalls['RECALL_REASON_DESCRIPTIONS'].str.contains('Offence|further', case=False,na=False)
further_offence_mask_2 = (recalls['FURTHER_CHARGE'] == 100)

# recalls[further_offence_mask_1]['RECALL_REASON_DESCRIPTIONS'].value_counts(dropna=False).reset_index()
recalls[further_offence_mask_1]['RECALL_REASON_DESCRIPTIONS'].size # 7510
recalls[further_offence_mask_2]['RECALL_REASON_DESCRIPTIONS'].size # 7510

noFurtherOffence = recalls[~further_offence_mask_1].copy()

len(noFurtherOffence) # 20310

someCols = ['NPS_DIVISION','NPS_CRC_NAME','PROBATION_AREA_DESCRIPTION','PROB_AREA','NOMS_REGION_DESCRIPTION']

for i in someCols:
    print('\n' + i)
    print(noFurtherOffence[i].value_counts(dropna=False))

walesMask = noFurtherOffence['NOMS_REGION_DESCRIPTION'].str.contains('wales',case=False,na=False)
walesNoOffence = noFurtherOffence[walesMask]

for i in someCols:
    print('\n' + i)
    print(walesNoOffence[i].value_counts(dropna=False))

walesMask = noFurtherOffence['NOMS_REGION_DESCRIPTION'].str.contains('wales',case=False,na=False)

noFurtherOffence['COUNTRY'] = 'England'
noFurtherOffence.loc[noFurtherOffence['NPS_DIVISION'].str.contains('wales',case=False,na=False),'COUNTRY'] = 'Wales'

noFurtherOffence['COUNTRY'].value_counts(dropna=False) # 18814,1496

# femalesNoFurtherOffence = noFurtherOffence[noFurtherOffence['GENDER'] == 'F'].copy()
# len(femalesNoFurtherOffence) #1688

# Wales probation areas
for i in someCols:
    print('\n' + i)
    print(noFurtherOffence[walesMask][i].value_counts(dropna=False))

# Country breakdown
noFurtherOffence['COUNTRY'].value_counts(dropna=False) # 18814,1496
