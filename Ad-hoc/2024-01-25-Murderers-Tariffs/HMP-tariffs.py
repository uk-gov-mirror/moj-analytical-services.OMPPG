""" 
GOAL: DETERMINE THE AVERAGE TARIFF FOR MURDER CONVICTIONS.
BREAKDOWN BY GENDER
By Eric Nyame, 25/06/2024
"""

#---------------------------------- Import Packages

import pandas as pd
import numpy as np
import sys
import duckdb
import importlib

# import re

# from dateutil.relativedelta import relativedelta

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
#import prepareMatch
#importlib.reload(prepareMatch)
#import openMatch
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
        
# Import PPUD ISP cases

ispPPUD = pd.read_excel("s3://alpha-omppg/isp-population/PPUD/2025Q1/PPUD_ISP_2025Q1.xls")
wlPPUD = pd.read_excel("s3://alpha-omppg/isp-population/PPUD/2025Q1/PPUD_WholeLife_2025Q1.xls")

ispPPUD.head()
wlPPUD.head()

# Remove duplicates - all columns

ispPPUD.drop_duplicates(inplace=True)
wlPPUD.drop_duplicates(inplace=True)

# Check date fields and ensure every date field has type 'datetime' 

ispPPUD.info()
wlPPUD.info()

# delete some offending and unneeded datetime fields

ispPPUD = ispPPUD.drop('INDEX_OFFENCE_DATE',axis = 1)
ispPPUD = ispPPUD.drop('LATEST_RELEASE_DATE',axis = 1)

# Add whole life flag to PPUD ISP data - use duckDB

query =  """SELECT a.*, 
                   b.WHOLE_LIFE
            FROM ispPPUD AS a LEFT JOIN 
                (SELECT DISTINCT PRISON_NUMBER, DOS,NOMS_ID,FILE_REFERENCE,WHOLE_LIFE FROM wlPPUD) AS b 
            ON  (
                    (a.PRISON_NUMBER = b.PRISON_NUMBER AND a.PRISON_NUMBER IS NOT NULL) OR
                    (a.FILE_REFERENCE = b.FILE_REFERENCE AND a.FILE_REFERENCE IS NOT NULL) OR
                    (a.NOMS_ID = b.NOMS_ID AND a.NOMS_ID IS NOT NULL)
                ) AND a.DOS = b.DOS AND a.DOS IS NOT NULL"""

ispPPUD_MATCHED = duckdb.sql(query).df()
ispPPUD_MATCHED.head()


