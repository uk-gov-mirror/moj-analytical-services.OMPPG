# Convert dates- similar to date convert
# Author: Eric Nyame, 06/03/2023

import pandas as pd

def dateConvert(df,date_var):
    ''' Returns date string as a date only'''
    df[date_var] = pd.to_datetime(df[date_var],dayfirst=True, errors = 'coerce').dt.normalize()
    return df

def dateTimeConvert(df,date_var):
    ''' Returns date string as a datetime'''
    df[date_var] = pd.to_datetime(df[date_var],dayfirst=True, errors = 'coerce')
    return df