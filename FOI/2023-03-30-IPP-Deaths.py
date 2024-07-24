# Libraries
import pandas as pd
import numpy as np
# import sys # for adding folders to the search path

import duckdb
import s3fs

pd.options.display.max_columns = None
pd.options.display.max_rows = None
# pd.options.display.precision = 2
# pd.set_option('max_colwidth',None)

# Root directory for Recalls data
rootDir = "s3://alpha-omppg/Recalls"

# Period variables
Quarter = 3 # 1:Jan-Mar, 2:Apr-Jun, 3:Jul-Sep, 4:Oct-Dec
Year = 2022 # Enter the year being run in 4 digit format

# Add macro folder to namespace to import custom modules and their functions
sys.path.append('/home/jovyan/OMPPG/Macro Library')
sys.path.append('/home/jovyan/OMPPG/Recalls/Reference Data/Recalls Lookup') # for recall lookups
#sys.path.append('/home/jovyan/.local/bin')


IPP_Deaths = pd.read_excel("s3://alpha-omppg/FOI/2023 03 30 IPP Deaths, Offence/IPP deaths.xlsx")
Pop_Data = pd.read_excel("s3://alpha-omppg/ISP Population/PPUD/2022Q4/PPUD_ISP_2022Q4.xls")
# IPP_Deaths["Date of Death"] = pd.to_datetime(IPP_Deaths["Date of Death"],errors='coerce')
IPP_Deaths.head()
IPP_Deaths.dtypes

Pop_Data.head()
Pop_Data.dtypes