ispPPUD_MATCHED['CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

ispPPUD_MATCHED[ispPPUD_MATCHED['CUSTODY_TYPE_DESCRIPTION']== 'HMP [*]']['INDEX_OFFENCE_DESCRIPTION'].value_counts(dropna=False)

# HMP mask

hmpMask = ispPPUD_MATCHED['CUSTODY_TYPE_DESCRIPTION']== 'HMP [*]'

murderMask = ispPPUD_MATCHED['INDEX_OFFENCE_DESCRIPTION']== 'Murder'

hmpData = ispPPUD_MATCHED[hmpMask & murderMask]


hmpData['INDEX_OFFENCE_DESCRIPTION'].value_counts(dropna=False)

# Murder cases from 2000 onwards, no whole life orders

hmpMask_final = ( (hmpData['DOS'].dt.year >= 2000) & 
                  (hmpData['WHOLE_LIFE'] != True)
               )

hmpMask_final.shape # 1035

hmpData = hmpData[hmpMask_final]
hmpData.shape # 835

# Tariff length in years and months

tmth = hmpData['TARIFF_EXPIRY_DATE'] >= hmpData['DOS']
tmth2 = (hmpData['TARIFF_EXPIRY_DATE'].dt.year == 1900) | (hmpData['TARIFF_EXPIRY_DATE'].dt.year == pd.Timestamp.max.year)

hmpData['TARIFF_MONTHS'] = np.where(tmth,
                                        hmpData.apply(lambda x: TimeDiffs.month_diff(x['DOS'],x['TARIFF_EXPIRY_DATE']),axis=1),
                                        np.nan)
                        
hmpData.loc[tmth2,'TARIFF_MONTHS'] = np.nan

hmpData['TARIFF_YEARS'] = hmpData['TARIFF_MONTHS'] // 12

# Gender
hmpData['GENDER'].value_counts(dropna=False)

conditions_gender = [hmpData['GENDER'] == 'F ( Was M )',
                     hmpData['GENDER'] == 'M ( Was F )']
choices_gender = ['F', 'M']

hmpData['GENDER'] = np.select(conditions_gender, choices_gender, default=hmpData['GENDER'])

# Year variable
hmpData['DOS_YEAR'] = hmpData['DOS'].dt.year

# No duplicates 
hmpData[~hmpData['TARIFF_MONTHS'].isna()].duplicated(['FILE_REFERENCE','DOS'],keep=False).sum()

sum(~hmpData['TARIFF_MONTHS'].isna()) # 827
len(hmpData) # 835

# We should ensure calculated values all being non-negative integers

# Tabulate

    # Send Results to Excel.
# writer = pd.ExcelWriter('murder_tariffs.xlsx', engine='xlsxwriter')

def nmiss(x):
    return x.isna().sum()

    # Perform the aggregation for TARIFF_MONTHS, TARIFF_YEARS

for var in ['TARIFF_MONTHS', 'TARIFF_YEARS']:
    print(f"\nStatistics for {var}:")
    result = hmpData.groupby( hmpData['DOS'].dt.year)[var].agg(['count', 'min', 'median', 'mean', 'max']).rename(columns={'count': 'N'})
    result['NMISS'] = hmpData.groupby( hmpData['DOS'].dt.year)[var].apply(lambda x: x.isna().sum())
    #result.round(2).to_excel(writer, sheet_name= var)
    display(result.round(2))


pd.pivot_table(
                        hmpData,
                        values = ['TARIFF_MONTHS', 'TARIFF_YEARS'],
                        index=['DOS_YEAR'],
                        #columns=['TARIFF_MONTHS', 'TARIFF_YEARS'],
                        #dropna=False,
                        aggfunc={'TARIFF_MONTHS': ['size','count', 'min', 'median', 'mean', 'max',nmiss], 
                                'TARIFF_YEARS': ['size','count', 'min', 'median', 'mean', 'max',nmiss]},# Counting the number of occurrences
                        fill_value=0     # Replace NaN with 0
                    ).reset_index()

with pd.ExcelWriter(output_work_book, engine='openpyxl', mode='a') as writer:  
    pd.pivot_table(
                        hmpData[hmpData['GENDER']=='F'],
                        values = ['TARIFF_MONTHS', 'TARIFF_YEARS'],
                        index=['DOS_YEAR'],
                        #columns=['TARIFF_MONTHS', 'TARIFF_YEARS'],
                        #dropna=False,
                        aggfunc={'TARIFF_MONTHS': 'mean', 
                                'TARIFF_YEARS': 'mean'},# Counting the number of occurrences
                        fill_value=0     # Replace NaN with 0
                    ).reset_index().to_excel(writer,sheet_name='Females')

with pd.ExcelWriter(output_work_book, engine='openpyxl', mode='a') as writer:  
    pd.pivot_table(
                        hmpData[hmpData['GENDER']=='M'],
                        values = ['TARIFF_MONTHS', 'TARIFF_YEARS'],
                        index=['DOS_YEAR'],
                        #columns=['TARIFF_MONTHS', 'TARIFF_YEARS'],
                        #dropna=False,
                        aggfunc={'TARIFF_MONTHS': 'mean', 
                                'TARIFF_YEARS': 'mean'},# Counting the number of occurrences
                        fill_value=0     # Replace NaN with 0
                    ).reset_index().to_excel(writer,sheet_name='Males')

# workbook closes by itself so no need use writer.close()


# ------------------------------------------ Table 5.3

# Creating the pivot table

with pd.ExcelWriter(output_work_book,engine='openpyxl', mode='a') as writer:  
    pd.pivot_table(
    recalls,
    index=['SUP_BODY', 'NPS_CRC_NAME'],
    columns=['YYQ', 'HDC'],
    dropna=False,
    aggfunc='size',
    fill_value='0'
).reset_index().to_excel(writer,sheet_name='Table 5_3')