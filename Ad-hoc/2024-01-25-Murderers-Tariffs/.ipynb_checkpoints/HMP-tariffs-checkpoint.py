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

sys.path.append('/home/jovyan/OMPPG/Macro Library')
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

ispPPUD = pd.read_excel("s3://alpha-omppg/isp-population/PPUD/2024Q1/PPUD_ISP_2024Q1.xls")
wlPPUD = pd.read_excel("s3://alpha-omppg/isp-population/PPUD/2024Q1/PPUD_WholeLife_2024Q1.xls")

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

# Check how murder is entered as an offence

murder_mask = ispPPUD_MATCHED['INDEX_OFFENCE_DESCRIPTION'].str.contains('Murder', na = False, case = False)

ispPPUD_MATCHED[murder_mask]['INDEX_OFFENCE_DESCRIPTION'].value_counts(dropna=False).sort_index().to_frame()

# Murder cases from 2000 onwards, no whole life orders

murder_mask_final = ( (ispPPUD_MATCHED['INDEX_OFFENCE_DESCRIPTION'] == 'Murder') & 
                      (ispPPUD_MATCHED['DOS'].dt.year >= 2000) & 
                      (ispPPUD_MATCHED['WHOLE_LIFE'] != True)
                    )

murderers = ispPPUD_MATCHED[murder_mask_final].copy()

# Tariff length in years and months

tmth = murderers['TARIFF_EXPIRY_DATE'] >= murderers['DOS']
tmth2 = (murderers['TARIFF_EXPIRY_DATE'].dt.year == 1900) | (murderers['TARIFF_EXPIRY_DATE'].dt.year == pd.Timestamp.max.year)

murderers['TARIFF_MONTHS'] = np.where(tmth,
                                        murderers.apply(lambda x: TimeDiffs.month_diff(x['DOS'],x['TARIFF_EXPIRY_DATE']),axis=1),
                                        np.nan)
                        
murderers.loc[tmth2,'TARIFF_MONTHS'] = np.nan

murderers['TARIFF_YEARS'] = murderers['TARIFF_MONTHS'] // 12

# Take a look
retain = ['PRISON_NUMBER','FAMILY_NAME','DOS', 'TARIFF_EXPIRY_DATE','TARIFF_MONTHS', 'TARIFF_YEARS','INDEX_OFFENCE_DESCRIPTION']
murderers [retain + [col for col in murderers .columns if col not in retain]].head(20)

# Gender
murderers['GENDER'].value_counts(dropna=False)

conditions_gender = [murderers['GENDER'] == 'F ( Was M )',
                     murderers['GENDER'] == 'M ( Was F )']
choices_gender = ['F', 'M']

murderers['GENDER'] = np.select(conditions_gender, choices_gender, default=murderers['GENDER'])

# Year variable
murderers['DOS_YEAR'] = murderers['DOS'].dt.year

# No duplicates
murderers_final = 
murderers[~murderers['TARIFF_MONTHS'].isna()].duplicated(['FILE_REFERENCE','DOS'],keep=False).sum()

len(murderers) # 8369

# We should ensure calculated values all being non-negative integers

for col in tariff_columns:
    print([murderers [col].isna().sum(),(murderers [col] < 0).sum(), col])

# Tabulate

    # Send Results to Excel.
writer = pd.ExcelWriter('murder_tariffs.xlsx', engine='xlsxwriter')

def nmiss(x):
    return x.isna().sum()

    # Perform the aggregation for TARIFF_MONTHS, TARIFF_YEARS

for var in ['TARIFF_MONTHS', 'TARIFF_YEARS']:
    print(f"\nStatistics for {var}:")
    result = murderers.groupby( murderers['DOS'].dt.year)[var].agg(['count', 'min', 'median', 'mean', 'max']).rename(columns={'count': 'N'})
    result['NMISS'] = murderers.groupby( murderers ['DOS'].dt.year)[var].apply(lambda x: x.isna().sum())
    #result.round(2).to_excel(writer, sheet_name= var)
    display(result.round(2))

    # Save and close excel file
writer.save()

# specify output table

output_work_book = 'murder_tariffs_update.xlsx'

# --------------------All 

with pd.ExcelWriter(output_work_book) as writer:  
    pd.pivot_table(
                        murderers,
                        values = ['TARIFF_MONTHS', 'TARIFF_YEARS'],
                        index=['DOS_YEAR'],
                        #columns=['TARIFF_MONTHS', 'TARIFF_YEARS'],
                        #dropna=False,
                        aggfunc={'TARIFF_MONTHS': ['size','count', 'min', 'median', 'mean', 'max',nmiss], 
                                'TARIFF_YEARS': ['size','count', 'min', 'median', 'mean', 'max',nmiss]},# Counting the number of occurrences
                        fill_value=0     # Replace NaN with 0
                    ).reset_index().to_excel(writer,sheet_name='All')

with pd.ExcelWriter(output_work_book, engine='openpyxl', mode='a') as writer:  
    pd.pivot_table(
                        murderers[murderers['GENDER']=='F'],
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
                        murderers[murderers['GENDER']=='M'],
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