import numpy as np
import pandas as pd

def my_log(data):
    """ 
    This function is view basic useful information about about
    created datasets
    Author: Eric Nyame
    """
    
    display(
            data.info(),
            data.dtypes.to_frame().T, # transposed view of datatypes of columns
            data.head(3)
    )