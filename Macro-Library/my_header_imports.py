import pandas as pd
import numpy as np
import duckdb
import s3fs

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.options.display.precision = 2
# pd.set_option('max_colwidth',None)

rootDir = "s3://alpha-omppg"