
import numpy as np
import pandas as pd

# A function to try to convert each date value and check if that is a success

def check_bounds(date_str):
    try:
        # Attempt to convert to datetime
        pd.to_datetime(date_str,dayfirst = True)
        return True  # Within bounds
    except ValueError:
        return False  # Out of bounds

# Function to show offendin rows

def date_out_of_bounds(df,dateColObj):
    """ 
    This function checks dates that are out of bounds
    and make conversion of column/variable to datetime
    impossible
    
    Author: Eric Nyame
    """
    # apply check bounds function to each row of the offending column
    
    # df['in_bounds'] = df[dateColObj].apply(check_bounds)
    # out_of_bounds_dates = df[~df['in_bounds']]
    
    outOfBoundsMask = df[dateColObj].astype(str).apply(check_bounds)
    out_of_bounds_dates = df[~outOfBoundsMask]
    
    # reset dataframe
    # df = df.drop(columns =['in_bounds'])
    
    return out_of_bounds_dates[[dateColObj] + [x for x in df.columns if x != dateColObj]]
