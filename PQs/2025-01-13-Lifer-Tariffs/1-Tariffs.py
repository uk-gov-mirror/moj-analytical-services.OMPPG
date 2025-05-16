""" 
To ask His Majesty’s Government what was the (1) mean, and (2) median, tariff length for prisoners receiving a life sentence aged 
(a) under 18, (b) 18 to 20, (c) 21 to 24, (d) 25 to 29, (e) 30 to 34 (f) 35 to 39, (g) 40 to 49, (h) 50 to 59, (i) 60 to 69, and (j) 70 and over, 
at the time of sentencing, in each year from 2002. 

Answered by Eric Nyame, 13/01/2025
Steps:
1. Get lifer tariff data. Exclude whole lifers and IPP.
2. Determine age at sentence.
3. Band the ages according to the cuts given
4. Calculate tariff lengths in days, months and years
5. Calculate average (mean and median) tariff lengths in days, months and years per age band.

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

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro-Library')
# from my_log import my_log
import Out_of_bounds_dates
import prepareMatch
#importlib.reload(prepareMatch)
import openMatch
# importlib.reload(openMatch)
import TimeDiffs
importlib.reload(TimeDiffs)
import tariff_groups


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
        df[col] = df[col].apply(lambda x: x.strip() if (isinstance(x, str) and not x.isspace()) else x) #
        
#----------------------------------SOme global variables are from 4 Releases_to_Recall program

month = str(9).zfill(2) # pads the number with a leading zero
day = 30
year = 2024
quarter = 3

#----------------------------------Import PPUD data
ispPPUD = pd.read_excel(f's3://alpha-omppg/isp-population/PPUD/{year}Q{quarter}/PPUD_ISP_{year}Q{quarter}.xls')
wlPPUD = pd.read_excel(f's3://alpha-omppg/isp-population/PPUD/{year}Q{quarter}/PPUD_WholeLife_{year}Q{quarter}.xls')

ispPPUD = ispPPUD.drop_duplicates()
wlPPUD = wlPPUD.drop_duplicates()

ispPPUD.info()
wlPPUD.info()

#----------------------------------Datetime columns appearing as object type - change
ispPPUD.select_dtypes(include=['object']).dtypes # find datetime column showing as an object column

strip_blanks(ispPPUD)
strip_blanks(wlPPUD)

ispPPUD.info()
wlPPUD.info()

ispPPUD.select_dtypes(include=['datetime64']).dtypes
ispPPUD.dtypes.value_counts()
wlPPUD.info()
#---------------------------------- Add whole life flag to PPUD ISP data

# duckdb.default_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

query2 = """SELECT a.*, 
                  b.WHOLE_LIFE 
                  
            FROM ispPPUD AS a 
            LEFT JOIN (SELECT DISTINCT PRISON_NUMBER, WHOLE_LIFE, DOS FROM wlPPUD) AS b
            
            ON  a.PRISON_NUMBER = b.PRISON_NUMBER AND
            a.DOS = b.DOS"""

ispPPUD_Matched = duckdb.sql(query2).df()
ispPPUD_Matched.shape #25147

ispPPUD_Matched['WHOLE_LIFE'].value_counts(dropna=False)

exclude = (ispPPUD_Matched['CUSTODY_TYPE_DESCRIPTION'].isin(['IPP','DPP','Restricted Patient (WLOT)','Unrestricted Patient'])) | (ispPPUD_Matched['WHOLE_LIFE'] == True)

ispPPUD_Matched = ispPPUD_Matched[~exclude]
ispPPUD_Matched['CUSTODY_TYPE_DESCRIPTION'].value_counts(dropna=False)

    # Tariff length in years and months

ispPPUD_Matched['TARIFF_EXPIRY_DATE'] = ispPPUD_Matched['TARIFF_EXPIRY_DATE'].dt.normalize()
ispPPUD_Matched['DOS'] = ispPPUD_Matched['DOS'].dt.normalize()
ispPPUD_Matched.head()

ispPPUD_Matched.dtypes

tmth = ispPPUD_Matched['TARIFF_EXPIRY_DATE'] >= ispPPUD_Matched['DOS']
tmth2 = ispPPUD_Matched['TARIFF_EXPIRY_DATE'].dt.year == 1900

ispPPUD_Matched['TARIFF_DAYS'] = ispPPUD_Matched['TARIFF_EXPIRY_DATE'] - ispPPUD_Matched['DOS']
ispPPUD_Matched.loc[tmth2,'TARIFF_DAYS'] = np.nan

ispPPUD_Matched['TARIFF_MONTHS'] = np.where(tmth,
                                        ispPPUD_Matched.apply(lambda x: TimeDiffs.month_diff(x['DOS'],x['TARIFF_EXPIRY_DATE']),axis=1),
                                        np.nan)
                        
ispPPUD_Matched.loc[tmth2,'TARIFF_MONTHS'] = np.nan

ispPPUD_Matched['TARIFF_YEARS'] = ispPPUD_Matched['TARIFF_MONTHS'] // 12

  # Year of sentence
ispPPUD_Matched['SENTENCE_YEAR'] = ispPPUD_Matched['DOS'].dt.year

    # Age at time of sentence

ispPPUD_Matched['SENTENCED_AGE'] = np.where(ispPPUD_Matched['DOS'] > ispPPUD_Matched['DOB'],
                                         ispPPUD_Matched.apply(lambda x: TimeDiffs.year_diff(x['DOB'],x['DOS']),axis=1),
                                        np.nan)

(a) under 18, (b) 18 to 20, (c) 21 to 24, (d) 25 to 29, (e) 30 to 34 (f) 35 to 39, (g) 40 to 49, (h) 50 to 59, (i) 60 to 69, and (j) 70 and over, 

cuts = pd.IntervalIndex.from_tuples([(0, 18), (18, 21),
                                     (21,25),(25,30),
                                     (30,35),(35,40),
                                     (40,50),(50,60),
                                     (60,70),(70,np.inf)],closed='left')
cuts

labels = ['under 18', '18 to 20', '21 to 24', '25 to 29', '30 to 34','35 to 39', '40 to 49', '50 to 59',
          '60 to 69', '70 and over'] 
map_dict = {cuts[i]:labels[i] for i in range(10)}

ispPPUD_Matched['AGE_BANDS'] = pd.cut(ispPPUD_Matched['SENTENCED_AGE'],cuts)
ispPPUD_Matched['AGE_BANDS_2'] = ispPPUD_Matched['AGE_BANDS'].map(map_dict)

ispPPUD_Matched=ispPPUD_Matched.sort_values('SENTENCED_AGE')
ispPPUD_Matched.pivot_table(index=['AGE_BANDS','AGE_BANDS_2'],aggfunc='size', observed=True)


ispPPUD_Matched[ispPPUD_Matched['SENTENCE_YEAR']>= 2002].pivot_table(index='AGE_BANDS_2',columns='SENTENCE_YEAR',aggfunc='size')

for var in ['TARIFF_DAYS', 'TARIFF_MONTHS', 'TARIFF_YEARS']:

in_scope = ispPPUD_Matched['SENTENCE_YEAR']>= 2002

show( np.round(ispPPUD_Matched[in_scope].pivot_table(index='AGE_BANDS_2',
                                      columns='SENTENCE_YEAR',
                                      values='TARIFF_YEARS',
                                      observed=True,
                                      aggfunc='mean')), buttons=["excelHtml5"])

show( np.round(ispPPUD_Matched[in_scope].pivot_table(index='AGE_BANDS_2',
                                      columns='SENTENCE_YEAR',
                                      values='TARIFF_YEARS',
                                      observed=True,
                                      aggfunc='median')), buttons=["excelHtml5"])

show( np.round(ispPPUD_Matched[in_scope].pivot_table(index='AGE_BANDS_2',
                                      columns='SENTENCE_YEAR',
                                      values='TARIFF_YEARS',
                                      observed=True,
                                      aggfunc='size')), buttons=["excelHtml5"])

