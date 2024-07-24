""" 
In 2022, what percentage of all Fixed Term Recalls issued were "second" FTRs on the same sentence? 
In other words, for how many individuals given an FTR in 2022 was this their second FTR under the same licence?

By Eric Nyame, 18/03/2024
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

sys.path.append('/home/jovyan/OMPPG/Macro Library')
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

""" Check the earliest date of sentence of those who received fixed term recall in 2022.
    This will allow you to know the cut-off point for recall data.
"""

# ------------------ Use publication and fresh extracts to determine number of fixed-term recalls each year

rec2022 = pd.read_excel(f"s3://alpha-omppg/Data Central/PPUD Recalls/Recalls_2021_2022.xls")
rec2022=rec2022[rec2022['LICENCE_REVOKE_DATE'].dt.year == 2022]
rec2022 = rec2022[rec2022['RECALL_TYPE_DESCRIPTION'].str.contains('FTR|Fixed', case=False)]  # keep only fixed-term recalls
rec2022['LICENCE_REVOKE_DATE'].dt.year.value_counts(dropna=False)

rec2022['DOS'].dt.year.value_counts(dropna=False).sort_index()
rec2022['RELEA'].dt.year.value_counts(dropna=False).sort_index()
rec2022.info()
    # Interprets last 5 years as 2018 to 2022
years = [2018, 2019, 2020, 2021, 2022] #2013,2014,2015,2016,2017, 
quarters =['q1','q2','q3','q4']

    # concatenate publication datasets and keep only fixed-term recalls

pub_fixed = pd.DataFrame() # start with an empty dataframe

for i in years:
    for j in quarters:
        if (i == 2013) and (j != 'q4'): # start from q4 2013 
            continue
        if (i == 2023) and (j =='q4'): # end at q3 2023
            break
        rec = pd.read_sas(f"s3://alpha-omppg/Recalls/Final Data/SAS/recalls_final_{i}{j}.sas7bdat", encoding='latin1')
        rec.columns = rec.columns.str.upper() # capitalise all headers
        rec = rec[rec['RECALL_TYPE_DESCRIPTION'].str.contains('FTR|Fixed', case=False)] # keep only fixed-term recalls
        pub_fixed = pd.concat([pub_fixed,rec],axis = 0, ignore_index= True) # concatenate 

       # import fresh fixed-term recall extracts from PPUD
    
rec_file_names = ['Recalls_up_to_2009.xls','Recalls_2012_2013.xls','Recalls_2014_2016.xls','Recalls_2017_2018.xls','Recalls_2019_2020.xls','Recalls_2021_2022.xls','Recalls_2023.xls'] # file names on amazon

extract_fixed = pd.DataFrame() # start with an empty dataframe to capture all PPUD fixed term recalls up to Sep 2023

for filename in rec_file_names:
    rec = pd.read_excel(f"s3://alpha-omppg/Data Central/PPUD Recalls/{filename}")
    rec = rec[rec['RECALL_TYPE_DESCRIPTION'].str.contains('FTR|Fixed', case=False)] # keep only fixed-term recalls
    extract_fixed = pd.concat([extract_fixed,rec],axis = 0, ignore_index= True) # concatenate

extract_fixed_2 = extract_fixed.copy()
extract_fixed_2.shape # 96804.

extract_fixed_2['RECALL_TYPE_DESCRIPTION'].value_counts(dropna=False)

  
# Create year variables in both datasets

# pub_fixed['YEAR'] = pub_fixed['LICENCE_REVOKE_DATE'].dt.to_period('Y')
extract_fixed_2['YEAR'] = extract_fixed_2['LICENCE_REVOKE_DATE'].dt.to_period('Y')

# Determine recall number for each combination of date of sentence and licence revocation date

extract_fixed_2['DOS'].isna().sum() # 2 cases with missing date of sentece, good
extract_fixed_2['LICENCE_REVOKE_DATE'].isna().sum() # 0
extract_fixed_2['NOMS_ID'].isna().sum() # 2839
extract_fixed_2['FILE_REFERENCE'].isna().sum() # 36
extract_fixed_2['PRISON_NUMBER'].isna().sum() # 2

# check duplicates
extract_fixed_2.duplicated(['PRISON_NUMBER','DOS','LICENCE_REVOKE_DATE'],keep='first').sum() # 8
extract_fixed_2.duplicated(['PRISON_NUMBER','LICENCE_REVOKE_DATE'],keep='first').sum() # 13

    # remove duplicate prison number and licence revoke date
extract_fixed_2 = extract_fixed_2.sort_values(['PRISON_NUMBER','LICENCE_REVOKE_DATE'])

extract_fixed_2 = extract_fixed_2.drop_duplicates(['PRISON_NUMBER','LICENCE_REVOKE_DATE'])
extract_fixed_2.shape #96791,42

    # Count fixed-term recalls per year
# pub_fixed['YEAR'].value_counts(dropna=False).sort_index() # should start from 2013 Q4 to 2023 Q3.
extract_fixed_2[extract_fixed_2['LICENCE_REVOKE_DATE'].dt.year == 2022]['YEAR'].value_counts(dropna=False).sort_index() #5227

    # count the recall number for each combination of prison number, dos and licence revoke date

extract_fixed_2 = extract_fixed_2.sort_values(['PRISON_NUMBER','DOS','LICENCE_REVOKE_DATE'])

extract_fixed_2['RECALL_NUMBER'] = extract_fixed_2.groupby(['PRISON_NUMBER','DOS']).cumcount() + 1

retain = ['FILE_REFERENCE','FAMILY_NAME','DOS','LICENCE_REVOKE_DATE','RECALL_NUMBER','RECALL_TYPE_DESCRIPTION']

extract_fixed_2 = extract_fixed_2[retain +[col for col in extract_fixed_2.columns if col not in retain]]

extract_fixed_2.head(50)

# Keep only the second fixed-term recalls
rec_2022 = extract_fixed_2[extract_fixed_2['LICENCE_REVOKE_DATE'].dt.year == 2022].copy()
second_ft_recalls_2022 = rec_2022[rec_2022['RECALL_NUMBER'] == 2]

second_ft_recalls_2022.shape[0] # 688

# tabulate to answer
    # number of second recall per year
    second_ft_recalls_2022['YEAR'].value_counts(dropna=False).sort_index()
    
    # number of recalls per year
    rec_2022['YEAR'].value_counts(dropna=False).sort_index()

#Conclusion
"""
Whave 688/5227 approx 13% of all FTR in 2022 being second fixed-term recall."""