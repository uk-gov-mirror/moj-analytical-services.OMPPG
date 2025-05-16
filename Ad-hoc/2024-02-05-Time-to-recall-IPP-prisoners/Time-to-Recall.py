""" 
GOAL: DETERMINE THE TIME IT TOOK TO RECALL IPP OFFENDERS CURRENTLY IN PRISON
ON RECALL
By Eric Nyame, 05/02/2024
"""

# Import Packages

import pandas as pd
import numpy as np
import re
import sys # for adding folders to the search path
import duckdb
from dateutil.relativedelta import relativedelta
import XlsxWriter

# import my predefined functions, akin to macros in SAS

sys.path.append('/home/jovyan/OMPPG/Macro Library')
from prepareMatch import prepareMatch

# Set display options

pd.options.display.max_columns = None
pd.options.display.max_rows = None

# Ensures no wrapping of cell contents - run it separately

%%html
<style>
.dataframe td {
    white-space: nowrap;
}
</style>

recalledIPPs = pd.read_sas("s3://alpha-omppg/ISP Population/Final Datasets/isp_pop_2024q1.sas7bdat",encoding = 'latin1')
recalledIPPs.columns = recalledIPPs.columns.str.upper()
recalledIPPs = recalledIPPs[recalledIPPs['ISP_STATUS'] == 'Recalled IPP']
recalledIPPs.shape
recalledIPPs._is_view
recalledIPPs.head()

# Get columns relating to offence data
# [x for x in recalledIPPs.columns if re.search('Offence',x, re.IGNORECASE)]
# pd.DataFrame(recalledIPPs['OFFENCE'].unique()).to_excel("Offence.xlsx",index = False)
# pd.DataFrame(recalledIPPs['DETAILED_OFFENCE_GROUP'].unique()).to_excel("Detailed_Offence.xlsx",index=False)

# Identify recalled IPPs in PPUD recall data for ISPS
ispPPUDRecalls = pd.read_excel("s3://alpha-omppg/Data Central/PPUD Recalls/ISP Recalls 2024 02 05.xls")

prepareMatch(ispPPUDRecalls)

# Identified recall data for those on recall in custody
query =  """SELECT a.*, 
                   b.NOMIS_ID,
                   b.EXTRACTDATE
                   
            FROM ispPPUDRecalls AS a LEFT JOIN recalledIPPs AS b 
            ON  (
            b.NOMIS_ID = a.NOMS_ID OR
            b.NOMIS_ID = a.NOMS_TRIM OR
            b.NOMIS_ID = a.NOMS_START OR
            b.NOMIS_ID = a.NOMS_END OR
            b.NOMIS_ID = a.PRISON_NUMBER OR
            b.NOMIS_ID = a.PN_TRIM OR
            b.NOMIS_ID = a.PN_START OR
            b.NOMIS_ID = a.PN_END)
        """

matched1 = duckdb.sql(query).df()
matched1 = matched1[matched1['NOMIS_ID'].notnull()]
matched1.shape #3376
matched1.head()
matched1 = matched1.drop_duplicates()
len(matched1)

# Normalise recall times

matched1['LICENCE_REVOKE_DATE'] =matched1['LICENCE_REVOKE_DATE'].dt.normalize()
matched1['RELEASE_BEFORE_RECALL'] =matched1['RELEASE_BEFORE_RECALL'].dt.normalize()

# Deduplicate recalls
matched1[matched1.duplicated(subset=['FILE_REFERENCE','LICENCE_REVOKE_DATE'], keep=False)]

matched1['numb1'] = matched1.apply(lambda x: x.str.contains("Not Applicable",case=False,na=False).sum(), axis=1)
matched1['numb2'] = matched1.apply(lambda x: x.str.contains("Not specified",case=False,na=False).sum(), axis=1)
matched1['numb3'] = matched1.apply(lambda x: pd.isna(x).sum(), axis=1)
matched1['numb'] = matched1['numb1'] + matched1['numb2'] + matched1['numb3']

matched1.sort_values(['FILE_REFERENCE','numb'], inplace=True)
matched1[matched1.duplicated(subset=['FILE_REFERENCE','LICENCE_REVOKE_DATE'], keep=False)]

    # keeps only the first entries with fewer missing data
