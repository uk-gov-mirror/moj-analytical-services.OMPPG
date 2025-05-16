""" 
GOAL: DPPs in prison
By Eric Nyame, 26/03/2025
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib
from itables import show

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

# function to remove trailing and leading blanks

def strip_blanks(df):
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

# Function to identify where bad datetime value is. Pass in the 

def dateOutOfBoundsColumn(dataset,value): # pass in the out-of-bounds date
    for col in dataset.columns:
        # Convert the column to string and check if any value contains the problematic date substring
        if dataset[col].astype(str).str.contains(value).any():
            hmm = dataset[col].astype(str).str.contains(value)
            cols_to_keep = ['NOMIS_ID','SURNAME','EXTRACTDATE',col]
            display(dataset[hmm][cols_to_keep])
            break

dateOutOfBoundsColumn(pop,'9999-03-30')
pop.dtypes
# Function to show table in my preferred way
def show_data(data):
    show(data,
         scrollY="200px", 
         scrollCollapse=True, 
         paging=False,
         buttons=["excelHtml5"])

#----------------------------------Set Global Parameters
years = list(range(2022,2025))
quarters =[f"q{i}" for i in range(1,5)]

#---------------------------------- Import data

# some of the files are SAS and others are Parquet, so try to import each
pop = pd.DataFrame() # start with an empty dataframe

for year in years:
        
    for quarter in quarters:

        quart_pop = pd.DataFrame() # Reset appending file

        try: # Try to import SAS file first
            quart_pop = pd.read_parquet(f"s3://alpha-omppg/isp-population/final/isp_pop_{year}{quarter}.parquet")
            quart_pop.columns = quart_pop.columns.str.upper()
            quart_pop.loc[quart_pop['WHOLE_LIFE'].isin([True,'True']),'TARIFF_EXPIRY_DATE'] = pd.Timestamp.max.normalize()
            print(f"Loaded Parquet file for {year}{quarter}")

        except Exception as e:# If no SAS file, import parquet version

            print(f"Failed to load parquet file for {year}{quarter}, error: {e}")

            try:
                quart_pop = pd.read_sas(f"s3://alpha-omppg/isp-population/final/isp_pop_{year}{quarter}.sas7bdat", encoding='latin1')
                quart_pop.columns = quart_pop.columns.str.upper()
                quart_pop.loc[quart_pop['WHOLE_LIFE'].isin([True,'True']),'TARIFF_EXPIRY_DATE'] = pd.Timestamp.max.normalize()
                print(f"Loaded SAS file for {year}{quarter}")

            except Exception as e:
                print(f"Failed to load SAS file for {year}{quarter}, error: {e}")
        quart_pop = quart_pop.drop(columns=['LATEST_RELEASE_DATE','EFFECTIVE_TED'],errors='ignore')
        pop = pd.concat([pop,quart_pop],axis=0)

pop
def conCatRecallDatasets(years,quarters):
    
    pop = pd.DataFrame() # start with an empty dataframe

    for year in years:
        
        for quarter in quarters:

            quart_pop = pd.DataFrame() # Reset appending file

            try: # Try to import SAS file first
                quart_pop = pd.read_sas(f"s3://alpha-omppg/isp-population/final/isp_pop_{year}{quarter}.sas7bdat", encoding='latin1')
                quart_pop.columns = quart_pop.columns.str.upper()
                print(f"Loaded SAS file for {year}{quarter}")

            except Exception as e:# If no SAS file, import parquet version

                print(f"Failed to load SAS file for {year}{quarter}, error: {e}")

                try:
                    quart_pop = pd.read_parquet(f"s3://alpha-omppg/isp-population/final/isp_pop_{year}{quarter}.parquet")
                    quart_pop.columns = quart_pop.columns.str.upper()
                    print(f"Loaded Parquet file for {year}{quarter}")

                except Exception as e:
                    print(f"Failed to load parquet file for {year}{quarter}, error: {e}")

            pop = pd.concat([pop,quart_pop],axis=0)

    return pop

pop = conCatRecallDatasets(years,quarters)
len(recalls) # 240817


#---------------------------------- Load GPP data

# Import MH SAS population data


pop['ISP_STATUS'].value_counts(dropna=False)

dpp_condition = (pop['ISP_STATUS'].str.contains('IPP', na=False))  & (pop['CUSTODY_TYPE_DESCRIPTION'] == 'DPP')

dpp = pop[dpp_condition]

show_data(dpp.pivot_table(index='EXTRACTDATE',columns='ISP_STATUS',aggfunc='size',fill_value=0).reset_index())

                     
len(dpp)
                     
dpp[['NOMIS_ID','SURNAME','FORENAME','CUSTODY_TYPE_DESCRIPTION','ISP_STATUS','PRISONNAME','GENDER','SENTENCED_AGE','OFFENCEGROUP','OFFENCE','AGE','LAST_RECALLNUM']].to_excel("DPPS.xlsx", index=False)

recall = pd.read_parquet("s3://alpha-omppg/Recalls/Final Data/Parquet/isp_recalls_2024q1.parquet")
recall.shape
recall['U_SENT'] = recall['TARIFF_EXPIRY_DATE'].astype(str) + recall['PRISON_NUMBER'].astype(str)

recall = recall.sort_values(['U_SENT','LICENCE_REVOKE_DATE'], ascending=[True,False])
recall = recall.drop_duplicates('U_SENT')
recall.shape

recall[recall['NOMS_ID']=='A4266AD']['RECALLNUM']
pop[recall[recall['NOMS_ID']=='A4266AD']['RECALLNUM']