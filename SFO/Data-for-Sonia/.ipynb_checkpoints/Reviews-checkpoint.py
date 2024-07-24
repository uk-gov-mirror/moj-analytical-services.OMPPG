# Libraries
import pandas as pd
import numpy as np
import duckdb
import s3fs

pd.options.display.max_columns = None
pd.options.display.max_rows = None
# pd.options.display.precision = 2
# pd.set_option('max_colwidth',None)

# Root directory for Recalls data
# rootDir = "s3://alpha-omppg/FOI"

# Add macro folder to namespace to import custom modules and their functions
# sys.path.append('/home/jovyan/OMPPG/Macro Library')
# sys.path.append('/home/jovyan/OMPPG/Recalls/Reference Data/Recalls Lookup') # for recall lookups
#sys.path.append('/home/jovyan/.local/bin')

# Import Reviews
Reviews = pd.read_excel("s3://alpha-omppg/SFO/Data for Sonia/Reviews/05 2023.xls")
Reviews.head()
Reviews.dtypes
len(Reviews)

Reviews.drop_duplicates("SFO_ID", inplace = True) 
len(Reviews) 

                                  
Reviews = Reviews[Reviews["NOMS_REGION_DESCRIPTION"] != 'Not Specified']

# Tabulate

Reviews[Reviews["NOMS_REGION_DESCRIPTION"] != "CRC"].\
    pivot_table(index = "NOMS_REGION_DESCRIPTION", 
                values = 'SFO_ID',
                fill_value = 0,
                aggfunc ='count',
               margins = True)