matched1 = matched1.drop_duplicates(subset=['FILE_REFERENCE','LICENCE_REVOKE_DATE'], keep = 'first')  
matched1 = matched1.drop(columns=(['numb1','numb2','numb3','numb','PN_TRIM','PN_LENGTH','PN_START',
                                   'PN_END','NOMS_TRIM','NOMS_LENGTH','NOMS_START','NOMS_END']))
matched1.head()
len(matched1)
len(matched1['FILE_REFERENCE'].unique()) # 1612
len(recalledIPPs) # 1625

# Check some non-matches - 13 unmatched cases, checks show quashed cases
recalledIPPs[~recalledIPPs['NOMIS_ID'].isin(matched1['NOMIS_ID'])]

columnOrder =['FILE_REFERENCE','FAMILY_NAME','DOS', 'RELEASE_BEFORE_RECALL','LICENCE_REVOKE_DATE','CUSTODY_TYPE_DESCRIPTION']
matched1 = matched1[columnOrder + [x for x in matched1.columns if x not in columnOrder]]
matched1.sort_values(by = ['FILE_REFERENCE','LICENCE_REVOKE_DATE'], inplace = True)
matched1.head(20)


# Check impossible date of sentence
matched1[matched1['DOS'].dt.year < 2005] # 1 case
matched1 = matched1[~(matched1['DOS'].dt.year < 2005)] # delet it

# delete recalls prior to sentence
matched1 = matched1[~(matched1['LICENCE_REVOKE_DATE'] <= matched1['DOS'])]
matched1 = matched1[~(matched1['LICENCE_REVOKE_DATE'] < matched1['RELEASE_BEFORE_RECALL'])]

# Time from release from recall
def years_diff(row,fromvar,tovar):
    if pd.isnull(row[fromvar]) or pd.isnull(row[tovar]):
        return pd.NA # returns values to be assigned to tariff_months and tariff_years
    elif row[fromvar] > row[tovar]:
        return pd.NA  # Handle cases where DOS is on or after TARIFF_EXPIRY_DATE
    else:
        return relativedelta(row[tovar], row[fromvar]).years

    # Apply the function to the DataFrame to create tariff_months and tariff_years
matched1['YEARS_TO_RECALL'] = matched1.apply(lambda row: years_diff(row,'RELEASE_BEFORE_RECALL','LICENCE_REVOKE_DATE'), 
                                                                axis=1, 
                                                                result_type='expand'
                                                              )

# Corrections
matched1[matched1['RELEASE_BEFORE_RECALL'] <= matched1['DOS']]
matched1 = matched1[matched1['RELEASE_BEFORE_RECALL'] > matched1['DOS']]
matched1 = matched1[matched1['RELEASE_BEFORE_RECALL'] <= matched1['LICENCE_REVOKE_DATE']] 

matched1['YEARS_TO_RECALL'].value_counts(dropna=False)
matched1[matched1['YEARS_TO_RECALL'].isna()]

matched1.head(20)
len(matched1)
len(matched1['FILE_REFERENCE'].unique()) #1611
len(recalledIPPs)

matched1['FIRST_RECALL'] = np.where(~(matched1['NOMIS_ID'].duplicated()), 'Y', 'N')

columnOrder =['FILE_REFERENCE','FAMILY_NAME','DOS', 'RELEASE_BEFORE_RECALL','LICENCE_REVOKE_DATE','YEARS_TO_RECALL','FIRST_RECALL','CUSTODY_TYPE_DESCRIPTION']
matched1 = matched1[columnOrder + [x for x in matched1.columns if x not in columnOrder]]

matched1.head(20)

# Save
matched1.to_excel("Recalled_IPP.xlsx", index = None)
# Matched_nodup.to_excel(""s3://alpha-omppg/Data Central/SFO/Matched_SFO.xlsx")

# Tabulate
matched1[matched1['FIRST_RECALL']=='Y']['YEARS_TO_RECALL'].value_counts(dropna=False)

matched1[ (matched1['FIRST_RECALL'] =='N') & 
          (matched1['YEARS_TO_RECALL'] >= 2)]['FILE_REFERENCE'].unique().size #226

matched1[matched1['YEARS_TO_RECALL'] > 13]