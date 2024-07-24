import numpy as np
import pandas as pd
import duckdb

# Import Data
openPrisons = pd.read_excel("s3://alpha-omppg/Supporting Data/Open Prisons.xls",sheet_name='Open Prisons')

# openPrisons.head()
# openPrisons.info()

# Change column headers to upper case
openPrisons.columns = openPrisons.columns.str.upper()


# Change year of 9999 2261 as pandas can't go past April 2262
for column in openPrisons.columns:
    if openPrisons[column].dtype == object:
        openPrisons[column] = openPrisons[column].astype(str).str.replace('9999', f'{pd.Timestamp.max.year - 1}')
        
# Convert some datetimes

openPrisons['END'] = pd.to_datetime(openPrisons['END'])
openPrisons['TYPEEND'] = pd.to_datetime(openPrisons['TYPEEND'])

# Change all text columns to string type to avoid issues with the object type
#object_cols = openPrisons.select_dtypes(include ='object').columns
#openPrisons[object_cols] = openPrisons[object_cols].astype('string')
#openPrisons.info()

# release conditions function

def update_release_conditions(row):
    if row['RELEASE_DATE'] < pd.Timestamp('2013-01-01'):
        return np.nan  # or keep existing value if preferred
    if pd.isna(row['CESTAB']) or row['CESTAB'] == '':
        return 'Unknown'
    elif pd.isna(row['LOCATION']) or row['LOCATION'] == '':
        return 'Closed'
    elif row['LOCATION'] == 'All':
        return 'Open'
    else:
        return 'Mixed'

#---------------------------------- Matching function

def openRelease(df):
    
    data = df.copy()
    
    # the double quotes on END is necessary as END is a sql keyword
    query = """SELECT DISTINCT a.*, 
                   b.LOCATION
            FROM data AS a LEFT JOIN (SELECT DISTINCT PRISONCODE, LOCATION, START, "END" FROM openPrisons) AS b 
            ON  ( a.CESTCODE = b.PRISONCODE AND
                  a.RELEASE_DATE >= b.START AND
                  a.RELEASE_DATE <= b."END"
                )"""
    result = duckdb.sql(query).df()
    
    # Apply conditions with loc for rows where RELEASE_DATE is on or after '01Jan2013'
    
    result['RELEASE_CONDITIONS'] = result.apply(update_release_conditions, axis=1)
    result = result.drop('LOCATION',axis =1)
    return result